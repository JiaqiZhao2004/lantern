# Named Query feature design decisions

This ADR captures the key design decisions made for the Named Query feature.

## SQL restricted to flat SELECT (see ADR-0007)
See [0007-named-query-sql-restricted-to-flat-select.md](0007-named-query-sql-restricted-to-flat-select.md).

## Stable views as the schema coupling boundary

Two Postgres views — `widget_transactions` and `widget_accounts` — act as the public API contract for Named Query SQL. Internal column renames and refactors are absorbed by updating the view, not the saved queries. The views bake in mandatory filters (`is_removed = false`, `is_active = true`, `is_hidden = false`) and expose `household_id` on both views for tenancy injection.

**Why views, not raw tables:**
Decouples the Member-facing column namespace from the internal schema. A future rename of `occurred_at` → `transaction_date` updates the view definition only; no saved Named Query breaks.

## `household_id` is a reserved column

Named Query SQL bodies must not reference `household_id` in their WHERE clause. The backend injects `AND household_id = :current_household_id` automatically. Queries that reference `household_id` in WHERE are rejected at validation time with a 422.

**Why reject rather than strip-and-replace:**
Silent replacement would be surprising and harder to audit. Rejection with a clear error message is unambiguous.

## Named Queries belong to the Household, not the Member

No `created_by_user_id` on the `named_queries` table. Any Member can create, patch, or delete any Named Query. This is consistent with the existing trust model — role governs Household administration only, never data visibility or mutation.

## `chart_type` is a nullable opaque string

The backend stores and returns `chart_type` without interpretation or validation. The frontend owns chart semantics entirely. Nullable so a Named Query can be created without a chart preference.

**Why not a backend enum:**
Coupling the backend to the frontend's chart library vocabulary means a backend migration every time the frontend adds a chart type.

## Execution uses a read-only transaction on the main connection

Named Query execution runs in a session with `SET TRANSACTION READ ONLY` and `statement_timeout = 2s`, on the main DB connection pool. A separate `widget_reader` Postgres role is deferred as a future hardening step.

**Why defer the separate role:**
`SET TRANSACTION READ ONLY` provides the critical safety guarantee (no writes possible in that session) without requiring a second set of credentials and a separate connection pool. The role adds defense-in-depth but is not the primary enforcement boundary.

## Response shape for query execution

```json
{
  "columns": [{"name": "category", "type": "text"}, ...],
  "rows": [{"category": "FOOD_AND_DRINK", "total_spend": "-342.50"}, ...],
  "truncated": false
}
```

- Rows as objects (column name → value) — frontend does not need to zip columns and values.
- Numeric values serialized as strings — avoids float precision loss on the wire.
- `truncated: true` when the 500-row cap is hit — Member knows to refine their query.

## Execution errors return 422, Named Query left intact

If a saved Named Query fails at execution time (e.g. a view column it referenced was removed), the response is 422 with a structured error body. The Named Query is not deleted or flagged automatically — it was valid when saved, the Member's work is preserved.

## Migration rollback deletes Named Query rows

The `downgrade()` for the Named Query migrations deletes all `named_queries` rows before dropping the views. Rolling back past the Named Query feature is a destructive operation. Scheduled DB backups should be in place before this feature is deployed to production.
