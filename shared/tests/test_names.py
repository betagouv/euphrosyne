"""Tests for shared.names normalization helpers."""

from django.test import SimpleTestCase

from shared.names import normalize_person_name


class NormalizePersonNameTests(SimpleTestCase):
    def test_none_returns_none(self):
        self.assertIsNone(normalize_person_name(None))

    def test_empty_or_whitespace_returns_empty(self):
        self.assertEqual(normalize_person_name(""), "")
        self.assertEqual(normalize_person_name("   "), "")

    def test_lowercase_is_titlecased(self):
        self.assertEqual(normalize_person_name("john doe"), "John Doe")

    def test_uppercase_is_titlecased(self):
        self.assertEqual(normalize_person_name("JOHN DOE"), "John Doe")

    def test_mixed_case_is_trimmed_but_not_titlecased(self):
        self.assertEqual(normalize_person_name("  McDonald  "), "McDonald")
        self.assertEqual(normalize_person_name("  van Helsing  "), "van Helsing")

    def test_single_character(self):
        self.assertEqual(normalize_person_name("a"), "A")
        self.assertEqual(normalize_person_name("Z"), "Z")

    def test_multiple_separators_preserved(self):
        self.assertEqual(normalize_person_name("jean--pierre"), "Jean--Pierre")
        self.assertEqual(normalize_person_name("o''neill"), "O''Neill")

    def test_unicode_handling(self):
        self.assertEqual(normalize_person_name(" \u00e9lise  "), "\u00c9lise")
        self.assertEqual(normalize_person_name("o\u2019neill"), "O\u2019Neill")
