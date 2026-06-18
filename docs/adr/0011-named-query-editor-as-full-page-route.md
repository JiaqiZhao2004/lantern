# Named Query editor is a full-page route, not a modal

Create and edit flows for Named Queries live at `/queries/new` and `/queries/{id}/edit`. The editor shows a SQL input and a live preview panel side-by-side; a modal cannot accommodate that layout without cramping both panels. A full-page route also gives draft state a stable URL, preventing accidental loss from modal dismissal.

## Considered Options

A modal over the dashboard was rejected because the preview panel (SQL editor + live results rendered simultaneously) requires horizontal space that a modal cannot provide without dominating the viewport.
