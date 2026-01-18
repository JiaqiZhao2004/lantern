// src/features/auth/pages/LoginPage.tsx
import React, { useState, FormEvent } from "react";
// Components
import PrimaryButton from "../../../Components/PrimaryButton";
import TextInput from "../../../Components/TextInput";
// API calls
import { loginWithEmail } from "../auth.api";
import { isAppError } from "../../../app/apiErrors";

export default function LoginPage() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await loginWithEmail(email.trim(), password);
    } catch (e: any) {
      // if (isAppError(e) && e.code === "auth/multi-factor-auth-required")
      //   navigate("/mfa/verify");
      setError(
        isAppError(e) ? e.message : "Failed to sign in. Please try again."
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        backgroundColor: "#f5f5f5",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          padding: "1.5rem",
          borderRadius: "8px",
          backgroundColor: "#ffffff",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        <h1 style={{ margin: 0, marginBottom: "1.25rem", fontSize: "1.5rem" }}>
          Sign in
        </h1>

        {error && (
          <div
            style={{
              marginBottom: "0.75rem",
              padding: "0.5rem 0.75rem",
              borderRadius: "4px",
              backgroundColor: "#ffe5e5",
              color: "#b00020",
              fontSize: "0.875rem",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <TextInput
            label="Email"
            type="email"
            value={email}
            onChange={setEmail}
            autoComplete="email"
            required
          />

          <TextInput
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
            required
          />

          <PrimaryButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </PrimaryButton>
        </form>

        {/* Optional: small extras */}
        <div style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
          Don&apos;t have an account? <a href="/register">Register</a>
        </div>
      </div>
    </div>
  );
}
