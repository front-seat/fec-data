# ruff: noqa: D102
import io
import unittest
from decimal import Decimal

from server.data.names.nicknames import MockGetNicknameIndex
from server.utils.validations import ValidationError

from . import contributions as cont
from .committees import Committee, MockGetCommittee, Party


class SplitNameTestCase(unittest.TestCase):
    def test_last_only(self):
        self.assertEqual(cont.split_name("Smith"), ("Smith", None))

    def test_last_comma_first(self):
        self.assertEqual(cont.split_name("Smith, John"), ("Smith", "John"))

    def test_stripping(self):
        self.assertEqual(cont.split_name(" Smith, John "), ("Smith", "John"))


class FuzzyIdentifierTestCase(unittest.TestCase):
    def setUp(self):
        self.get_nickname_index = MockGetNicknameIndex(
            [["Dave", "David", "Davey"], ["Matt", "Matthew"]]
        )

    def test_last_first_simple(self):
        self.assertEqual(
            cont.FuzzyIdentifier.from_last_first(
                "Smith", "John", "12345", get_nickname_index=self.get_nickname_index
            ),
            "SMITH-JOHN-12345",
        )

    def test_last_no_first_simple(self):
        self.assertEqual(
            cont.FuzzyIdentifier.from_last_first(
                "Smith", None, "12345", get_nickname_index=self.get_nickname_index
            ),
            "SMITH-NONE-12345",
        )

    def test_last_first_nickname(self):
        self.assertEqual(
            cont.FuzzyIdentifier.from_last_first(
                "Smith",
                "Davey",
                "12345",
                get_nickname_index=self.get_nickname_index,
            ),
            "SMITH-0-12345",
        )


class ContributionTestCase(unittest.TestCase):
    def test_from_data_valid(self):
        contribution = cont.Contribution.from_data(
            {
                "id": "12345",
                "committee_id": "C12345",
                "name": "Smith, John",
                "city": "Seattle",
                "state": "WA",
                "zip_code": "98101",
                "amount": "10",
            }
        )
        self.assertEqual(contribution.id, "12345")
        self.assertEqual(contribution.committee_id, "C12345")
        self.assertEqual(contribution.name, "Smith, John")
        self.assertEqual(contribution.city, "Seattle")
        self.assertEqual(contribution.state, "WA")
        self.assertEqual(contribution.zip_code, "98101")
        self.assertEqual(contribution.amount, Decimal(10))

    def test_from_data_invalid(self):
        with self.assertRaises(ValidationError):
            cont.Contribution.from_data({})

    def test_to_data(self):
        contribution = cont.Contribution(
            id="12345",
            committee_id="C12345",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(10),
        )
        self.assertEqual(
            contribution.to_data(),
            {
                "id": "12345",
                "committee_id": "C12345",
                "name": "Smith, John",
                "city": "Seattle",
                "state": "WA",
                "zip_code": "98101",
                "amount": "10",
            },
        )

    def test_from_contribution_row_valid(self):
        contribution = cont.Contribution.from_contribution_row(
            [
                "C12345",
                "",
                "",
                "",
                "",
                "",
                cont.EntityTypeCode.INDIVIDUAL,
                "Smith, John",
                "Seattle",
                "WA",
                "98101",
                "",
                "",
                "",
                "10",
                "",
                "",
                "",
                "",
                "",
                "12345",
            ]
        )
        self.assertIsNotNone(contribution)
        assert contribution is not None
        self.assertEqual(contribution.id, "12345")
        self.assertEqual(contribution.committee_id, "C12345")
        self.assertEqual(contribution.name, "Smith, John")
        self.assertEqual(contribution.city, "Seattle")
        self.assertEqual(contribution.state, "WA")
        self.assertEqual(contribution.zip_code, "98101")
        self.assertEqual(contribution.amount, Decimal(10))

    def test_from_contribution_row_invalid(self):
        contribution = cont.Contribution.from_contribution_row(
            [
                "C12345",
                "",
                "",
                "",
                "",
                "",
                cont.EntityTypeCode.CANDIDATE,
                "Smith, John",
                "Seattle",
                "WA",
                "98101",
                "",
                "",
                "",
                "10",
                "",
                "",
                "",
                "",
                "",
                "12345",
            ]
        )
        self.assertIsNone(contribution)


