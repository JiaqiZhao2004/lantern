import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "@/features/auth/pages/LoginPage";
import {
  loginWithEmail,
  loginWithGoogle,
} from "@/features/auth/api/firebase/client";
import { AppError } from "@/shared/api/appError";

vi.mock("@/features/auth/api/firebase/client", () => ({
  loginWithEmail: vi.fn(),
  loginWithGoogle: vi.fn(),
}));

const mockedLoginWithEmail = vi.mocked(loginWithEmail);
const mockedLoginWithGoogle = vi.mocked(loginWithGoogle);

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedLoginWithEmail.mockResolvedValue(undefined);
    mockedLoginWithGoogle.mockResolvedValue(undefined);
  });

  it("renders the Google sign-in option", () => {
    renderLoginPage();

    expect(
      screen.getByRole("button", { name: "Continue with Google" })
    ).toBeInTheDocument();
  });

  it("signs in with Google when the provider button is clicked", async () => {
    renderLoginPage();

    fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    await waitFor(() => {
      expect(mockedLoginWithGoogle).toHaveBeenCalledTimes(1);
    });
  });

  it("shows provider errors", async () => {
    mockedLoginWithGoogle.mockRejectedValue(
      new AppError("unknown", "Google sign-in was cancelled.")
    );
    renderLoginPage();

    fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    expect(
      await screen.findByText("Google sign-in was cancelled.")
    ).toBeInTheDocument();
  });

  it("keeps the email-password sign-in flow", async () => {
    renderLoginPage();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "correct-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockedLoginWithEmail).toHaveBeenCalledWith(
        "user@example.com",
        "correct-password"
      );
    });
  });
});
