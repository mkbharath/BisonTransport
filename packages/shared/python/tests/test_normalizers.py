"""Tests for value normalizers."""

from datetime import date

import pytest

from order_shared.utils.normalizers import (
    expand_address_abbreviations,
    normalize_date,
    normalize_phone,
    normalize_weight,
)


class TestNormalizeDate:
    """Test date normalization across 15+ formats."""

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("2026-06-15", date(2026, 6, 15)),
            ("06/15/2026", date(2026, 6, 15)),
            ("06/15/26", date(2026, 6, 15)),
            ("15/06/2026", date(2026, 6, 15)),
            ("June 15, 2026", date(2026, 6, 15)),
            ("Jun 15, 2026", date(2026, 6, 15)),
            ("June 15 2026", date(2026, 6, 15)),
            ("Jun 15 2026", date(2026, 6, 15)),
            ("15 June 2026", date(2026, 6, 15)),
            ("15 Jun 2026", date(2026, 6, 15)),
            ("20260615", date(2026, 6, 15)),
            ("06-15-2026", date(2026, 6, 15)),
            ("06.15.2026", date(2026, 6, 15)),
        ],
    )
    def test_standard_formats(self, input_val: str, expected: date) -> None:
        assert normalize_date(input_val) == expected

    def test_today(self) -> None:
        result = normalize_date("today")
        assert result == date.today()

    def test_tomorrow(self) -> None:
        result = normalize_date("tomorrow")
        assert result == date.today() + __import__("datetime").timedelta(days=1)

    def test_next_monday(self) -> None:
        ref = date(2026, 6, 23)  # Tuesday
        result = normalize_date("next Monday", reference_date=ref)
        assert result == date(2026, 6, 29)  # Following Monday

    def test_next_friday(self) -> None:
        ref = date(2026, 6, 23)  # Tuesday
        result = normalize_date("next Friday", reference_date=ref)
        assert result == date(2026, 6, 26)  # Same week Friday

    def test_3_weeks_from_today(self) -> None:
        ref = date(2026, 6, 23)
        result = normalize_date("3 weeks from today", reference_date=ref)
        assert result == date(2026, 7, 14)

    def test_5_days_from_today(self) -> None:
        ref = date(2026, 6, 23)
        result = normalize_date("5 days from today", reference_date=ref)
        assert result == date(2026, 6, 28)

    def test_none_input(self) -> None:
        assert normalize_date(None) is None

    def test_empty_string(self) -> None:
        assert normalize_date("") is None

    def test_unparseable(self) -> None:
        assert normalize_date("not a date at all") is None


class TestNormalizeWeight:
    """Test weight normalization."""

    @pytest.mark.parametrize(
        "input_val,expected_value,expected_unit",
        [
            ("5000 lbs", 5000.0, "lbs"),
            ("5000 pounds", 5000.0, "lbs"),
            ("5,000 lbs", 5000.0, "lbs"),
            ("2500 kg", 2500.0, "kgs"),
            ("2500 kgs", 2500.0, "kgs"),
            ("2500 kilograms", 2500.0, "kgs"),
            ("1.5 tons", 3000.0, "lbs"),  # tons converted to lbs
            ("42000", 42000.0, "lbs"),  # bare number, default unit
            ("3,500.5 lb", 3500.5, "lbs"),
        ],
    )
    def test_weight_formats(
        self, input_val: str, expected_value: float, expected_unit: str
    ) -> None:
        value, unit = normalize_weight(input_val)
        assert value == expected_value
        assert unit == expected_unit

    def test_none_input(self) -> None:
        value, unit = normalize_weight(None)
        assert value is None
        assert unit == "lbs"

    def test_custom_default_unit(self) -> None:
        value, unit = normalize_weight("1000", default_unit="kgs")
        assert value == 1000.0
        assert unit == "kgs"


class TestNormalizePhone:
    """Test phone number normalization to E.164."""

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("+14165551234", "+14165551234"),  # Already E.164
            ("4165551234", "+14165551234"),  # 10 digits
            ("14165551234", "+14165551234"),  # 11 digits with leading 1
            ("(416) 555-1234", "+14165551234"),
            ("416-555-1234", "+14165551234"),
            ("416.555.1234", "+14165551234"),
        ],
    )
    def test_phone_formats(self, input_val: str, expected: str) -> None:
        assert normalize_phone(input_val) == expected

    def test_none_input(self) -> None:
        assert normalize_phone(None) is None

    def test_international_passthrough(self) -> None:
        assert normalize_phone("+442071234567") == "+442071234567"


class TestExpandAddressAbbreviations:
    """Test address abbreviation expansion."""

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("123 Main St", "123 Main Street"),
            ("456 Oak Ave", "456 Oak Avenue"),
            ("789 Elm Blvd", "789 Elm Boulevard"),
            ("100 Pine Dr", "100 Pine Drive"),
            ("200 Maple Rd", "200 Maple Road"),
            ("300 Cedar Ln", "300 Cedar Lane"),
        ],
    )
    def test_expansions(self, input_val: str, expected: str) -> None:
        assert expand_address_abbreviations(input_val) == expected

    def test_no_abbreviation(self) -> None:
        assert expand_address_abbreviations("123 Main Street") == "123 Main Street"

    def test_st_james_not_expanded(self) -> None:
        # 'St' in the middle of the address is NOT a street type suffix
        result = expand_address_abbreviations("123 St James Ave")
        assert result == "123 St James Avenue"

    def test_none_input(self) -> None:
        assert expand_address_abbreviations(None) is None
