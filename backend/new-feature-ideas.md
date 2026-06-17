# AI-assisted creation of personal widgets

The user may have a thousand ideas on how they want to monitor their money. And we cannot exhaust all of them. Therefore, instead of providing fixed features, we want to allow the users to use AI to create their own.
This idea is the term Personal Widgets -- it can have a better name, but let's just call it that for now. Behind each of these widgets should be a micro ETL pipeline. Yes, this is pretty wild, so we should consider how to do it carefully.
Let's brainstorm by looking at some use cases.
1. The first case is aggregated weekly spending over a year. How can we gather this data from basic transaction rows? 
The simplest solution is just stored the E and T rules in ETL, and then calculate the graph on the fly. We don't use any materialized views or extra tables to store intermediate calculations like the aggregated spending of each week, but we recalculate the per week sum every time. This is probably more than enough for the first iteration.
So for the E and T rules, we will need to design a little bit. For extraction, this means a time range scoped to the current calendar year, and a selection of only expenditures, not income. For T it means detecting the week boundaries and then do sum based on it.
For flexibility, we can create a unified filter rule that takes a column name, an operator like IN, >, <, >=, <=, EQUALS, NOT EQUALS, and a value or a set of values. This filter will be generic enough to work for both the time range filter and the selection based on type of transaction.
Then, for T, currently, we start with aggregations. For this aggregation we need group-by-week as the grouping and then SUM as the transformation.
Actually, looking back, we are just recreating SQL. So maybe our MVP is just skipping the rules and just use raw SQL as the selector. The user writes the SQL or generate it using an LLM Assistant provided in the app. Then the backend receives the SQL, checks it and then run it on the database, then return to the user. I know this can be vulnerable to SQL injection so we might have to figure out a mechanism to prevent it.
