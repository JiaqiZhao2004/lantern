import { useMemo, useState } from "react";
import { AuthPageLayout } from "@/features/auth/components/AuthPageLayout";
import formStyles from "@/features/auth/components/AuthForm.module.css";
import { sendVerificationEmail } from "@/features/auth/api/firebase/client";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { isAppError } from "@/shared/api/appError";
import { Button } from "@/shared/ui/Button/Button";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import { TextField } from "@/shared/ui/TextField/TextField";

export default function EmailVerificationPage() {
  const { logout, refresh, user } = useAuthSession();
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const email = useMemo(() => user?.email ?? "", [user?.email]);

  const handleResend = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    try {
      await sendVerificationEmail();
      setStatus("Verification email sent.");
    } catch (caughtError: unknown) {
      if (isAppError(caughtError)) {
        setError(
          caughtError.code === "auth/too-many-requests"
            ? "Verification email sent recently. Please wait a minute and try again."
            : caughtError.message
        );
      } else {
        setError("Unexpected error.");
      }
    } finally {
      setIsBusy(false);
    }
  };

  const handleCheckVerified = async () => {
    setIsBusy(true);
    setStatus("");
    setError("");

    const refreshedUser = await refresh();

    if (!refreshedUser?.emailVerified) {
      setStatus("Still not verified yet. Please click the link in your email.");
    }

    setIsBusy(false);
  };

  return (
    <AuthPageLayout
      title="Verify your email"
      description="Open the verification link from your inbox, then come back here to continue into the app."
      footer={
        <button
          className={formStyles.footerLink}
          type="button"
          onClick={() => void logout()}
        >
          Back to login
        </button>
      }
    >
      <TextField
        label="Email"
        type="email"
        value={email}
        onChange={() => undefined}
        autoComplete="email"
        readOnly
      />

      {status ? <InlineMessage tone="success">{status}</InlineMessage> : null}
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}

      <div className={formStyles.actions}>
        <Button onClick={handleResend} disabled={isBusy} variant="secondary" fullWidth>
          {isBusy ? "Working..." : "Send verification email"}
        </Button>

        <Button onClick={handleCheckVerified} disabled={isBusy} fullWidth>
          {isBusy ? "Working..." : "I have verified my email"}
        </Button>
      </div>
    </AuthPageLayout>
  );
}
