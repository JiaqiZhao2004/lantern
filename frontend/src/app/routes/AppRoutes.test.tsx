import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AppRoutes } from "@/app/routes/AppRoutes";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useMembershipQuery } from "@/features/household/api/queries";
import { useViewerQuery } from "@/features/viewer/api/queries";

vi.mock("@/features/auth/session/AuthSessionProvider", () => ({
  useAuthSession: vi.fn(),
}));

vi.mock("@/features/viewer/api/queries", () => ({
  useViewerQuery: vi.fn(),
}));

vi.mock("@/features/household/api/queries", () => ({
  useMembershipQuery: vi.fn(),
}));

const mockedUseAuthSession = vi.mocked(useAuthSession);
const mockedUseViewerQuery = vi.mocked(useViewerQuery);
const mockedUseMembershipQuery = vi.mocked(useMembershipQuery);

function renderRoutes(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AppRoutes />
    </MemoryRouter>
  );
}

describe("AppRoutes", () => {
  beforeEach(() => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: null,
    });
    mockedUseViewerQuery.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      isSuccess: true,
      refetch: vi.fn(),
    } as never);
    mockedUseMembershipQuery.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      isSuccess: true,
      refetch: vi.fn(),
    } as never);
  });

  it("renders the public overview at root for signed-out users", () => {
    renderRoutes("/");

    expect(
      screen.getByRole("heading", {
        name: "See household finances clearly",
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Sign in to explore" })
    ).toHaveAttribute("href", "/login");
    expect(
      screen.getByRole("link", { name: "See walkthrough" })
    ).toHaveAttribute("href", "#walkthrough");
    expect(
      screen.getByText(
        "Lantern supports real sign-in, household setup, and app workflows; the public environment uses Plaid Sandbox for financial institution linking."
      )
    ).toBeInTheDocument();
    expect(mockedUseViewerQuery).not.toHaveBeenCalled();
    expect(mockedUseMembershipQuery).not.toHaveBeenCalled();
  });

  it("renders an app CTA at root for signed-in users without bootstrapping queries", () => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: { emailVerified: true, email: "user@example.com" },
    } as never);

    renderRoutes("/");

    expect(
      screen.getByRole("link", { name: "Open app" })
    ).toHaveAttribute("href", "/dashboard");
    expect(mockedUseViewerQuery).not.toHaveBeenCalled();
    expect(mockedUseMembershipQuery).not.toHaveBeenCalled();
  });

  it("shows a neutral CTA loading state while auth is resolving", () => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: true,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: null,
    });

    renderRoutes("/");

    expect(screen.getByText("Checking access")).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Sign in to explore" })
    ).not.toBeInTheDocument();
  });

  it("keeps dashboard routes behind authentication", async () => {
    renderRoutes("/dashboard");

    expect(
      await screen.findByRole("heading", { name: "Sign in" })
    ).toBeInTheDocument();
  });

  it("keeps transactions routes behind authentication", async () => {
    renderRoutes("/transactions");

    expect(
      await screen.findByRole("heading", { name: "Sign in" })
    ).toBeInTheDocument();
  });
});
