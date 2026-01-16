import React, { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { reload, sendEmailVerification } from "firebase/auth";

import { AuthContext } from "../AuthContext";
import { auth } from "../firebase";
import TextInput from "../../../Components/TextInput";
import PrimaryButton from "../../../Components/PrimaryButton";

export default function EmailVerificationPage() {
  const navigate = useNavigate();
  const ctx = useContext(AuthContext);

  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState(false);

  const email = useMemo(() => ctx?.state.user?.email ?? "", [ctx]);

  // Redirects must happen in an effect (not during render).
  useEffect(() => {
    if (!ctx) return;

    if (!ctx.state.user) {
      navigate("/login", { replace: true });
      return;
    }

    if (ctx.state.user.emailVerified) {
      navigate("/2fa", { replace: true });
      return;
    }
  }, [ctx, navigate]);

  const refreshUserInContext = async () => {
    const fbUser = auth.currentUser;
    if (!fbUser) {
      ctx?.dispatch({
        type: "SET_STATE",
        payload: {
          user: null,
          isAuthenticated: false,
          isLoading: false,
          errorCode: "auth/no-current-user",
          errorMessage: "Please log in again.",
        },
      });
      navigate("/login", { replace: true });
      return null;
    }

    await reload(fbUser);

    ctx?.dispatch({
      type: "SET_STATE",
      payload: {
        user: {
          firebase_uid: fbUser.uid,
          email: fbUser.email!,
          emailVerified: fbUser.emailVerified,
        },
      },
    });

    return fbUser;
  };

  const handleCheckVerified = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    try {
      const fbUser = await refreshUserInContext();
      if (!fbUser) return;

      if (fbUser.emailVerified) {
        navigate("/2fa", { replace: true });
      } else {
        setStatus(
          "Still not verified yet. Click the link in your email, then try again."
        );
      }
    } catch (e) {
      console.error(e);
      setError("Failed to refresh verification status. Please try again.");
    } finally {
      setIsBusy(false);
    }
  };

  const handleResend = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    try {
      const fbUser = auth.currentUser;
      if (!fbUser) {
        navigate("/login", { replace: true });
        return;
      }

      await sendEmailVerification(fbUser);
      setStatus("Verification email sent. Please check your inbox.");
    } catch (e) {
      console.error(e);
      setError("Failed to send verification email. Please try again.");
    } finally {
      setIsBusy(false);
    }
  };

  // While redirect effect runs, keep UI stable.
  if (!ctx || !ctx.state.user) return null;

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
          We sent a verification link to your email. Click the link, then come
          back and press “I have verified my email”.
        </p>

        {/* Using TextInput as a read-only display of the email */}
        <TextInput
          label="Email"
          type="email"
          value={email}
          onChange={() => {
            // no-op (read-only display)
          }}
          autoComplete="email"
          required
        />
        <div style={{ marginTop: "-0.5rem", marginBottom: "0.75rem" }}>
          <small style={{ color: "#777" }}>
            (This field is read-only on this page.)
          </small>
        </div>

        {status && (
          <p style={{ margin: "0.75rem 0 0", color: "#1976d2" }}>{status}</p>
        )}
        {error && (
          <p style={{ margin: "0.75rem 0 0", color: "#d32f2f" }}>{error}</p>
        )}

        <PrimaryButton onClick={handleCheckVerified} disabled={isBusy}>
          {isBusy ? "Working..." : "I have verified my email"}
        </PrimaryButton>

        <PrimaryButton
          onClick={handleResend}
          disabled={isBusy}
          style={{ marginTop: "0.5rem", backgroundColor: "#455a64" }}
        >
          {isBusy ? "Working..." : "Resend verification email"}
        </PrimaryButton>

        <button
          type="button"
          onClick={() => navigate("/login", { replace: true })}
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
