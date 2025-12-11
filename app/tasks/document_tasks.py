"""Celery tasks for document processing."""

import json
import logging
from datetime import datetime
from decimal import Decimal

from app.tasks.celery_app import celery_app
from app.processing.ocr import extract_text_from_document
from app.processing.parser import parse_document_data

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    """
    Process a document: OCR, parse, extract data.

    Args:
        document_id: ID of the document to process
    """
    logger.info(f"Starting processing for document {document_id}")

    # Import here to avoid circular imports
    from app.db.base import async_session_maker
    from app.db.models import Document, DocumentStatus, Transaction, LineItem
    from sqlalchemy import select
    import asyncio

    async def process():
        async with async_session_maker() as db:
            # Get document
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return

            try:
                # Update status to processing
                document.status = DocumentStatus.PROCESSING
                await db.commit()

                # Step 1: OCR/Extract text
                logger.info(f"Extracting text from {document.file_path}")
                extraction_result = extract_text_from_document(
                    document.file_path,
                    document.mime_type,
                    lang="en"  # TODO: Get from settings or user preference
                )

                raw_text = extraction_result.get("raw_text", "")
                document.raw_text = raw_text

                if not raw_text:
                    raise ValueError("No text extracted from document")

                # Step 2: Parse structured data
                logger.info("Parsing document data")
                parsed_data = parse_document_data(raw_text)
                document.extracted_data = json.dumps(parsed_data)

                # Step 3: Create transaction if we have amount and date
                if parsed_data.get("amount") and parsed_data.get("date"):
                    logger.info("Creating transaction from parsed data")

                    transaction = Transaction(
                        user_id=document.user_id,
                        document_id=document.id,
                        date=datetime.fromisoformat(parsed_data["date"]).date(),
                        amount=Decimal(str(parsed_data["amount"])),
                        currency=parsed_data.get("currency", "USD"),
                        merchant=parsed_data.get("merchant"),
                        tax=Decimal(str(parsed_data["tax"])) if parsed_data.get("tax") else None,
                        is_expense=True,  # TODO: Determine from context
                    )
                    db.add(transaction)
                    await db.flush()  # Get transaction ID

                    # Step 4: Auto-categorize transaction
                    from app.processing.categorization import categorize_transaction
                    category_id = await categorize_transaction(transaction, db, document.user_id)
                    if category_id:
                        transaction.category_id = category_id

                    # Create line items if available
                    for item_data in parsed_data.get("line_items", []):
                        line_item = LineItem(
                            transaction_id=transaction.id,
                            name=item_data["name"],
                            quantity=Decimal(str(item_data["quantity"])),
                            unit_price=Decimal(str(item_data["unit_price"])),
                            total_price=Decimal(str(item_data["total_price"])),
                        )
                        db.add(line_item)

                # Mark as processed
                document.status = DocumentStatus.PROCESSED
                document.processed_at = datetime.utcnow()
                document.error_message = None

                await db.commit()
                logger.info(f"Successfully processed document {document_id}")

            except Exception as e:
                logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)[:500]  # Limit error message length
                await db.commit()

                # Retry if not max retries
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

    # Run async function
    asyncio.run(process())
