# Archived Plaid Quickstart

This directory contains the older Plaid quickstart-style frontend that used
demo endpoints and local reducer/context state.

It was archived during the application refactor because the active frontend now
uses:

- route guards instead of effect-driven redirects
- TanStack Query for backend data access
- shared UI primitives under `src/shared/ui`
- contract-aligned Plaid support based on `src/core/backendDTOTypes.ts`

Keep this directory only as historical reference while the backend Plaid
exchange flow catches up to the new contract-aligned frontend.
