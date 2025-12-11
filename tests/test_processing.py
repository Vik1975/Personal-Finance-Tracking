"""Tests for document processing modules (OCR and parsing)."""

import pytest
from decimal import Decimal
from datetime import date

from app.processing.parser import (
    parse_date,
    parse_amount,
    parse_merchant,
    parse_currency,
    parse_tax,
    parse_document_data,
)


class TestDateParsing:
    """Test date extraction from text."""

    def test_parse_date_slash_format(self):
        """Test parsing dates in DD/MM/YYYY format."""
        text = "Date: 25/12/2025"
        result = parse_date(text)
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 25

    def test_parse_date_dash_format(self):
        """Test parsing dates in YYYY-MM-DD format."""
        text = "Transaction date: 2025-12-25"
        result = parse_date(text)
        assert result == date(2025, 12, 25)

    def test_parse_date_written_format(self):
        """Test parsing dates in written format."""
        text = "Date: 25 December 2025"
        result = parse_date(text)
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 25

    def test_parse_date_no_date_found(self):
        """Test parsing when no date is found (returns today)."""
        text = "No date here just random text"
        result = parse_date(text)
        assert result == date.today()


class TestAmountParsing:
    """Test amount extraction from text."""

    def test_parse_amount_with_dollar_sign(self):
        """Test parsing amount with $ symbol."""
        text = "Total: $123.45"
        result = parse_amount(text)
        assert result == Decimal("123.45")

    def test_parse_amount_without_symbol(self):
        """Test parsing amount without currency symbol."""
        text = "Amount: 99.99"
        result = parse_amount(text)
        assert result == Decimal("99.99")

    def test_parse_amount_with_euro_sign(self):
        """Test parsing amount with € symbol."""
        text = "Total: €50.75"
        result = parse_amount(text)
        assert result == Decimal("50.75")

    def test_parse_amount_largest_value(self):
        """Test that parser returns largest amount (likely the total)."""
        text = """
        Item 1: $10.00
        Item 2: $15.50
        Subtotal: $25.50
        Tax: $2.04
        Total: $27.54
        """
        result = parse_amount(text)
        assert result == Decimal("27.54")

    def test_parse_amount_with_commas(self):
        """Test parsing amount with thousand separators."""
        text = "Total: $1,234.56"
        result = parse_amount(text)
        assert result == Decimal("1234.56")

    def test_parse_amount_no_amount(self):
        """Test parsing when no amount found."""
        text = "No amounts here"
        result = parse_amount(text)
        assert result is None


class TestMerchantParsing:
    """Test merchant/store name extraction."""

    def test_parse_merchant_from_header(self):
        """Test extracting merchant from document header."""
        text = """
        WALMART SUPERCENTER
        123 Main Street
        Date: 12/11/2025
        Items:
        Milk: $3.50
        """
        result = parse_merchant(text)
        assert "WALMART" in result.upper()

    def test_parse_merchant_skips_keywords(self):
        """Test that parser skips lines with common receipt keywords."""
        text = """
        RECEIPT
        FRESH FOODS MARKET
        Date: 12/11/2025
        """
        result = parse_merchant(text)
        assert "FRESH FOODS" in result

    def test_parse_merchant_no_merchant(self):
        """Test when no merchant can be determined."""
        text = "123\n456\n789"
        result = parse_merchant(text)
        # Should return None or first non-numeric line
        assert result is None or result != "123"


class TestCurrencyParsing:
    """Test currency detection."""

    def test_parse_currency_usd(self):
        """Test detecting USD from $ symbol."""
        text = "Total: $100.00"
        result = parse_currency(text)
        assert result == "USD"

    def test_parse_currency_eur(self):
        """Test detecting EUR from € symbol."""
        text = "Total: €50.00"
        result = parse_currency(text)
        assert result == "EUR"

    def test_parse_currency_gbp(self):
        """Test detecting GBP from £ symbol."""
        text = "Total: £30.00"
        result = parse_currency(text)
        assert result == "GBP"

    def test_parse_currency_code(self):
        """Test detecting currency from code."""
        text = "Total: 100.00 EUR"
        result = parse_currency(text)
        assert result == "EUR"

    def test_parse_currency_default(self):
        """Test default currency when none found."""
        text = "Total: 100"
        result = parse_currency(text)
        assert result == "USD"


