import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NamedQueryResultTable } from "@/features/named-queries/components/NamedQueryResultTable";

describe("NamedQueryResultTable", () => {
  it("renders a centered stat for a single-value result", () => {
    render(
      <NamedQueryResultTable
        columns={[{ name: "status", type: "text" }]}
        rows={[{ status: "Ready" }]}
        truncated={false}
      />
    );

    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("status")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("keeps the table for multi-column results", () => {
    render(
      <NamedQueryResultTable
        columns={[
          { name: "month", type: "text" },
          { name: "total_spend", type: "numeric" },
        ]}
        rows={[{ month: "2026-06", total_spend: "1234.56" }]}
        truncated={false}
      />
    );

    const table = screen.getByRole("table");
    expect(within(table).getByText("month")).toBeInTheDocument();
    expect(within(table).getByText("2026-06")).toBeInTheDocument();
    expect(within(table).getByText("1234.56")).toBeInTheDocument();
  });
});
