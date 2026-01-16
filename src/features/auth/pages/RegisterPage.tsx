// src/features/auth/pages/RegisterPage.tsx
import React, { useState, FormEvent, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../AuthContext";
// Components
import TextInput from "../../../Components/TextInput";
import PrimaryButton from "../../../Components/PrimaryButton";
// API
import { registerWithEmail } from "../auth.api"; // adjust path if needed
import { isAppError } from "../../../app/apiErrors";

export default function RegisterPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ctx = useContext(AuthContext);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== passwordConfirm) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await registerWithEmail(email.trim(), password);
      await ctx?.refresh();
      console.log("Registered with email and password");
      navigate("/verify-email", { replace: true });
    } catch (err: any) {
      const message = isAppError(err)
        ? err.message
        : "Failed to register. Please try again.";
      setError(message);
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
          Create an account
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
            autoComplete="new-password"
            required
          />

          <TextInput
            label="Confirm Password"
            type="password"
            value={passwordConfirm}
            onChange={setPasswordConfirm}
            autoComplete="new-password"
            required
          />

          <PrimaryButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Register"}
          </PrimaryButton>
        </form>

        <div
          style={{
            marginTop: "0.75rem",
            fontSize: "0.85rem",
            textAlign: "center",
          }}
        >
          Already have an account?{" "}
          <Link to="/login" style={{ color: "#1976d2" }}>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
