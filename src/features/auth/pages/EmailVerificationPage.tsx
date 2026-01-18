import React, { useContext, useMemo, useState } from "react";
import { isAppError } from "../../../app/apiErrors";
import { AuthContext } from "../AuthContext";
// Components
import PrimaryButton from "../../../Components/PrimaryButton";
import TextInput from "../../../Components/TextInput";
// API calls
import { logoutFirebase, sendVerificationEmail } from "../auth.api";

export default function EmailVerificationPage() {
  const ctx = useContext(AuthContext);

  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState(false);

  const email = useMemo(() => ctx?.state.user?.email ?? "", [ctx]);

  const handleResend = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    try {
      await sendVerificationEmail();
      console.log("Email sent");
      setStatus("Verification email sent");
    } catch (e) {
      if (isAppError(e)) {
        if (e.code === "auth/too-many-requests")
          setError("Verification email sent. Please try again in a minute.");
        else setError(e.message);
      } else {
        setError("Unexpected error.");
      }
    }
    setIsBusy(false);
  };

  const handleCheckVerified = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    await ctx?.refresh();

    if (!ctx?.state.user?.emailVerified) {
      setStatus(
        "Still not verified yet. Please click the link in your email."
      );
    }
    setIsBusy(false);
  };

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
          backgroundColor: "#fff",
          borderRadius: 8,
          border: "1px solid #e0e0e0",
          boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: "0.75rem" }}>
          Verify your email
        </h2>

        <p style={{ marginTop: 0, marginBottom: "0.75rem", color: "#444" }}>
          We sent a verification link to your email. The email may be in your
          junk folder. Click the link, then come back and press “I have verified
          my email”.
        </p>

        <TextInput
          label="Email"
          type="email"
          value={email}
          onChange={() => {
            // no-op (read-only display)
          }}
          autoComplete="email"
          disabled={true}
          required
        />

        {status && (
          <p style={{ margin: "0.75rem 0 0", color: "#1976d2" }}>{status}</p>
        )}
        {error && (
          <p style={{ margin: "0.75rem 0 0", color: "#d32f2f" }}>{error}</p>
        )}

        <PrimaryButton
          onClick={handleResend}
          disabled={isBusy}
          style={{ marginTop: "0.5rem", backgroundColor: "#455a64" }}
        >
          {isBusy ? "Working..." : "Send verification email"}
        </PrimaryButton>

        <PrimaryButton onClick={handleCheckVerified} disabled={isBusy}>
          {isBusy ? "Working..." : "I have verified my email"}
        </PrimaryButton>

        <button
          type="button"
          onClick={() => logoutFirebase()}
          style={{
            width: "100%",
            marginTop: "0.75rem",
            border: "none",
            background: "none",
            color: "#1976d2",
            textDecoration: "underline",
            cursor: "pointer",
          }}
        >
          Back to login
        </button>
      </div>
    </div>
  );
}
