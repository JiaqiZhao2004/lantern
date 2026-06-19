# App provides LLM generation for Named Query SQL candidates

AI-assisted Named Query creation generates an ephemeral SQL candidate through an app-provided LLM integration, not a Household-provided API key. The LLM receives only the Named Query schema contract and the Member's request, not Transaction rows, so the primary risks are abuse and cost rather than financial data exposure. Those risks are controlled with a per-Household daily quota, matching the ownership boundary of Named Queries and avoiding a new Household credential-management feature.

The LLM generation conversation is ephemeral page state owned by the frontend. Each generation request sends the current short page-session message transcript to the backend. If the LLM needs clarification, it may ask one clarifying question at a time while the Member stays on the creation page, but refreshing or leaving the page discards that conversation and any generated SQL candidate. The only persisted Household resource is the Named Query created when a Member explicitly saves a generated or manually edited SQL candidate.

When the LLM produces SQL, the backend validates it against the same Named Query SQL rules used by manual queries before returning it to the Member. Invalid SQL is not returned; the backend feeds the validation error back to the LLM within a bounded repair loop. If the LLM still cannot produce valid SQL, the backend returns a generation failure and asks the Member to rephrase.

The Named Query generation endpoint returns a complete form candidate — name, SQL body, and chart type hint — so the frontend can prefill the normal Named Query creation UI. Lower-level LLM infrastructure remains domain-agnostic and may be reused for other endpoints later; the Named Query generation service owns the prompt, schema contract, validation, and repair loop for this feature.

The per-Household daily quota uses a simple v1 model: each Member message that asks the LLM to generate SQL or continue after a clarifying question consumes one quota unit, while backend repair attempts for invalid SQL do not. The quota is intended as an abuse and cost backstop, not as a normal product limit Members routinely encounter. The app records generation observability — quota units consumed, LLM calls made, clarification outcomes, validation failures, repair attempts, and generation failures — so the quota model can be tuned after real usage. The generation prompt also constrains the LLM to help only with creating Named Query SQL for this app, but prompt scope is treated as product guidance rather than the sole abuse-control mechanism.

## Considered Options

Household-provided API keys were rejected for v1 because they add storage, validation, rotation, provider-specific failure states, and unclear Member usage semantics. Since Named Queries are Household resources usable by any Member, a Household key would either be consumable by every Member or require new role rules for feature usage.

Having the LLM produce a structured query specification, which the backend would compile into SQL, is a strong long-term direction because it would move validation earlier and reduce SQL repair. It is deferred for v1 in favor of returning validated SQL candidates directly, because the existing Named Query contract is already SQL and the flat SELECT validator provides a practical safety boundary.
