# ruff: noqa: E501 D102

import io
import unittest

from server.utils.validations import ValidationError

from . import committees as c

RAW_CSV_DATA = """\
C00000059|HALLMARK CARDS PAC|SARAH MOE|2501 MCGEE|MD #500|KANSAS CITY|MO|64108|U|Q|UNK|M|C||
C00000422|AMERICAN MEDICAL ASSOCIATION POLITICAL ACTION COMMITTEE|WALKER, KEVIN MR.|25 MASSACHUSETTS AVE, NW|SUITE 600|WASHINGTON|DC|200017400|B|Q||M||DELAWARE MEDICAL PAC|
C00000489|D R I V E POLITICAL FUND CHAPTER 886|JERRY SIMS JR|3528 W RENO||OKLAHOMA CITY|OK|73107|U|N||Q|L||
C00000547|KANSAS MEDICAL SOCIETY POLITICAL ACTION COMMITTEE|JERRY SLAUGHTER|623 SW 10TH AVE||TOPEKA|KS|666121627|U|Q|UNK|Q|M|KANSAS MEDICAL SOCIETY|
C00000638|INDIANA STATE MEDICAL ASSOCIATION POLITICAL ACTION COMMITTEE|ACHENBACH, GRANT MR.|322 CANAL WALK, CANAL LEVEL||INDIANAPOLIS|IN|46202|U|Q||T|M||
C00000729|AMERICAN DENTAL ASSOCIATION POLITICAL ACTION COMMITTEE|BARNES, BRAD W DR.|1111 14TH STREET, NW|SUITE 1100|WASHINGTON|DC|200055627|B|Q|UNK|M|M|INDIANA DENTAL PAC|
C00000885|INTERNATIONAL UNION OF PAINTERS AND ALLIED TRADES POLITICAL ACTION TOGETHER POLITICAL COMMITTEE|GALIS, GEORGE|7234 PARKWAY DRIVE||HANOVER|MD|21076|B|Q|UNK|M|L|INTERNATIONAL UNION OF PAINTERS AND ALLIED TRADES|
C00000901|BUILD POLITICAL ACTION COMMITTEE OF THE NATIONAL ASSOCIATION OF HOME BUILDERS (BUILDPAC)|RAMAGE, EILEEN|1201 15TH STREET, NW||WASHINGTON|DC|20005|B|Q|UNK|M|T|NATIONAL ASSOCIATION OF HOME BUILDERS|
C00000935|DCCC|GUINN, LUCINDA|430 SOUTH CAPITOL STREET, SE|2ND FLOOR|WASHINGTON|DC|200034024|U|Y|DEM|M|||
C00000984|UNITED STATES TELECOM ASSOCIATION POLITICAL ACTION COMMITTEE (TELECOMPAC)|HEINER, BRANDON|601 NEW JERSEY AVE NW|STE 600|WASHINGTON|DC|20001|B|Q|UNK|M|T|UNITED STATES TELECOM ASSOCIATION|
"""


class CommitteeTypeCodeTestCase(unittest.TestCase):
    def test_name_for_code(self):
        self.assertEqual(
            c.CommitteeTypeCode.name_for_code(c.CommitteeTypeCode.COMMUNICATION_COST),
            "Communication Cost",
        )

    def test_name_for_code_none(self):
        self.assertEqual(c.CommitteeTypeCode.name_for_code("NOPE"), None)


class PartyTestCase(unittest.TestCase):
    def test_name_for_code(self):
        self.assertEqual(c.Party.name_for_code(c.Party.DEMOCRAT), "Democrat")

    def test_name_for_code_none(self):
        self.assertEqual(c.Party.name_for_code("NOPE"), None)


