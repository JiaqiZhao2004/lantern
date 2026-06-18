# Frontend recognizes `bar` and `line` as chart_type values; unknown values fall back to table

The frontend defines two valid `chart_type` strings: `bar` (categorical comparisons — spending by category, top merchants) and `line` (time-series — weekly totals, month-over-month). These cover all documented Named Query use cases. If a card's `chart_type` is null or an unrecognized value, it renders as table-only with no error.

The backend stores `chart_type` as an opaque nullable string with no validation (ADR-0008). The frontend owns the chart vocabulary entirely — adding a new chart type requires no backend change.

## Considered Options

`pie` was considered for "spending by category" but rejected for MVP: it breaks down with many categories and is harder to compare. It can be added later as a new recognized value without any migration.
