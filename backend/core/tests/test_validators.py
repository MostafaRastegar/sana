"""Unit tests for core validators."""
from django.test import TestCase
from django.core.exceptions import ValidationError

from core.utils.validators import StrongPasswordValidator


class StrongPasswordValidatorTest(TestCase):
    def setUp(self):
        self.validator = StrongPasswordValidator()

    def test_valid_password_passes(self):
        self.validator.validate("Abc1@def")  # has upper, lower, digit, special

    def test_missing_uppercase_and_lowercase(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate("12345!@#")
        # The regex [A-z] matches any ASCII letter, but "12345!@#" has none
        self.assertIn("letter", str(ctx.exception.message))

    def test_missing_lowercase(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate("ABCD1@")
        self.assertIn("lowercase", str(ctx.exception.message).lower())

    def test_missing_number(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate("Abcdef!@")
        self.assertIn("number", str(ctx.exception.message).lower())

    def test_missing_special_character(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate("Abcdef1")
        self.assertIn("special", str(ctx.exception.message).lower())

    def test_help_text(self):
        text = self.validator.get_help_text()
        self.assertIn("number", str(text).lower())