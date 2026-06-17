"""
SQL validation for Named Query bodies.

Rules enforced:
- Must be a single SELECT statement (no DDL, DML, multiple statements)
- No CTEs (WITH clause) — flat SELECT only per ADR-0007
- No subqueries in FROM, WHERE, or SELECT
- Only widget_transactions and widget_accounts are allowed as table sources
- household_id must not appear in the WHERE clause (backend injects it)
"""

from typing import NamedTuple

import sqlglot
import sqlglot.expressions as exp


ALLOWED_TABLES = {"widget_transactions", "widget_accounts"}


class ValidationResult(NamedTuple):
    valid: bool
    error: str | None
    referenced_columns: list[str]


def validate_named_query_sql(sql: str) -> ValidationResult:
    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except sqlglot.errors.ParseError as e:
        return ValidationResult(False, f"SQL parse error: {e}", [])

    if not statements or len(statements) != 1:
        return ValidationResult(False, "Named Query must be a single SQL statement", [])

    stmt = statements[0]

    if not isinstance(stmt, exp.Select):
        return ValidationResult(False, "Named Query must be a SELECT statement", [])

    # Reject WITH (CTEs)
    if stmt.args.get("with"):
        return ValidationResult(False, "CTEs (WITH clause) are not allowed in Named Queries", [])

    # Reject subqueries anywhere in the tree
    for subquery in stmt.find_all(exp.Subquery):
        return ValidationResult(False, "Subqueries are not allowed in Named Queries", [])

    # Collect all table references and reject unknown tables
    table_refs = list(stmt.find_all(exp.Table))
    if not table_refs:
        return ValidationResult(False, "Named Query must reference at least one table", [])

    for table in table_refs:
        name = table.name.lower() if table.name else ""
        if name not in ALLOWED_TABLES:
            return ValidationResult(
                False,
                f"Table '{table.name}' is not allowed. Use widget_transactions or widget_accounts",
                [],
            )

    # Reject household_id in WHERE clause
    where = stmt.args.get("where")
    if where:
        for col in where.find_all(exp.Column):
            if col.name.lower() == "household_id":
                return ValidationResult(
                    False,
                    "household_id must not appear in the WHERE clause — it is injected automatically",
                    [],
                )

    # Extract referenced column names for dependency tracking
    referenced: list[str] = []
    for col in stmt.find_all(exp.Column):
        col_name = col.name.lower()
        if col_name and col_name not in referenced:
            referenced.append(col_name)

    return ValidationResult(True, None, referenced)
