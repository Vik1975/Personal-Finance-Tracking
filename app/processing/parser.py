"""Document parsing and data extraction."""

import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_date(text: str) -> Optional[date]:
    """Extract and parse date from text."""
    # Common date patterns
    patterns = [
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # DD/MM/YYYY or MM/DD/YYYY
        r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",  # YYYY-MM-DD
        r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})",  # DD Month YYYY
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            date_str = matches[0]
            # Try different date formats
            for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except Exception:
                    continue

    # Default to today if no date found
    return date.today()


def parse_amount(text: str) -> Optional[Decimal]:
    """Extract monetary amount from text."""
    # Pattern for amounts with currency symbol or decimal point: $123.45, €123,45
    # Prioritize amounts with currency symbols or clear decimal indicators
    currency_pattern = r"[\$€£₽]\s*(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{2}))"

    matches = re.findall(currency_pattern, text)

    if not matches:
        # Fallback: look for numbers with decimal points (likely monetary amounts)
        # Require at least a decimal point with 2 digits
        decimal_pattern = r"\b(\d{1,3}(?:[,\s]\d{3})*[.,]\d{2})\b"
        matches = re.findall(decimal_pattern, text)

    if matches:
        amounts = []
        for match in matches:
            # Normalize: remove spaces and thousand separators
            normalized = match.replace(" ", "")
            # If comma is used as thousand separator (e.g., 1,234.56), remove it
            # If comma is used as decimal separator (e.g., 123,45), replace with dot
            if "." in normalized and "," in normalized:
                # Both present - comma is thousand separator
                normalized = normalized.replace(",", "")
            elif "," in normalized:
                # Only comma - could be decimal separator
                # Check if it's followed by exactly 2 digits (decimal)
                if re.search(r",\d{2}$", normalized):
                    normalized = normalized.replace(",", ".")
                else:
                    # Thousand separator
                    normalized = normalized.replace(",", "")
            try:
                amount = Decimal(normalized)
                # Filter out unreasonably large amounts (likely receipt numbers, not prices)
                if amount < 1000000:  # Less than 1 million
                    amounts.append(amount)
            except Exception:
                continue

        if amounts:
            return max(amounts)

    return None


def parse_merchant(text: str) -> Optional[str]:
    """Extract merchant/store name from text."""
    # Look for common patterns in first few lines
    lines = text.split("\n")[:5]

    for line in lines:
        line = line.strip()
        # Skip lines with dates, amounts, or common receipt words
        if any(
            keyword in line.lower() for keyword in ["receipt", "invoice", "tax", "total", "date"]
        ):
            continue
        # Look for capitalized words or company patterns
        if line and len(line) > 3 and not re.match(r"^\d+$", line):
            return line[:255]  # Limit to 255 chars

    return None


def parse_currency(text: str) -> str:
    """Extract currency from text."""
    currency_symbols = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "₽": "RUB",
    }

    for symbol, code in currency_symbols.items():
        if symbol in text:
            return code

    # Look for currency codes
    currency_pattern = r"\b(USD|EUR|GBP|RUB)\b"
    matches = re.findall(currency_pattern, text, re.IGNORECASE)
    if matches:
        return matches[0].upper()

    return "USD"  # Default


def parse_tax(text: str, total: Optional[Decimal]) -> Optional[Decimal]:
    """Extract tax amount from text."""
    # Look for tax patterns - match "Tax: 0.82", "Tax (8%): 2.40", "VAT: 1.50"
    tax_patterns = [
        r"tax\s*(?:\([^)]*\))?\s*[:\s]+[\$€£]?\s*(\d+[.,]\d{2})",
        r"vat\s*(?:\([^)]*\))?\s*[:\s]+[\$€£]?\s*(\d+[.,]\d{2})",
        r"налог\s*(?:\([^)]*\))?\s*[:\s]+[\$€£]?\s*(\d+[.,]\d{2})",
    ]

    for pattern in tax_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                tax_str = matches[0].replace(",", ".")
                return Decimal(tax_str)
            except Exception:
                continue

    return None


def parse_line_items(text: str) -> List[Dict[str, Any]]:
    """Extract line items from receipt."""
    items = []

    # Simple pattern: item name, quantity, price
    # Example: "Milk 2x 3.50"
    pattern = r"([A-Za-z\s]+)\s+(\d+)(?:x|\*)?\s+(\d+[.,]\d{2})"
    matches = re.findall(pattern, text)

    for match in matches:
        item_name = match[0].strip()
        quantity = match[1]
        price = match[2].replace(",", ".")

        try:
            items.append(
                {
                    "name": item_name[:255],
                    "quantity": Decimal(quantity),
                    "unit_price": Decimal(price),
                    "total_price": Decimal(quantity) * Decimal(price),
                }
            )
        except Exception:
            continue

    return items


def parse_document_data(raw_text: str) -> Dict[str, Any]:
    """Parse document and extract structured data."""
    logger.info("Parsing document data...")

    # Extract key fields
    transaction_date = parse_date(raw_text)
    amount = parse_amount(raw_text)
    merchant = parse_merchant(raw_text)
    currency = parse_currency(raw_text)
    tax = parse_tax(raw_text, amount)
    line_items = parse_line_items(raw_text)

    result = {
        "date": transaction_date.isoformat() if transaction_date else None,
        "amount": float(amount) if amount else None,
        "merchant": merchant,
        "currency": currency,
        "tax": float(tax) if tax else None,
        "line_items": line_items,
    }

    logger.info(f"Parsed data: {result}")
    return result
