# Natural sign convention for transaction amounts

We store transaction amounts with positive = inflow (deposits, refunds) and negative = outflow (purchases, fees), matching how a bank statement reads to a Member. Plaid's wire format is the inverse (positive = outflow), so we negate at the ingest boundary in the mapper.

We chose the natural convention because all consumers — queries, reports, and the future LLM layer — can use `SUM(amount)` directly to get net cash flow with the correct sign. Under Plaid's convention every read site would need to remember to negate, and a missed negation produces silently wrong numbers.
