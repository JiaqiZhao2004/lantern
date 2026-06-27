import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NamedQueryEditorPage from "@/features/named-queries/pages/NamedQueryEditorPage";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useAccountsQuery } from "@/features/connections/api/queries";
import { useHouseholdQuery } from "@/features/household/api/queries";
import {
  useCreateNamedQueryMutation,
  useGenerateNamedQueryMutation,
  useNamedQueriesQuery,
  usePatchNamedQueryMutation,
  usePreviewNamedQueryMutation,
} from "@/features/named-queries/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";

vi.mock("@/features/auth/session/AuthSessionProvider", () => ({
  useAuthSession: vi.fn(),
}));

vi.mock("@/features/viewer/api/queries", () => ({
  useViewerQuery: vi.fn(),
}));

vi.mock("@/features/household/api/queries", () => ({
  useHouseholdQuery: vi.fn(),
}));

vi.mock("@/features/connections/api/queries", () => ({
  useAccountsQuery: vi.fn(),
}));

vi.mock("@/features/named-queries/api/queries", () => ({
  useCreateNamedQueryMutation: vi.fn(),
  useGenerateNamedQueryMutation: vi.fn(),
  useNamedQueriesQuery: vi.fn(),
  usePatchNamedQueryMutation: vi.fn(),
  usePreviewNamedQueryMutation: vi.fn(),
}));

const mockedUseAuthSession = vi.mocked(useAuthSession);
const mockedUseViewerQuery = vi.mocked(useViewerQuery);
const mockedUseHouseholdQuery = vi.mocked(useHouseholdQuery);
const mockedUseAccountsQuery = vi.mocked(useAccountsQuery);
const mockedUseNamedQueriesQuery = vi.mocked(useNamedQueriesQuery);
const mockedUseCreateNamedQueryMutation = vi.mocked(useCreateNamedQueryMutation);
const mockedUsePatchNamedQueryMutation = vi.mocked(usePatchNamedQueryMutation);
const mockedUsePreviewNamedQueryMutation = vi.mocked(usePreviewNamedQueryMutation);
const mockedUseGenerateNamedQueryMutation = vi.mocked(useGenerateNamedQueryMutation);

function renderEditor() {
  return render(
    <MemoryRouter initialEntries={["/queries/new"]}>
      <Routes>
        <Route path="/queries/new" element={<NamedQueryEditorPage />} />
        <Route path="/dashboard" element={<div>Dashboard destination</div>} />
        <Route path="/transactions" element={<div>Transactions destination</div>} />
        <Route path="/settings" element={<div>Settings destination</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("NamedQueryEditorPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: { email: "user@example.com", emailVerified: true },
    } as never);
    mockedUseViewerQuery.mockReturnValue({
      data: { email: "user@example.com", name: "Viewer" },
      isError: false,
      isLoading: false,
    } as never);
    mockedUseHouseholdQuery.mockReturnValue({
      data: { name: "Household" },
      isError: false,
      isLoading: false,
    } as never);
    mockedUseAccountsQuery.mockReturnValue({
      data: { items: [] },
      isError: false,
      isLoading: false,
    } as never);
    mockedUseNamedQueriesQuery.mockReturnValue({
      data: [],
      isError: false,
      isLoading: false,
    } as never);
    mockedUseCreateNamedQueryMutation.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    } as never);
    mockedUsePatchNamedQueryMutation.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    } as never);
    mockedUsePreviewNamedQueryMutation.mockReturnValue({
      data: undefined,
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    } as never);
    mockedUseGenerateNamedQueryMutation.mockReturnValue({
      error: null,
      isError: false,
      isPending: false,
      mutateAsync: vi.fn(),
    } as never);
  });

  it("blocks app-shell navigation when the draft is dirty and the user stays", () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    renderEditor();

    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Generated spending query" },
    });
    fireEvent.click(screen.getByRole("link", { name: "Dashboard" }));

    expect(confirmSpy).toHaveBeenCalledWith(
      "You have unsaved named query changes. Leave this page and lose them?"
    );
    expect(screen.getByRole("heading", { name: "New Named Query" })).toBeInTheDocument();
    expect(screen.queryByText("Dashboard destination")).not.toBeInTheDocument();
  });

  it("lets cancel navigate away after confirmation", () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderEditor();

    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Generated spending query" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.getByText("Dashboard destination")).toBeInTheDocument();
  });
});
