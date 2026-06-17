# Vendor-neutral names for financial integration entities

Domain entities are named after the concepts they represent, not after the vendor that provides the underlying data. Concretely: `InstitutionConnection` (not `PlaidItem`), `Account` (not `PlaidAccount`), `SyncJob` (not `PlaidSyncJob`).

Plaid-specific identifiers and credentials live as fields prefixed with `plaid_` (e.g. `plaid_access_token_ciphertext`, `plaid_account_id`) so the seam is visible, but the entity names and the domain language are vendor-agnostic.

We chose this because the domain concept — "a connection to a bank that syncs accounts and transactions" — outlives any particular aggregator. Naming entities after Plaid would force a rename cascade if we ever add a second aggregator or manual entry, and would leak vendor vocabulary into every layer of the product (API responses, reports, LLM prompts).
