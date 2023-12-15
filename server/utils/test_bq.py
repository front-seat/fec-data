# ruff: noqa: D102

import unittest

from google.cloud import bigquery

from .bq import Statement


class QueryBuilderTestCase(unittest.TestCase):
    def test_build_query_select_star(self):
        qb = Statement("table")
        query = qb.build_query()
        self.assertEqual(query, "SELECT * FROM 'table'")

    def test_build_query_select_one_column(self):
        qb = Statement("table").select("column")
        query = qb.build_query()
        self.assertEqual(query, "SELECT column FROM 'table'")

    def test_build_query_select_one_column_alias(self):
        qb = Statement("table").select(("column", "alias"))
        query = qb.build_query()
        self.assertEqual(query, "SELECT column AS alias FROM 'table'")

    def test_build_query_select_multiple_columns_separately(self):
        qb = Statement("table").select("column1").select("column2")
        query = qb.build_query()
        self.assertEqual(query, "SELECT column1, column2 FROM 'table'")

    def test_build_query_select_multiple_columns_together(self):
        qb = Statement("table").select("column1", "column2")
        query = qb.build_query()
        self.assertEqual(query, "SELECT column1, column2 FROM 'table'")

    def test_build_query_select_multiple_columns_with_aliases(self):
        qb = Statement("table").select(("column1", "alias1"), ("column2", "alias2"))
        query = qb.build_query()
        self.assertEqual(
            query, "SELECT column1 AS alias1, column2 AS alias2 FROM 'table'"
        )

    def test_where_equality_int64(self):
        qb = Statement("table").where("column", "=", 1)
        query = qb.build_query()
        self.assertEqual(query, "SELECT * FROM 'table' WHERE column = @param0")
        query_params = qb.build_query_params()
        self.assertEqual(len(query_params), 1)
        self.assertEqual(
            query_params[0], bigquery.ScalarQueryParameter("param0", "INT64", 1)
        )

    def test_where_lte_string(self):
        qb = Statement("table").where("column", "<=", "potato")
        query = qb.build_query()
        self.assertEqual(query, "SELECT * FROM 'table' WHERE column <= @param0")
        query_params = qb.build_query_params()
        self.assertEqual(len(query_params), 1)
        self.assertEqual(
            query_params[0], bigquery.ScalarQueryParameter("param0", "STRING", "potato")
        )
