from datetime import date

from scripts.collect_financial_data import get_available_quarters


class TestGetAvailableQuarters:
    """Test get_available_quarters function."""

    def test_2026_feb_21(self) -> None:
        """Test 2026-02-21: 2024Q4, 2025Q1-Q3 disclosed, 2025Q4 not yet."""
        result = get_available_quarters(date(2026, 2, 21))
        assert result == [
            ("2024", "11011"),
            ("2025", "11013"),
            ("2025", "11012"),
            ("2025", "11014"),
        ]

    def test_2026_jan_01(self) -> None:
        """Test 2026-01-01: 2024Q4, 2025Q1-Q3 disclosed, 2025Q4 not yet."""
        result = get_available_quarters(date(2026, 1, 1))
        assert ("2025", "11011") not in result
        assert ("2024", "11011") in result
        assert len(result) == 4

    def test_q4_disclosure_deadline_exact(self) -> None:
        """Test 2025-03-31: 2024Q4 included on deadline day."""
        result = get_available_quarters(date(2025, 3, 31))
        assert ("2024", "11011") in result

    def test_q4_before_deadline(self) -> None:
        """Test 2025-03-30: 2024Q4 not yet disclosed."""
        result = get_available_quarters(date(2025, 3, 30))
        assert ("2024", "11011") not in result

    def test_q1_disclosure_deadline_exact(self) -> None:
        """Test 2025-05-15: 2024Q1 included on deadline day."""
        result = get_available_quarters(date(2025, 5, 15))
        assert ("2024", "11013") in result

    def test_chronological_order(self) -> None:
        """Test result is sorted chronologically (oldest first)."""
        result = get_available_quarters(date(2026, 2, 21))
        assert result[0] == ("2024", "11011")
        assert result[-1] == ("2025", "11014")

    def test_q2_disclosure_deadline_exact(self) -> None:
        """Test 2025-08-14: 2024Q2 included on deadline day."""
        result = get_available_quarters(date(2025, 8, 14))
        assert ("2024", "11012") in result

    def test_q3_disclosure_deadline_exact(self) -> None:
        """Test 2025-11-14: 2024Q3 included on deadline day."""
        result = get_available_quarters(date(2025, 11, 14))
        assert ("2024", "11014") in result

    def test_before_any_disclosure(self) -> None:
        """Test early in year: 2023Q4, 2024Q1-Q3 disclosed, 2024Q4 not yet."""
        result = get_available_quarters(date(2025, 1, 1))
        assert len(result) == 4
        assert ("2023", "11011") in result
        assert ("2024", "11013") in result
        assert ("2024", "11012") in result
        assert ("2024", "11014") in result
        assert ("2024", "11011") not in result

    def test_after_all_disclosures(self) -> None:
        """Test late in year: 2024Q1-Q4 disclosed, 2025Q1 not yet."""
        result = get_available_quarters(date(2025, 12, 31))
        assert len(result) == 4
        assert ("2024", "11013") in result
        assert ("2024", "11012") in result
        assert ("2024", "11014") in result
        assert ("2024", "11011") in result