class CommitteeTestCase(unittest.TestCase):
    def test_from_data_id_name(self):
        """Test that we can create a committee from data."""
        data = {"id": "id", "name": "name"}
        committee = c.Committee.from_data(data)
        self.assertEqual(committee.id, "id")
        self.assertEqual(committee.name, "name")
        self.assertIsNone(committee.party)
        self.assertIsNone(committee.candidate_id)

    def test_from_data_all(self):
        """Test that we can create a committee from data."""
        data = {
            "id": "id",
            "name": "name",
            "party": "party",
            "candidate_id": "candidate_id",
        }
        committee = c.Committee.from_data(data)
        self.assertEqual(committee.id, "id")
        self.assertEqual(committee.name, "name")
        self.assertEqual(committee.party, "party")
        self.assertEqual(committee.candidate_id, "candidate_id")

    def test_from_data_invalid(self):
        """Test that we can create a committee from data."""
        data = {"id": "id", "name": "name", "party": 42, "candidate_id": None}
        with self.assertRaises(ValidationError):
            c.Committee.from_data(data)

    def test_to_data(self):
        """Test that we can create a committee from data."""
        committee = c.Committee("id", "name", "party", "candidate_id")
        data = committee.to_data()
        self.assertEqual(data["id"], "id")
        self.assertEqual(data["name"], "name")
        self.assertEqual(data["party"], "party")
        self.assertEqual(data["candidate_id"], "candidate_id")

    def test_to_data_missing(self):
        """Test that we can create a committee from data."""
        committee = c.Committee("id", "name", None, None)
        data = committee.to_data()
        self.assertEqual(data["id"], "id")
        self.assertEqual(data["name"], "name")
        self.assertFalse("party" in data)
        self.assertFalse("candidate_id" in data)

    def test_from_committee_row(self):
        """Test that we can create a committee from a row."""
        row = [
            "C00000059",
            "HALLMARK CARDS PAC",
            "SARAH MOE",
            "2501 MCGEE",
            "MD #500",
            "KANSAS CITY",
            "MO",
            "64108",
            "U",
            "Q",
            "UNK",
            "M",
            "C",
            "CRUNK",
        ]
        committee = c.Committee.from_committee_row(row)
        self.assertEqual(committee.id, "C00000059")
        self.assertEqual(committee.name, "HALLMARK CARDS PAC")
        self.assertIsNone(committee.party)
        self.assertEqual(committee.candidate_id, "CRUNK")


class CommitteeManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.example_committees = [
            c.Committee("id1", "name1", "party1", "candidate_id1"),
            c.Committee("id2", "name2", "party2", "candidate_id2"),
            c.Committee("id3", "name3", None, None),
        ]

    def test_committees(self):
        """Test that we can create a committee manager."""
        manager = c.CommitteeManager(self.example_committees)
        self.assertEqual(len(manager.committees), len(self.example_committees))

    def test_id_to_committees(self):
        """Test that we can create a committee manager."""
        manager = c.CommitteeManager(self.example_committees)
        self.assertEqual(
            manager.id_to_committee,
            {
                "id1": self.example_committees[0],
                "id2": self.example_committees[1],
                "id3": self.example_committees[2],
            },
        )

    def test_get_committee(self):
        """Test that we can create a committee manager."""
        manager = c.CommitteeManager(self.example_committees)
        self.assertEqual(manager.get_committee("id1"), self.example_committees[0])
        self.assertEqual(manager.get_committee("id2"), self.example_committees[1])
        self.assertEqual(manager.get_committee("id3"), self.example_committees[2])
        self.assertIsNone(manager.get_committee("id4"))

    def test_jsonl_io(self):
        manager = c.CommitteeManager(self.example_committees)
        writable = io.StringIO()
        manager.to_jsonl_io(writable)
        readable = io.StringIO(writable.getvalue())
        manager2 = c.CommitteeManager.from_jsonl_io(readable)
        self.assertEqual(manager.committees, manager2.committees)

    def test_csv_io(self):
        readable = io.StringIO(RAW_CSV_DATA)
        manager = c.CommitteeManager.from_csv_io(readable)
        self.assertEqual(len(manager.committees), 10)
        committee = manager.get_committee("C00000059")
        self.assertIsNotNone(committee)
        assert committee is not None
        self.assertEqual(committee.id, "C00000059")
        self.assertEqual(committee.name, "HALLMARK CARDS PAC")
        self.assertIsNone(committee.party)
        self.assertIsNone(committee.candidate_id)
        self.assertIsNone(manager.get_committee("NOPE"))
