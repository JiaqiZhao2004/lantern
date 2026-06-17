import { render, screen } from "@testing-library/react";
import { ReactElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import {
  EmailVerificationLayout,
  HouseholdRequiredLayout,
  HouseholdSetupLayout,
  PublicOnlyLayout,
  VerifiedSessionLayout,
} from "@/app/routes/RouteLayouts";
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

function buildQueryState(overrides: Record<string, unknown> = {}) {
  return {
    data: undefined,
    error: null,
    isError: false,
    isLoading: false,
    isSuccess: true,
    refetch: vi.fn(),
    ...overrides,
  };
}

function renderWithRoutes({
  element,
  initialEntry,
  outletLabel,
  outletPath,
}: {
  initialEntry: string;
  outletPath: string;
  outletLabel: string;
  element: ReactElement;
}) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route element={element}>
          <Route path={outletPath} element={<div>{outletLabel}</div>} />
        </Route>
        <Route path="/login" element={<div>login page</div>} />
        <Route path="/register" element={<div>register page</div>} />
        <Route path="/verify-email" element={<div>verify email page</div>} />
        <Route path="/household/setup" element={<div>household setup page</div>} />
        <Route path="/dashboard" element={<div>dashboard page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Route layouts", () => {
  beforeEach(() => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: null,
    });
    mockedUseViewerQuery.mockReturnValue(buildQueryState() as any);
    mockedUseMembershipQuery.mockReturnValue(buildQueryState() as any);
  });

  it("renders public routes for signed-out users", () => {
    renderWithRoutes({
      initialEntry: "/login",
      outletPath: "/login",
      outletLabel: "login page",
      element: <PublicOnlyLayout />,
    });
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("redirects signed-in but unverified users to email verification", async () => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: { emailVerified: false },
    } as never);

    renderWithRoutes({
      initialEntry: "/login",
      outletPath: "/login",
      outletLabel: "login page",
      element: <PublicOnlyLayout />,
    });
    expect(await screen.findByText("verify email page")).toBeInTheDocument();
  });

  it("redirects verified users without a household to setup", async () => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: { emailVerified: true },
    } as never);
    mockedUseViewerQuery.mockReturnValue(
      buildQueryState({ data: { id: "user-1" } }) as any
    );
    mockedUseMembershipQuery.mockReturnValue(
      buildQueryState({ data: null }) as any
    );

    renderWithRoutes({
      initialEntry: "/login",
      outletPath: "/login",
      outletLabel: "login page",
      element: <PublicOnlyLayout />,
    });
    expect(await screen.findByText("household setup page")).toBeInTheDocument();
  });

  it("redirects unauthenticated access to verified routes back to login", async () => {
    renderWithRoutes({
      initialEntry: "/dashboard",
      outletPath: "/dashboard",
      outletLabel: "dashboard page",
      element: <VerifiedSessionLayout />,
    });
    expect(await screen.findByText("login page")).toBeInTheDocument();
  });

  it("redirects verified members away from the setup route", async () => {
    mockedUseMembershipQuery.mockReturnValue(
      buildQueryState({ data: { household_id: "household-1" } }) as any
    );

    renderWithRoutes({
      initialEntry: "/household/setup",
      outletPath: "/household/setup",
      outletLabel: "household setup page",
      element: <HouseholdSetupLayout />,
    });
    expect(await screen.findByText("dashboard page")).toBeInTheDocument();
  });

  it("redirects non-members away from the dashboard route", async () => {
    mockedUseMembershipQuery.mockReturnValue(
      buildQueryState({ data: null }) as any
    );

    renderWithRoutes({
      initialEntry: "/dashboard",
      outletPath: "/dashboard",
      outletLabel: "dashboard page",
      element: <HouseholdRequiredLayout />,
    });
    expect(await screen.findByText("household setup page")).toBeInTheDocument();
  });

  it("keeps unverified users on the verification route", () => {
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn(),
      user: { emailVerified: false },
    } as never);

    renderWithRoutes({
      initialEntry: "/verify-email",
      outletPath: "/verify-email",
      outletLabel: "verify email page",
      element: <EmailVerificationLayout />,
    });
    expect(screen.getByText("verify email page")).toBeInTheDocument();
  });
});
