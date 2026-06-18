# Named Queries are the dashboard landing page; connections and accounts move to Settings

The `/dashboard` route now renders Named Queries as the primary content Members see when they open the app. InstitutionConnection and Account management (previously at `/dashboard`) moves to a `/settings` route. Settings was chosen over a narrower name like "Connections" because profile and preferences are expected to live there eventually — the label should match the eventual scope, not just what's there today.

## Considered Options

Keeping connections/accounts on the dashboard and adding Named Queries as a new section was rejected because Named Queries are the analytical surface Members use daily, while connection management is infrequent setup work. Burying Named Queries below institution setup would invert the priority.