class ContributionSummaryTestCase(unittest.TestCase):
    def setUp(self):
        self.contribution_1 = cont.Contribution(
            id="12345",
            committee_id="C12345",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(10),
        )
        self.contribution_2 = cont.Contribution(
            id="12346",
            committee_id="C67890",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(20),
        )
        self.contribution_3 = cont.Contribution(
            id="12347",
            committee_id="CABCDE",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(50),
        )
        self.get_committee = MockGetCommittee(
            [
                Committee(
                    id="C12345",
                    name="Barney for America",
                    party=Party.DEMOCRAT,
                    candidate_id="CAN12345",
                ),
                Committee(
                    id="C67890",
                    name="Donald for Duck",
                    party=Party.DEMOCRAT,
                    candidate_id="CAN67890",
                ),
                Committee(
                    id="CABCDE",
                    name="Jupiter for Pluto",
                    party=Party.GREEN,
                    candidate_id="CANABCDE",
                ),
            ]
        )

    def test_new(self):
        summary = cont.ContributionSummary.new(
            "SMITH-JOHN-98101",
            self.contribution_1,
            get_committee=self.get_committee,
        )
        self.assertEqual(summary.fuzzy_id, "SMITH-JOHN-98101")
        self.assertEqual(summary.name, "Smith, John")
        self.assertEqual(summary.zip_code, "98101")
        self.assertEqual(summary.total, Decimal(10))
        self.assertEqual(len(summary.by_party), 1)
        self.assertEqual(summary.by_party.get(Party.DEMOCRAT), Decimal(10))
        self.assertTrue("C12345" in summary.by_committee)
        self.assertEqual(len(summary.by_committee), 1)
        self.assertEqual(summary.by_committee.get("C12345"), Decimal(10))

    def test_add(self):
        summary = cont.ContributionSummary.new(
            "SMITH-JOHN-98101",
            self.contribution_1,
            get_committee=self.get_committee,
        )
        summary.add(self.contribution_2, get_committee=self.get_committee)
        summary.add(self.contribution_3, get_committee=self.get_committee)
        self.assertEqual(summary.fuzzy_id, "SMITH-JOHN-98101")
        self.assertEqual(summary.name, "Smith, John")
        self.assertEqual(summary.zip_code, "98101")
        self.assertEqual(summary.total, Decimal(80))
        self.assertEqual(len(summary.by_party), 2)
        self.assertEqual(summary.by_party.get(Party.DEMOCRAT), Decimal(30))
        self.assertEqual(summary.by_party.get(Party.GREEN), Decimal(50))
        self.assertEqual(len(summary.by_committee), 3)
        self.assertEqual(summary.by_committee.get("C12345"), Decimal(10))
        self.assertEqual(summary.by_committee.get("C67890"), Decimal(20))
        self.assertEqual(summary.by_committee.get("CABCDE"), Decimal(50))

    def test_from_data_valid(self):
        data = {
            "fuzzy_id": "SMITH-JOHN-98101",
            "name": "Smith, John",
            "zip_code": "98101",
            "total": "80",
            "by_party": {Party.DEMOCRAT: "30", Party.GREEN: "50"},
            "by_committee": {"C12345": "10", "C67890": "20", "CABCDE": "50"},
        }
        summary = cont.ContributionSummary.from_data(data)
        self.assertEqual(summary.fuzzy_id, "SMITH-JOHN-98101")
        self.assertEqual(summary.name, "Smith, John")
        self.assertEqual(summary.zip_code, "98101")
        self.assertEqual(summary.total, Decimal(80))
        self.assertEqual(len(summary.by_party), 2)
        self.assertEqual(summary.by_party.get(Party.DEMOCRAT), Decimal(30))
        self.assertEqual(summary.by_party.get(Party.GREEN), Decimal(50))
        self.assertEqual(len(summary.by_committee), 3)
        self.assertEqual(summary.by_committee.get("C12345"), Decimal(10))
        self.assertEqual(summary.by_committee.get("C67890"), Decimal(20))
        self.assertEqual(summary.by_committee.get("CABCDE"), Decimal(50))

    def test_from_data_invalid(self):
        data = {
            "fuzzy_id": "SMITH-JOHN-98101",
        }
        with self.assertRaises(ValidationError):
            cont.ContributionSummary.from_data(data)

    def test_to_data(self):
        summary = cont.ContributionSummary.new(
            "SMITH-JOHN-98101",
            self.contribution_1,
            get_committee=self.get_committee,
        )
        summary.add(self.contribution_2, get_committee=self.get_committee)
        summary.add(self.contribution_3, get_committee=self.get_committee)
        data = summary.to_data()
        self.assertEqual(data["fuzzy_id"], "SMITH-JOHN-98101")
        self.assertEqual(data["name"], "Smith, John")
        self.assertEqual(data["zip_code"], "98101")
        self.assertEqual(data["total"], "80")
        self.assertEqual(len(data["by_party"]), 2)
        self.assertEqual(data["by_party"].get(Party.DEMOCRAT), "30")
        self.assertEqual(data["by_party"].get(Party.GREEN), "50")
        self.assertEqual(len(data["by_committee"]), 3)
        self.assertEqual(data["by_committee"].get("C12345"), "10")
        self.assertEqual(data["by_committee"].get("C67890"), "20")
        self.assertEqual(data["by_committee"].get("CABCDE"), "50")


class ContributionsManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.contribution_1 = cont.Contribution(
            id="12345",
            committee_id="C12345",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(10),
        )
        self.contribution_2 = cont.Contribution(
            id="12346",
            committee_id="C67890",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(20),
        )
        self.contribution_3 = cont.Contribution(
            id="12347",
            committee_id="CABCDE",
            name="Smith, John",
            city="Seattle",
            state="WA",
            zip_code="98101",
            amount=Decimal(50),
        )
        self.contributions = [
            self.contribution_1,
            self.contribution_2,
            self.contribution_3,
        ]
        self.get_committee = MockGetCommittee(
            [
                Committee(
                    id="C12345",
                    name="Barney for America",
                    party=Party.DEMOCRAT,
                    candidate_id="CAN12345",
                ),
                Committee(
                    id="C67890",
                    name="Donald for Duck",
                    party=Party.DEMOCRAT,
                    candidate_id="CAN67890",
                ),
                Committee(
                    id="CABCDE",
                    name="Jupiter for Pluto",
                    party=Party.GREEN,
                    candidate_id="CANABCDE",
                ),
            ]
        )
        self.get_nickname_index = MockGetNicknameIndex(
            [["Dave", "David", "Davey"], ["Matt", "Matthew"]]
        )

    def test_contributions(self):
        manager = cont.ContributionsManager(
            self.contributions,
            get_committee=self.get_committee,
            get_nickname_index=self.get_nickname_index,
        )
        self.assertEqual(len(manager.contributions), 3)

    def test_from_csv_io(self):
        contribution_1 = """C12345||||||IND|Smith, John|Seattle|WA|98101||||10||||||12345"""  # noqa: E501
        contribution_2 = """C12345||||||COM|Smith, John|Seattle|WA|98101||||10||||||12345"""  # noqa: E501
        csv_io = io.StringIO("\n".join([contribution_1, contribution_2]))
        manager = cont.ContributionsManager.from_csv_io(
            csv_io,
            get_committee=self.get_committee,
            get_nickname_index=self.get_nickname_index,
        )
        self.assertEqual(len(manager.contributions), 1)
        self.assertEqual(manager.contributions[0].id, "12345")

    def test_contribution_summaries(self):
        manager = cont.ContributionsManager(
            self.contributions,
            get_committee=self.get_committee,
            get_nickname_index=self.get_nickname_index,
        )
        self.assertEqual(len(manager.contribution_summaries), 1)
        self.assertEqual(manager.contribution_summaries["SMITH-JOHN-98101"].total, 80)

    def test_contribution_summaries_manager(self):
        manager = cont.ContributionsManager(
            self.contributions,
            get_committee=self.get_committee,
            get_nickname_index=self.get_nickname_index,
        )
        summaries_manager = manager.contribution_summaries_manager
        self.assertEqual(len(summaries_manager.contribution_summaries), 1)
