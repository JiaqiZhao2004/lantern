# Transaction ledger is a top-level cursor-paginated route

The Member-facing transaction ledger lives at its own top-level route instead of inside the dashboard, and its API uses cursor pagination with exact filtered counts. We chose this because the dashboard is reserved for saved analysis surfaces like Named Queries, while the ledger is a separate high-frequency inspection tool whose ordering must stay stable as new Transactions arrive.
