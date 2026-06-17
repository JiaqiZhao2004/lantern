import { FormEvent, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { useCreateHouseholdMutation } from "@/features/household/api/queries";
import styles from "@/features/household/pages/HouseholdSetupPage.module.css";
import {
  HOUSEHOLD_NAME_MAX_LENGTH,
  validateHouseholdName,
} from "@/features/household/utils/validation";
import { AppShell } from "@/shared/ui/AppShell/AppShell";
import { Button } from "@/shared/ui/Button/Button";
import { Card } from "@/shared/ui/Card/Card";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import { TextField } from "@/shared/ui/TextField/TextField";

export default function HouseholdSetupPage() {
  const navigate = useNavigate();
  const { logout, user } = useAuthSession();
  const createHouseholdMutation = useCreateHouseholdMutation();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [householdName, setHouseholdName] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const validationError = useMemo(
    () => validateHouseholdName(householdName),
    [householdName]
  );

  const isSubmitting = createHouseholdMutation.isPending;

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

  const handleCreateHousehold = async (event: FormEvent) => {
    event.preventDefault();
    setHasSubmitted(true);
    setSubmitError(null);

    if (validationError) {
      return;
    }

    try {
      await createHouseholdMutation.mutateAsync({ name: householdName.trim() });
      setIsModalOpen(false);
      setHouseholdName("");
      setHasSubmitted(false);
      navigate("/dashboard", { replace: true });
    } catch (caughtError: unknown) {
      setSubmitError(
        caughtError instanceof Error
          ? caughtError.message
          : "Failed to create household. Please try again."
      );
    }
  };

  return (
    <AppShell
      title="Set up your household"
      subtitle="Before entering the dashboard, create a household or get ready for a future invite-based join flow."
      email={user?.email}
      onLogout={logout}
    >
      <div className={styles.grid}>
        <Card>
          <div className={styles.stack}>
            <div>
              <h2 className={styles.cardTitle}>Create household</h2>
              <p className={styles.cardBody}>
                Start a new household and become the first member.
              </p>
            </div>
            <Button type="button" onClick={openModal}>
              Create household
            </Button>
          </div>
        </Card>

        <Card className={styles.mutedCard}>
          <div className={styles.stack}>
            <div>
              <h2 className={styles.cardTitle}>Join household</h2>
              <p className={styles.cardBody}>
                The backend join API is wrapped and ready, but the polished invite
                UX is intentionally deferred until there is something better than
                raw household IDs.
              </p>
            </div>
            <Button type="button" variant="secondary" disabled>
              Join household
            </Button>
          </div>
        </Card>
      </div>

      {isModalOpen ? (
        <div className={styles.overlay} role="dialog" aria-modal="true">
          <Card style={{ width: "100%", maxWidth: "28rem" }}>
            <div className={styles.stack}>
              <div>
                <h2 className={styles.cardTitle}>Create a household</h2>
                <p className={styles.cardBody}>
                  Choose a name using spaces, letters, numbers, or underscores.
                </p>
              </div>

              <form className={styles.form} onSubmit={handleCreateHousehold}>
                <TextField
                  label="Household name"
                  value={householdName}
                  onChange={setHouseholdName}
                  required
                  disabled={isSubmitting}
                  error={hasSubmitted ? validationError : null}
                  hint={`${householdName.length}/${HOUSEHOLD_NAME_MAX_LENGTH} characters`}
                />

                {submitError ? (
                  <InlineMessage tone="error">{submitError}</InlineMessage>
                ) : null}

                <Button
                  type="submit"
                  disabled={isSubmitting || validationError !== null}
                  fullWidth
                >
                  {isSubmitting ? "Creating household..." : "Create household"}
                </Button>
              </form>

              <p className={styles.caption}>
                Household join is intentionally hidden until the invite flow is more
                user-friendly.
              </p>

              <Button
                type="button"
                onClick={closeModal}
                disabled={isSubmitting}
                variant="secondary"
                fullWidth
              >
                Cancel
              </Button>
            </div>
          </Card>
        </div>
      ) : null}
    </AppShell>
  );
}
