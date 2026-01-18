import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../AuthContext";
// Components
import TextInput from "../../../Components/TextInput";
import PrimaryButton from "../../../Components/PrimaryButton";
// API
import { enrollSMSMFA, userHasSms2FA, verifySMSMFA } from "../auth.api";
import { isAppError } from "../../../app/apiErrors";

export default function MFASetupPage() {
  const ctx = useContext(AuthContext);
  const navigate = useNavigate();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationId, setVerificationId] = useState<string | null>(null);
  const [isCheckingExisting, setIsCheckingExisting] = useState(true);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  // Route guards + check if SMS MFA already exists
  useEffect(() => {
    console.log(ctx);

    if (!ctx || ctx.state.isLoading) return;

    // If not logged in → go to login
    if (!ctx.state.user) {
      navigate("/login", { replace: true });
      return;
    }

    // If email not verified → go to email verify first
    if (!ctx.state.user.emailVerified) {
      navigate("/verify-email", { replace: true });
      return;
    }

    let cancelled = false;

    const checkExistingMfa = async () => {
      try {
        const hasSms2FA = await userHasSms2FA();
        if (!cancelled && hasSms2FA) {
          navigate("/mfa/verify", { replace: true });
          return;
        }
      } catch (e) {
        console.error(e);
        // Non-fatal: user can still attempt enrollment
      } finally {
        if (!cancelled) {
          setIsCheckingExisting(false);
        }
      }
    };

    checkExistingMfa();

    return () => {
      cancelled = true;
    };
  }, [ctx, navigate]);

  const handleSendCode = async (e: React.MouseEvent) => {
    setError(null);
    setStatus(null);

    // Simple guard; you can add more validation if you like
    if (!phoneNumber.trim()) {
      setError("Please enter a phone number.");
      return;
    }

    setIsSendingCode(true);

    try {
      // Make phoneNumber E.164 formatted: +14155552671 by adding '+'
      setVerificationId(await enrollSMSMFA("+" + phoneNumber.replace(" ", "")));
      console.log("verificationId: ", verificationId);
    } catch (e: any) {
      setError(
        isAppError(e)
          ? e.message
          : "Failed to enroll SMS 2FA. Please check the number and try again."
      );
    } finally {
      setIsSendingCode(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus(null);

    // Simple guard; you can add more validation if you like
    if (!phoneNumber.trim()) {
      setError("Please enter a phone number.");
      return;
    }

    setIsSubmitting(true);

    try {
      // Make phoneNumber E.164 formatted: +14155552671 by adding '+'
      verifySMSMFA(verificationId!, verificationCode.trim());

      if (!verificationId) {
        setError(
          "Failed to send SMS code, please check your internet connection"
        );
      }
      setStatus("SMS 2FA has been set up. Redirecting...");
      navigate("/dashboard", { replace: true });
    } catch (e: any) {
      setError(
        isAppError(e)
          ? e.message
          : "Failed to enroll SMS 2FA. Please check the number and try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // While we are deciding where to send the user, don't flash the form
  if (!ctx || !ctx.state.user || isCheckingExisting) {
    return null;
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#f5f5f5",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          padding: "1.6rem",
          backgroundColor: "#ffffff",
          borderRadius: 8,
          border: "1px solid #e0e0e0",
          boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: "0.75rem" }}>
          Set up SMS 2FA
        </h2>
        <p style={{ marginTop: 0, marginBottom: "0.75rem", color: "#444" }}>
          Add a phone number to receive verification codes. (e.g.{" "}
          <code>14155552671</code>).
        </p>

        <form onSubmit={handleSubmit}>
          <TextInput
            label="Phone number"
            type="tel"
            value={phoneNumber}
            onChange={setPhoneNumber}
            autoComplete="tel"
            required
          />

          {/* reCAPTCHA container for Firebase phone auth */}
          <div
            id="recaptcha-container"
            style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}
          ></div>

          <TextInput
            label="Code"
            value={verificationCode}
            onChange={setVerificationCode}
            autoComplete="tel"
          />

          <button
            id="get-code-button"
            type="button"
            onClick={handleSendCode}
            disabled={isSendingCode}
          >
            Send Code
          </button>

          {status && (
            <p style={{ marginTop: "0.5rem", color: "#1976d2" }}>{status}</p>
          )}
          {error && (
            <p style={{ marginTop: "0.5rem", color: "#d32f2f" }}>{error}</p>
          )}

          <PrimaryButton
            type="submit"
            disabled={isSubmitting || !verificationCode || !verificationCode}
          >
            {isSubmitting ? "Setting up..." : "Set up SMS 2FA"}
          </PrimaryButton>
        </form>
      </div>
    </div>
  );
}
