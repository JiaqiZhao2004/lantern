import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RegisterPage from "@/features/auth/pages/RegisterPage";
import {
  loginWithGoogle,
  registerWithEmail,
  sendVerificationEmail,
} from "@/features/auth/api/firebase/client";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { AppError } from "@/shared/api/appError";

vi.mock("@/features/auth/api/firebase/client", () => ({
  loginWithGoogle: vi.fn(),
  registerWithEmail: vi.fn(),
  sendVerificationEmail: vi.fn(),
}));

vi.mock("@/features/auth/session/AuthSessionProvider", () => ({
  useAuthSession: vi.fn(),
}));

const mockedLoginWithGoogle = vi.mocked(loginWithGoogle);
const mockedRegisterWithEmail = vi.mocked(registerWithEmail);
const mockedSendVerificationEmail = vi.mocked(sendVerificationEmail);
const mockedUseAuthSession = vi.mocked(useAuthSession);

function renderRegisterPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>
  );
}

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedLoginWithGoogle.mockResolvedValue(undefined);
    mockedRegisterWithEmail.mockResolvedValue(undefined);
    mockedSendVerificationEmail.mockResolvedValue(undefined);
    mockedUseAuthSession.mockReturnValue({
      isLoading: false,
      logout: vi.fn(),
      refresh: vi.fn().mockResolvedValue(null),
      user: null,
    });
  });

  it("renders the Google sign-in option", () => {
    renderRegisterPage();

    expect(
      screen.getByRole("button", { name: "Continue with Google" })
    ).toBeInTheDocument();
  });

  it("signs in with Google when the provider button is clicked", async () => {
    renderRegisterPage();

    fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    await waitFor(() => {
      expect(mockedLoginWithGoogle).toHaveBeenCalledTimes(1);
    });
  });

  it("shows provider errors", async () => {
    mockedLoginWithGoogle.mockRejectedValue(
      new AppError(
        "auth/invalid-credential",
        "An account already exists for this email."
      )
    );
    renderRegisterPage();

    fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    expect(
      await screen.findByText("An account already exists for this email.")
    ).toBeInTheDocument();
  });

  it("keeps the email-password registration flow", async () => {
    renderRegisterPage();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "new-user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "correct-password" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(mockedRegisterWithEmail).toHaveBeenCalledWith(
        "new-user@example.com",
        "correct-password"
      );
    });
    expect(mockedSendVerificationEmail).toHaveBeenCalledTimes(1);
  });
});
