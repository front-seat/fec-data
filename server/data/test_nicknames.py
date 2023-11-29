# ruff: noqa: D102
import unittest

from . import nicknames as nn


class SplitNameTestCase(unittest.TestCase):
    def test_empty_fails(self):
        with self.assertRaises(ValueError):
            nn.split_name(" ")

    def test_last_only(self):
        self.assertEqual(nn.split_name("Smith"), ("SMITH", ""))

    def test_last_first(self):
        self.assertEqual(nn.split_name("Smith, John"), ("SMITH", "JOHN"))

    def test_last_first_middle(self):
        self.assertEqual(nn.split_name("Smith, John A."), ("SMITH", "JOHN"))

    def test_last_first_middle_suffix(self):
        self.assertEqual(nn.split_name("Smith, John A. Jr."), ("SMITH", "JOHN"))

    def test_messy_spacing(self):
        self.assertEqual(nn.split_name("  Smith ,  John  "), ("SMITH", "JOHN"))