class TestTaxParsing:
    """Test tax amount extraction."""

    def test_parse_tax_with_label(self):
        """Test parsing tax with 'tax' label."""
        text = """
        Subtotal: $100.00
        Tax: $8.00
        Total: $108.00
        """
        result = parse_tax(text, Decimal("108.00"))
        assert result == Decimal("8.00")

    def test_parse_tax_vat_label(self):
        """Test parsing tax with 'VAT' label."""
        text = """
        Subtotal: €100.00
        VAT: €20.00
        Total: €120.00
        """
        result = parse_tax(text, Decimal("120.00"))
        assert result == Decimal("20.00")

    def test_parse_tax_no_tax(self):
        """Test when no tax found."""
        text = "Total: $100.00"
        result = parse_tax(text, Decimal("100.00"))
        assert result is None


class TestDocumentDataParsing:
    """Test complete document parsing."""

    def test_parse_complete_receipt(self):
        """Test parsing a complete receipt."""
        text = """
        FRESH FOODS MARKET
        123 Main Street
        Date: 12/11/2025

        Items:
        Milk: $3.50
        Bread: $2.99

        Subtotal: $6.49
        Tax: $0.52
        Total: $7.01

        Thank you!
        """
        result = parse_document_data(text)

        assert result["date"] is not None
        assert result["amount"] is not None
        assert result["amount"] > 6.0  # Should get the total
        assert result["merchant"] is not None
        assert "FRESH FOODS" in result["merchant"]
        assert result["currency"] == "USD"
        assert result["tax"] is not None

    def test_parse_minimal_receipt(self):
        """Test parsing receipt with minimal info."""
        text = """
        Store Name
        Total: $25.00
        """
        result = parse_document_data(text)

        assert result["amount"] == 25.0
        assert result["merchant"] == "Store Name"
        assert result["date"] is not None  # Should default to today

    def test_parse_receipt_no_amounts(self):
        """Test parsing receipt with no amounts."""
        text = "Just some random text"
        result = parse_document_data(text)

        assert result["amount"] is None
        assert result["date"] is not None  # Defaults to today


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_amount_decimal_comma(self):
        """Test parsing European format with comma as decimal."""
        text = "Total: 123,45"
        result = parse_amount(text)
        # Should handle comma as decimal separator
        assert result == Decimal("123.45")

    def test_parse_date_ambiguous_format(self):
        """Test parsing ambiguous date format."""
        text = "Date: 01/02/2025"
        result = parse_date(text)
        # Should parse (might be Jan 2 or Feb 1 depending on locale)
        assert result.year == 2025

    def test_parse_merchant_long_name(self):
        """Test parsing very long merchant name."""
        text = "A" * 300 + "\nDate: 12/11/2025"
        result = parse_merchant(text)
        # Should truncate to 255 chars
        assert len(result) <= 255

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        result = parse_document_data("")
        assert result["amount"] is None
        assert result["merchant"] is None
        assert result["date"] is not None  # Defaults to today


class TestRealWorldScenarios:
    """Test with real-world receipt scenarios."""

    def test_parse_grocery_receipt(self):
        """Test parsing typical grocery store receipt."""
        text = """
        WALMART SUPERCENTER #1234
        123 MAIN ST, ANYTOWN, USA

        RECEIPT #: 123456789
        DATE: 11/25/2025  TIME: 14:30:15

        MILK 1%          1 @  3.49    $3.49
        BREAD WHITE      2 @  2.50    $5.00
        BANANAS          3 LB @ 0.59  $1.77

        SUBTOTAL                      $10.26
        TAX                            $0.82
        TOTAL                         $11.08

        THANK YOU FOR SHOPPING
        """
        result = parse_document_data(text)

        assert result["amount"] == 11.08
        assert "WALMART" in result["merchant"]
        assert result["tax"] == 0.82
        assert result["currency"] == "USD"
        assert result["date"] == "2025-11-25"

    def test_parse_restaurant_receipt(self):
        """Test parsing restaurant receipt."""
        text = """
        THE PIZZA PLACE
        123 Food St

        Server: John    Table: 5
        Date: 12/10/2025

        Large Pepperoni Pizza    $18.99
        Garlic Bread              $4.99
        Soda (2)                  $5.98

        Subtotal:                $29.96
        Tax (8%):                 $2.40
        ================================
        TOTAL:                   $32.36

        Tip: _______

        Thank you!
        """
        result = parse_document_data(text)

        assert result["amount"] == 32.36
        assert "PIZZA" in result["merchant"]
        assert result["tax"] == 2.40

    def test_parse_gas_station_receipt(self):
        """Test parsing gas station receipt."""
        text = """
        SHELL GAS STATION
        Pump #3
        Date: 12/11/2025

        UNLEADED 87
        Gallons: 12.5
        Price/Gal: $3.45

        FUEL TOTAL: $43.13
        """
        result = parse_document_data(text)

        assert result["amount"] == 43.13
        assert "SHELL" in result["merchant"]
