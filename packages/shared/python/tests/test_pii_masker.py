"""Tests for PII masking utility."""

import pytest

from order_shared.utils.pii_masker import mask_email, mask_phone, mask_pii


class TestMaskEmail:
    """Test email address masking."""

    def test_standard_email(self) -> None:
        assert mask_email("john.doe@example.com") == "j***@example.com"

    def test_single_char_local(self) -> None:
        assert mask_email("j@example.com") == "*@example.com"

    def test_no_at_sign(self) -> None:
        assert mask_email("not-an-email") == "not-an-email"


class TestMaskPhone:
    """Test phone number masking."""

    def test_standard_phone(self) -> None:
        assert mask_phone("+14165551234") == "***-***-1234"

    def test_short_number(self) -> None:
        assert mask_phone("123") == "***"

    def test_formatted_phone(self) -> None:
        assert mask_phone("(416) 555-1234") == "***-***-1234"


class TestMaskPii:
    """Test full PII masking on text strings."""

    def test_masks_email_in_text(self) -> None:
        text = "Contact customer at john.doe@example.com for details"
        result = mask_pii(text)
        assert "john.doe@example.com" not in result
        assert "j***@example.com" in result

    def test_masks_phone_in_text(self) -> None:
        text = "Call the customer at 416-555-1234 for pickup info"
        result = mask_pii(text)
        assert "416-555-1234" not in result
        assert "***-***-1234" in result

    def test_masks_multiple_pii(self) -> None:
        text = "Email: test@domain.com, Phone: (905) 123-4567"
        result = mask_pii(text)
        assert "test@domain.com" not in result
        assert "(905) 123-4567" not in result

    def test_no_pii_unchanged(self) -> None:
        text = "Order ORD-20260615-00001 processed successfully"
        assert mask_pii(text) == text
