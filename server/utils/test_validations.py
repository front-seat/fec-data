# ruff: noqa: D102
import pathlib
import tempfile
from unittest import TestCase

from . import validations as v


class StringValidationTestCase(TestCase):
    def test_is_str_true(self):
        self.assertTrue(v.is_str("foo"))

    def test_is_str_false(self):
        self.assertFalse(v.is_str(42))

    def test_validate_str(self):
        self.assertEqual(v.validate_str("foo"), "foo")

    def test_validate_str_raises(self):
        with self.assertRaises(v.ValidationError):
            v.validate_str(42)

    def test_is_str_or_none_true(self):
        self.assertTrue(v.is_str_or_none("foo"))
        self.assertTrue(v.is_str_or_none(None))

    def test_is_str_or_none_false(self):
        self.assertFalse(v.is_str_or_none(42))

    def test_validate_str_or_none(self):
        self.assertEqual(v.validate_str_or_none("foo"), "foo")
        self.assertEqual(v.validate_str_or_none(None), None)

    def test_validate_str_or_none_raises(self):
        with self.assertRaises(v.ValidationError):
            v.validate_str_or_none(42)


class DirValidationTestCase(TestCase):
    def test_is_extant_dir_true(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            self.assertTrue(v.is_extant_dir(temp_path))

    def test_is_extant_dir_false_does_not_exist(self):
        temp_path = pathlib.Path("/tmp/does_not_exist" + str(id(self)))
        self.assertFalse(v.is_extant_dir(temp_path))

    def test_is_extant_dir_false_actually_a_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = pathlib.Path(temp_file.name)
            self.assertFalse(v.is_extant_dir(temp_path))

    def test_validate_extant_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            self.assertEqual(v.validate_extant_dir(temp_path), temp_path.resolve())

    def test_validate_extant_dir_raises_does_not_exist(self):
        with self.assertRaises(v.ValidationError):
            v.validate_extant_dir(pathlib.Path("/tmp/does_not_exist" + str(id(self))))

    def test_validate_extant_dir_raises_actually_a_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = pathlib.Path(temp_file.name)
            with self.assertRaises(v.ValidationError):
                v.validate_extant_dir(temp_path)


class FileValidationTestCase(TestCase):
    def test_is_extant_file_true(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = pathlib.Path(temp_file.name)
            self.assertTrue(v.is_extant_file(temp_path))

    def test_is_extant_file_false_does_not_exist(self):
        temp_path = pathlib.Path("/tmp/does_not_exist" + str(id(self)))
        self.assertFalse(v.is_extant_file(temp_path))

    def test_is_extant_file_false_actually_a_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            self.assertFalse(v.is_extant_file(temp_path))

    def test_validate_extant_file(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = pathlib.Path(temp_file.name)
            self.assertEqual(v.validate_extant_file(temp_path), temp_path.resolve())

    def test_validate_extant_file_raises_does_not_exist(self):
        with self.assertRaises(v.ValidationError):
            v.validate_extant_file(pathlib.Path("/tmp/does_not_exist" + str(id(self))))

    def test_validate_extant_file_raises_actually_a_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            with self.assertRaises(v.ValidationError):
                v.validate_extant_file(temp_path)