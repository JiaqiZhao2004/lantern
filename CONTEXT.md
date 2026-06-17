# Family Finance Backend

A backend that lets a family pool their bank accounts (via Plaid) into a shared household and see all their transactions in one place. Scoped specifically to families because members can see each other's transactions — the trust model does not extend to friends or roommates.

## Language

**Household**:
A financial unit of people (a family) who share visibility into each other's bank accounts and transactions. The unit of access control for all financial data.
_Avoid_: Family, Group, Account

**User**:
An authenticated identity (Firebase-backed) with an email. Exists from signup, before joining any Household. A User belongs to at most one Household at a time. They may leave and join a different Household, but the previous membership is terminated — concurrent membership is not allowed.
_Avoid_: Account, Person

**Member**:
A User in the context of their Household, with a role. The thing that has permissions and sees transactions. Same person as the User, different concept — talk about Members when discussing access and visibility, Users when discussing identity and authentication. All Members of a Household see all other Members' transactions equally, regardless of role.

A User who has left their Household is no longer a Member anywhere — they enter a transient state between Households until they join or create a new one. In that state they can authenticate but cannot see any financial data. Only self-removal is supported; an Owner cannot remove another Member.
_Avoid_: Participant

**Owner**:
The Member who created the Household. Can invite and remove other Members and delete the Household. The only role with administrative authority.
_Avoid_: Admin

**Role**:
A Member's authority level within their Household. One of `owner` or `member`. Governs administrative actions on the Household only — never transaction visibility.

**InstitutionConnection**:
A persistent connection from a Household to a financial institution (e.g. a bank), through which we sync Accounts and Transactions. Vendor-neutral — currently always backed by a Plaid Item. Owned by the User who linked it. When that User leaves the Household, their InstitutionConnections are deactivated. When they join a new Household, they re-link their banks fresh — new InstitutionConnections are created.
_Avoid_: PlaidItem, Connection, Link

**Institution**:
A financial provider (bank, credit union, brokerage) that holds Accounts. Identified by Plaid's `institution_id` and a human-readable name. Currently a value, not its own entity — lives as fields on `InstitutionConnection`.
_Avoid_: Bank, Provider

**Account**:
A single bank or credit account at an Institution (checking, savings, credit card, etc.) that contributes Transactions to a Household. First-class to Members — they see Accounts in the UI, can hide and reorder them. One InstitutionConnection has many Accounts.
_Avoid_: PlaidAccount, BankAccount

**Transaction**:
A single financial event on an Account that a Member can see — a purchase, deposit, transfer, fee, refund. The logical entity, not the row. A pending charge that later posts is one Transaction whose state changes from `pending` to `posted`, even though it occupies two database rows during that lifecycle. Members never see removed Transactions.

Transactions are owned by the User whose InstitutionConnection produced them, not by the Household. `household_id` is a nullable denormalization — it is set to the User's current Household for query performance, set to NULL when the User is between Households, and reassigned when the User joins a new Household. The new Household sees the User's full Transaction history from the moment they join.

**Pending Transaction**:
A Transaction in the `pending` state — authorized by the institution but not yet cleared. Will later be replaced by a posted Transaction (and the pending row internally tombstoned via `is_removed`).

**Posted Transaction**:
A Transaction that has cleared at the institution and reflects a settled charge or deposit. The final state in the lifecycle.

**Removed Transaction**:
An internal tombstone, not a domain concept Members see. Used when Plaid retracts a Transaction (e.g. the pending version was replaced, or fraud reversal). Removed Transactions are excluded from every Member-facing view.
_Avoid_: Deleted Transaction

**Occurred At**:
The date a Transaction happened from the Member's perspective — what shows in lists and reports. Defined as `authorized_date` when the institution provides one, otherwise `posted_date`. The Member-facing date; never an internal-only timestamp like `created_at`.
_Avoid_: Effective Date, Transaction Date, Activity Date

**Inflow / Outflow**:
The direction of a Transaction's money movement. Inflows are positive amounts (deposits, refunds, paychecks). Outflows are negative amounts (purchases, fees, withdrawals). The DB and API use the natural convention — positive = money in, negative = money out — matching how a bank statement reads to a Member.
_Avoid_: Debit, Credit (these have opposite meanings depending on the account type, which makes them ambiguous)

**SyncJob**:
A unit of work that fetches fresh data for an InstitutionConnection. Subject-agnostic — what it fetches is captured by its Sync Subject; why it ran is captured by its Sync Trigger. One InstitutionConnection has at most one queued or running SyncJob at a time per subject.
_Avoid_: Job, Task, TransactionSyncJob

**Sync Subject**:
The kind of data a SyncJob fetches. Currently only `transactions`; the field exists so future subjects (`balances`, `identity`, `holdings`) can be added without reshaping the model.
_Avoid_: Sync Type, Job Type

**Sync Trigger**:
The reason a SyncJob was enqueued. One of `webhook` (Plaid notified us), `onboarding` (a new InstitutionConnection was just linked), or `manual_resync` (a Member asked for a refresh). Distinct from Sync Subject — same Subject, different Triggers, are common.
_Avoid_: Job Type, Cause, Source

**Sync State**:
The current health of an InstitutionConnection's sync — one of `in_sync`, `syncing`, `retry_scheduled`, `needs_reauth`, or `disabled`. Lives on the InstitutionConnection because there is only one Sync Subject today (transactions); the state implicitly refers to that subject. If a second subject is ever added, this field has to be either split per-subject or redefined as an aggregate.
_Avoid_: Status (overloaded), Health
