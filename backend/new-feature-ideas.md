# Agentic creation of personal widgets

We want to create an agent that can generate comprehensive SQL queries safely for users trying to monitor their spending / income. The agent mainly interacts with the postgres DB's two views, widget_accounts and widget_transactions. (the names of the views should be changed since we are avoiding the term widgets.)

User story:
I want to monitor my spending on recurring subscriptions, grouped by the category they are in. However, I don't know what subscriptions I currently have.

In this example, a good agent will go into the transactions table to look for these kind of subscriptions and generate useful SQL query. At the same time only give the LLM desensitized information and never reveal PII.
A very good agent generates SQL that can also automatically pick up later added subscription spending, without the user asking. 
An excellent agent does all this while keeping the cost and latency low.

can you help me refine this problem statement like a product manager?

**Monitor**:
The Member-facing concept for a saved, reusable view of Household financial activity. A Monitor helps Members track spending or income patterns over time and may be backed internally by a Named Query. Members should not need to know SQL to create or use a Monitor.
_Avoid_: Widget
