import React, { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import PrimaryButton from "../../../Components/PrimaryButton";
import TextInput from "../../../Components/TextInput";
import { create_household } from "../api/backend/client";
import {
  HOUSEHOLD_NAME_MAX_LENGTH,
  validateHouseholdName,
} from "../utils/validation";

export default function HouseholdSetupPage() {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [householdName, setHouseholdName] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const validationError = useMemo(
    () => validateHouseholdName(householdName),
    [householdName]
  );

  const closeModal = () => {
    if (isSubmitting) {
      return;
    }

    setIsModalOpen(false);
    setHouseholdName("");
    setSubmitError(null);
    setHasSubmitted(false);
  };

  const openModal = () => {
    setIsModalOpen(true);
    setSubmitError(null);
    setHasSubmitted(false);
  };

  const handleCreateHousehold = async (e: FormEvent) => {
    e.preventDefault();
    setHasSubmitted(true);
    setSubmitError(null);

    if (validationError) {
      return;
    }

    setIsSubmitting(true);

    try {
      await create_household({ name: householdName.trim() });
      setIsModalOpen(false);
      setHouseholdName("");
      setSubmitError(null);
      setHasSubmitted(false);
      navigate("/dashboard", { replace: true });
    } catch (error: any) {
      const message =
        error?.response?.data?.detail?.[0]?.msg ??
        error?.response?.data?.detail ??
        "Failed to create household. Please try again.";
      setSubmitError(String(message));
    } finally {
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
          maxWidth: "760px",
          padding: "2rem",
          borderRadius: "12px",
          backgroundColor: "#ffffff",
          boxShadow: "0 4px 18px rgba(0,0,0,0.08)",
        }}
      >
        <h1 style={{ marginTop: 0, marginBottom: "0.75rem" }}>
          Set up your household
        </h1>
        <p style={{ marginTop: 0, marginBottom: "1.5rem", color: "#555" }}>
          Before entering the dashboard, create a household or join an existing
          one.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "1rem",
          }}
        >
          <div
            style={{
              padding: "1.25rem",
              border: "1px solid #d6e4ff",
              borderRadius: "10px",
              backgroundColor: "#f7fbff",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Create household</h2>
            <p style={{ color: "#555", minHeight: "3rem" }}>
              Start a new household and become the first member.
            </p>
            <PrimaryButton type="button" onClick={openModal}>
              Create household
            </PrimaryButton>
          </div>

          <div
            style={{
              padding: "1.25rem",
              border: "1px solid #e0e0e0",
              borderRadius: "10px",
              backgroundColor: "#f0f0f0",
              opacity: 0.75,
            }}
          >
            <h2 style={{ marginTop: 0, color: "#666" }}>Join household</h2>
            <p style={{ color: "#666", minHeight: "3rem" }}>
              Join an existing household with an invite flow. Not yet
              implemented.
            </p>
            <PrimaryButton type="button" disabled>
              Join household
            </PrimaryButton>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.35)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "440px",
              backgroundColor: "#fff",
              borderRadius: "10px",
              padding: "1.5rem",
              boxShadow: "0 12px 28px rgba(0,0,0,0.18)",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "0.5rem" }}>
              Create a household
            </h2>
            <p style={{ marginTop: 0, color: "#555" }}>
              Choose a name using spaces, letters, numbers, or underscores.
            </p>

            <form onSubmit={handleCreateHousehold}>
              <TextInput
                label="Household name"
                value={householdName}
                onChange={setHouseholdName}
                required
                disabled={isSubmitting}
              />

              <p
                style={{
                  margin: "0.25rem 0 0.5rem",
                  fontSize: "0.85rem",
                  color: "#666",
                }}
              >
                {householdName.length}/{HOUSEHOLD_NAME_MAX_LENGTH} characters
              </p>

              {hasSubmitted && validationError && (
                <div
                  style={{
                    marginBottom: "0.75rem",
                    color: "#b00020",
                    fontSize: "0.9rem",
                  }}
                >
                  {validationError}
                </div>
              )}

              {submitError && (
                <div
                  style={{
                    marginBottom: "0.75rem",
                    color: "#b00020",
                    fontSize: "0.9rem",
                  }}
                >
                  {submitError}
                </div>
              )}

              <PrimaryButton
                type="submit"
                disabled={isSubmitting || validationError !== null}
              >
                {isSubmitting ? "Creating household..." : "Create household"}
              </PrimaryButton>
            </form>

            <button
              type="button"
              onClick={closeModal}
              disabled={isSubmitting}
              style={{
                width: "100%",
                marginTop: "0.75rem",
                padding: "0.6rem 0.8rem",
                borderRadius: "4px",
                border: "1px solid #ccc",
                backgroundColor: "#fff",
                cursor: isSubmitting ? "default" : "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
