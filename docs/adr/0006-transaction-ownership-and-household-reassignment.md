# Transactions are owned by the User, not the Household

Transactions belong to the User whose InstitutionConnection produced them. `household_id` on the `transactions` table is nullable and denormalized — it reflects the User's current Household for query performance, not ownership.

**Lifecycle:**
- While a User is a Member of a Household: `household_id` is set; the Household sees these Transactions.
- When a User leaves (self-removal): `household_id` is set to NULL; the Transactions become invisible to the old Household.
- When a User joins a new Household: `household_id` is updated to the new Household; the new Household sees the User's full Transaction history from before the join.

**Why not delete on departure:**
The User owns the data — deleting it on departure would mean repulling everything from Plaid when they join a new Household. That is expensive, slow, and may not be possible if Plaid's history window has advanced.

**Why full history follows the User to the new Household (not just from join date):**
Simplicity. Scoping visibility to post-join Transactions requires a cutoff timestamp per (User, Household) pair, complicating every query. This can be revisited if the "new household-mates can see your entire history" behaviour proves unwanted.

**Code implication:**
`ON DELETE CASCADE` on `transactions.household_id` must not be used — that would delete Transactions when a Household is deleted, not when a User leaves. Household deletion and User self-removal are handled by explicit service-layer logic.
