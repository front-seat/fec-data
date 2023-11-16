# ruff: noqa: D102
from unittest import TestCase

from .city_state import CityState
from .metros import MajorMetros


class ForCityTestCase(TestCase):
    def test_seattle(self):
        self.assertEqual(MajorMetros.for_city("Seattle"), CityState("SEATTLE", "WA"))

    def test_case_inesensitive(self):
        self.assertEqual(MajorMetros.for_city("seattle"), CityState("SEATTLE", "WA"))
        self.assertEqual(MajorMetros.for_city("SEATTLE"), CityState("SEATTLE", "WA"))

    def test_nothing(self):
        self.assertIsNone(MajorMetros.for_city("Nothing"))
