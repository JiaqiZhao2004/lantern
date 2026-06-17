# Named Query SQL is restricted to flat SELECT statements

Named Query SQL bodies must be a single, flat SELECT statement — no CTEs (`WITH`), no subqueries, no nested SELECTs. This restriction applies to the MVP; it may be lifted in a future iteration.

**Why flat SELECT only:**
The Named Query executor injects a `household_id` filter before running user-supplied SQL. With a flat SELECT, the injector has exactly one place to attach the filter — the top-level WHERE clause. CTEs and subqueries require walking the full AST to find every node that references `widget_transactions` or `widget_accounts` and injecting the filter at each one. That logic is non-trivial and hard to audit for security correctness.

**Why this is not an expressiveness blocker:**
The primary use cases — spending by category, weekly totals, top merchants, month-over-month comparisons — are all expressible as flat SELECTs using GROUP BY, HAVING, ORDER BY, and LIMIT. The cases that genuinely require subqueries (e.g. "transactions above the household average") are edge cases, not core use cases.

**When to lift this restriction:**
If Members need to express queries that flat SELECT cannot cover, extend the injector to walk the full AST and inject at every table reference. At that point, write a new ADR documenting the injection strategy for nested queries.
