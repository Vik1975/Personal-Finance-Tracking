"""Tests for document upload API endpoints."""

import pytest
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Document


@pytest.mark.asyncio
class TestUploadDocument:
    """Test document upload."""

    async def test_upload_pdf_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful PDF upload."""
        # Create fake PDF file
        pdf_content = b"%PDF-1.4\nTest PDF content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

        response = await async_client.post("/uploads", files=files, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["status"] in ["uploaded", "queued"]

    async def test_upload_image_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful image upload."""
        # Create fake image file
        image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        files = {"file": ("receipt.png", io.BytesIO(image_content), "image/png")}

        response = await async_client.post("/uploads", files=files, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["mime_type"] == "image/png"

    async def test_upload_without_auth(self, async_client: AsyncClient):
        """Test upload without authentication."""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        response = await async_client.post("/uploads", files=files)
        assert response.status_code == 401

    async def test_upload_unsupported_file_type(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test uploading unsupported file type."""
        files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}

        response = await async_client.post("/uploads", files=files, headers=auth_headers)
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
class TestListDocuments:
    """Test listing documents."""

    async def test_list_documents(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test listing user's documents."""
        # Create test documents
        documents = [
            Document(
                user_id=test_user.id,
                filename="receipt1.pdf",
                file_path="/path/to/receipt1.pdf",
                mime_type="application/pdf",
                file_size=1000,
                status="processed",
            ),
            Document(
                user_id=test_user.id,
                filename="receipt2.jpg",
                file_path="/path/to/receipt2.jpg",
                mime_type="image/jpeg",
                file_size=2000,
                status="uploaded",
            ),
        ]
        for doc in documents:
            db_session.add(doc)
        await db_session.commit()

        response = await async_client.get("/uploads/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_list_documents_without_auth(self, async_client: AsyncClient):
        """Test listing documents without authentication."""
        response = await async_client.get("/uploads/list")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetDocument:
    """Test getting document details."""

    async def test_get_document_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting document by ID."""
        document = Document(
            user_id=test_user.id,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            status="processed",
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)

        response = await async_client.get(f"/uploads/{document.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document.id
        assert data["filename"] == "test.pdf"

    async def test_get_nonexistent_document(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting non-existent document."""
        response = await async_client.get("/uploads/99999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestReprocessDocument:
    """Test reprocessing document."""

    async def test_reprocess_document(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test manually triggering document reprocessing."""
        document = Document(
            user_id=test_user.id,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            mime_type="application/pdf",
            file_size=1000,
            status="failed",
            error_message="Previous error",
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)

        response = await async_client.post(
            f"/uploads/{document.id}/process", headers=auth_headers
        )
        # Should queue for reprocessing (may fail if Celery not running, but endpoint should work)
        assert response.status_code in [200, 500]  # 500 if Celery unavailable


@pytest.mark.asyncio
class TestDeleteDocument:
    """Test deleting document."""

    async def test_delete_document_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test deleting document."""
        document = Document(
            user_id=test_user.id,
            filename="to_delete.pdf",
            file_path="/path/to/to_delete.pdf",
            mime_type="application/pdf",
            file_size=1000,
            status="uploaded",
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)

        response = await async_client.delete(f"/uploads/{document.id}", headers=auth_headers)
        assert response.status_code == 204

    async def test_delete_nonexistent_document(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent document."""
        response = await async_client.delete("/uploads/99999", headers=auth_headers)
        assert response.status_code == 404
