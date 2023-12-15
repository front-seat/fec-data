"""BigQuery utilities."""

import datetime
import typing as t
from abc import ABC, abstractmethod

from google.cloud import bigquery
from google.cloud.bigquery import query

type QueryParamValue = str | int | float | datetime.date | datetime.datetime | t.Sequence[  # noqa: E501
    str
]
type QueryParams = t.Mapping[str, QueryParamValue]


def default_table_alias(table_name: str, table_alias: str | None = None) -> str | None:
    """Return the default table alias if appropriate, and no explicit alias is given."""
    if not table_alias and "." in table_name:
        table_alias = table_name.split(".")[-1]
    return table_alias


class Statement:
    """A BigQuery SQL statement builder."""

    table_name: str
    table_alias: str | None
    select_columns: list[str]
    filters: list[str]
    joins: list[str]
    params: dict[str, QueryParamValue]

    def __init__(self, table_name: str, table_alias: str | None = None):
        self.table_name = table_name
        self.table_alias = default_table_alias(table_name, table_alias)
        self.table_alias = table_alias
        self.select_columns = []
        self.filters = []
        self.joins = []
        self.params = {}

    def select(
        self,
        *columns: str | tuple[str, str],
    ):
        """Add a column to the SELECT clause of the query."""
        for column in columns:
            if isinstance(column, tuple):
                self.select_columns.append(f"{column[0]} AS {column[1]}")
            else:
                self.select_columns.append(column)
        return self

    def where(self, column, operator, value, param_name=None):
        """Add a filter to the WHERE clause of the query."""
        if param_name is None:
            param_name = f"param{len(self.params)}"
        self.params[param_name] = value
        if operator.lower() == "in":
            condition = f"{column} IN UNNEST(@{param_name})"
        else:
            condition = f"{column} {operator} @{param_name}"
        self.filters.append(condition.strip())
        return self

    def join(
        self, table_name, on_clause, join_type="INNER", table_alias: str | None = None
    ):
        """Add a JOIN clause to the query."""
        table_alias = default_table_alias(table_name, table_alias)
        alias_clause = f" AS {table_alias}" if table_alias else ""
        self.joins.append(
            f"{join_type} JOIN `{table_name}`{alias_clause} ON {on_clause}"
        )
        return self

    def build_query(self):
        """Build the query string."""
        select_clause = ", ".join(self.select_columns) or "*"
        join_clause = " ".join(self.joins).strip()
        where_clause = " AND ".join(self.filters) if self.filters else ""

        alias_clause = f" AS {self.table_alias}" if self.table_alias else ""

        query_parts = [
            f"SELECT {select_clause} FROM `{self.table_name}`{alias_clause}",
        ]
        if join_clause:
            query_parts.append(join_clause)
        if where_clause:
            query_parts.append(f"WHERE {where_clause}")
        return " ".join(query_parts).strip()

    def build_query_param(
        self, name: str, value: QueryParamValue
    ) -> query._AbstractQueryParameter:
        """Build a query parameter."""
        if isinstance(value, str):
            return bigquery.ScalarQueryParameter(name, "STRING", value)
        elif isinstance(value, int):
            return bigquery.ScalarQueryParameter(name, "INT64", value)
        elif isinstance(value, float):
            return bigquery.ScalarQueryParameter(name, "FLOAT64", value)
        elif isinstance(value, datetime.datetime):
            return bigquery.ScalarQueryParameter(name, "DATETIME", value)
        elif isinstance(value, datetime.date):
            return bigquery.ScalarQueryParameter(name, "DATE", value)
        elif isinstance(value, t.Sequence):
            if all(isinstance(v, str) for v in value):
                return bigquery.ArrayQueryParameter(name, "STRING", value)
        raise ValueError(f"Unsupported parameter type: {type(value)}")

    def build_query_params(self):
        """Build the query parameters."""
        return [
            self.build_query_param(name, value) for name, value in self.params.items()
        ]

    def build_query_job_config(self):
        """Build the query job config."""
        return bigquery.QueryJobConfig(query_parameters=self.build_query_params())


class BQClient(bigquery.Client):
    """Our BigQuery client, with some extra methods for convenience."""

    def execute(self, statement: Statement):
        """Execute the query."""
        query = statement.build_query()
        job_config = statement.build_query_job_config()
        job = self.query(query, job_config=job_config)
        return job.result()


class Table[ModelT](ABC):
    """Base class for all 'tables' -- aka managers for getting data from BQ."""

    client: BQClient
    name: str
    alias: str | None

    def __init__(self, client: BQClient, name: str, alias: str | None = None):
        self.client = client
        self.name = name
        self.alias = default_table_alias(name, alias)

    @abstractmethod
    def get_model_instance(self, bq_row: t.Any) -> ModelT:
        """Create an instance from a BigQuery row."""
        ...

    def execute(self, statement: Statement) -> t.Iterable[ModelT]:
        """Execute a BigQuery statement."""
        return (self.get_model_instance(row) for row in self.client.execute(statement))

    def all_stmt(self) -> Statement:
        """Return the default statement."""
        return Statement(self.name, self.alias)

    def all(self) -> t.Iterable[ModelT]:
        """Return the default query."""
        return self.execute(self.all_stmt())


def get_client(project_id: str = "five-minute-5") -> BQClient:
    """Get a BigQuery client for a specific GCP project ID."""
    return BQClient(project_id)
