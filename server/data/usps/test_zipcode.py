# ruff: noqa: D102
import io
from unittest import TestCase

from . import zipcode as z

FAKE_CSV_DATA = """\
PHYSICAL ZIP,PHYSICAL CITY,PHYSICAL STATE
12345,NEW YORK,NY
12345,NEW YORK,NY
12345,BRONX,NY
98101,SEATTLE,WA
98102,SEATTLE,WA
98103,SEATTLE,WA
98104,SEATTLE,WA
98105,SEATTLE,WA
"""


class ZipCodeManagerTestCase(TestCase):
    def setUp(self):
        self.data = io.StringIO(FAKE_CSV_DATA)
        self.zip_code_manager = z.ZipCodeManager.from_csv_io(self.data)
        self.new_york = z.CityState("NEW YORK", "NY")
        self.bronx = z.CityState("BRONX", "NY")
        self.seattle = z.CityState("SEATTLE", "WA")

    def test_init(self):
        self.assertEqual(len(self.zip_code_manager.zip_codes), 8)

    def test_city_to_zip_codes(self):
        self.assertEqual(len(self.zip_code_manager.city_to_zip_codes), 3)
        self.assertEqual(len(self.zip_code_manager.city_to_zip_codes[self.new_york]), 1)
        self.assertEqual(len(self.zip_code_manager.city_to_zip_codes[self.bronx]), 1)
        self.assertEqual(len(self.zip_code_manager.city_to_zip_codes[self.seattle]), 5)

    def test_zip5_to_cities(self):
        self.assertEqual(len(self.zip_code_manager.zip5_to_cities), 6)
        self.assertEqual(
            self.zip_code_manager.zip5_to_cities["12345"],
            frozenset([self.new_york, self.bronx]),
        )
        self.assertEqual(
            self.zip_code_manager.zip5_to_cities["98101"], frozenset([self.seattle])
        )

    def test_get_zip_codes(self):
        self.assertEqual(len(self.zip_code_manager.get_zip_codes(self.new_york)), 1)
        self.assertEqual(len(self.zip_code_manager.get_zip_codes(self.bronx)), 1)
        self.assertEqual(len(self.zip_code_manager.get_zip_codes(self.seattle)), 5)
        self.assertEqual(len(self.zip_code_manager.get_zip_codes("seattle")), 5)
        self.assertEqual(len(self.zip_code_manager.get_zip_codes("nowhere")), 0)

    def test_get_city_states(self):
        self.assertEqual(
            self.zip_code_manager.get_city_states("12345"),
            frozenset([self.new_york, self.bronx]),
        )
        self.assertEqual(
            self.zip_code_manager.get_city_states("98101"), frozenset([self.seattle])
        )

    def test_get_city_state_not_found(self):
        self.assertEqual(self.zip_code_manager.get_city_states("00000"), frozenset())
        self.assertEqual(self.zip_code_manager.get_city_states("99999"), frozenset())
