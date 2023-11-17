# ruff: noqa: D102
import io
import unittest

from . import nicknames as n


class MessyNicknamesTestCase(unittest.TestCase):
    def test_from_messy_io(self) -> None:
        messy_io = io.StringIO(
            """Dave  David,  Davey,  Davie  Rob\n"""
            """John  Jack,  Johnny,  Jonathan\n"""
            """Bob  Bobby,  Rob,  Robert\n"""
            """\n"""
            """Matt  // Matthew,  Matty,  Mat, Rob\n"""
        )
        manager = n.MessyNicknamesManager.from_messy_io(messy_io)
        self.assertEqual(
            manager.messy_names,
            [
                frozenset(["Dave", "David", "Davey", "Davie", "Rob"]),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
                frozenset(["Bob", "Bobby", "Rob", "Robert"]),
                frozenset(["Matt", "Matthew", "Matty", "Mat", "Rob"]),
            ],
        )

    def test_messy_names(self) -> None:
        manager = n.MessyNicknamesManager(
            [
                frozenset(["Dave", "David", "Davey", "Davie", "Rob"]),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
                frozenset(["Bob", "Bobby", "Rob", "Robert"]),
                frozenset(["Matt", "Matthew", "Matty", "Mat", "Rob"]),
            ],
        )
        self.assertEqual(
            manager.messy_names,
            [
                frozenset(["Dave", "David", "Davey", "Davie", "Rob"]),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
                frozenset(["Bob", "Bobby", "Rob", "Robert"]),
                frozenset(["Matt", "Matthew", "Matty", "Mat", "Rob"]),
            ],
        )

    def test_names(self) -> None:
        """Validate that the names are merged."""
        manager = n.MessyNicknamesManager(
            [
                frozenset(["Dave", "David", "Davey", "Davie", "Rob"]),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
                frozenset(["Bob", "Bobby", "Rob", "Robert"]),
                frozenset(["Matt", "Matthew", "Matty", "Mat", "Rob"]),
            ],
        )
        self.assertEqual(
            manager.names,
            [
                frozenset(
                    [
                        "Dave",
                        "David",
                        "Davey",
                        "Davie",
                        "Bob",
                        "Bobby",
                        "Rob",
                        "Robert",
                        "Matt",
                        "Matthew",
                        "Matty",
                        "Mat",
                    ]
                ),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
            ],
        )

    def test_nicknames_manager(self) -> None:
        manager = n.MessyNicknamesManager(
            [
                frozenset(["Dave", "David", "Davey", "Davie", "Rob"]),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
                frozenset(["Bob", "Bobby", "Rob", "Robert"]),
                frozenset(["Matt", "Matthew", "Matty", "Mat", "Rob"]),
            ],
        )
        nicknames_manager = manager.nicknames_manager
        self.assertEqual(
            nicknames_manager.names,
            [
                frozenset(
                    [
                        "Dave",
                        "David",
                        "Davey",
                        "Davie",
                        "Bob",
                        "Bobby",
                        "Rob",
                        "Robert",
                        "Matt",
                        "Matthew",
                        "Matty",
                        "Mat",
                    ]
                ),
                frozenset(["John", "Jack", "Johnny", "Jonathan"]),
            ],
        )


class NicknamesManagerTestCase(unittest.TestCase):
    def test_from_jsonl_io(self) -> None:
        jsonl_io = io.StringIO("""["A", "B"]\n["C", "D"]\n["E", "F"]\n""")
        manager = n.NicknamesManager.from_jsonl_io(jsonl_io)
        self.assertEqual(
            manager.names,
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )

    def test_names(self) -> None:
        manager = n.NicknamesManager(
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )
        self.assertEqual(
            manager.names,
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )

    def test_name_to_idnex(self) -> None:
        manager = n.NicknamesManager(
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )
        self.assertEqual(
            manager.name_to_index, {"A": 0, "B": 0, "C": 1, "D": 1, "E": 2, "F": 2}
        )

    def test_get_index(self) -> None:
        manager = n.NicknamesManager(
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )
        self.assertEqual(manager.get_index("A"), 0)
        self.assertEqual(manager.get_index("B"), 0)
        self.assertEqual(manager.get_index("C"), 1)
        self.assertEqual(manager.get_index("D"), 1)
        self.assertEqual(manager.get_index("E"), 2)
        self.assertEqual(manager.get_index("F"), 2)
        self.assertIsNone(manager.get_index("G"))

    def test_get_names_for_index(self) -> None:
        manager = n.NicknamesManager(
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )
        self.assertEqual(manager.get_names_for_index(0), frozenset({"A", "B"}))
        self.assertEqual(manager.get_names_for_index(1), frozenset({"C", "D"}))
        self.assertEqual(manager.get_names_for_index(2), frozenset({"E", "F"}))
        self.assertEqual(manager.get_names_for_index(3), frozenset())

    def test_get_related_names(self) -> None:
        manager = n.NicknamesManager(
            [
                frozenset(["A", "B"]),
                frozenset(["C", "D"]),
                frozenset(["E", "F"]),
            ],
        )
        self.assertEqual(manager.get_related_names("A"), frozenset({"A", "B"}))
        self.assertEqual(manager.get_related_names("B"), frozenset({"A", "B"}))
        self.assertEqual(manager.get_related_names("C"), frozenset({"C", "D"}))
        self.assertEqual(manager.get_related_names("D"), frozenset({"C", "D"}))
        self.assertEqual(manager.get_related_names("E"), frozenset({"E", "F"}))
        self.assertEqual(manager.get_related_names("F"), frozenset({"E", "F"}))
        self.assertEqual(manager.get_related_names("G"), frozenset())
