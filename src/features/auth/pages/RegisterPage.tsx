import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { AuthPageLayout } from "@/features/auth/components/AuthPageLayout";
import formStyles from "@/features/auth/components/AuthForm.module.css";
import {
  registerWithEmail,
  sendVerificationEmail,
} from "@/features/auth/api/firebase/client";
import { useAuthSession } from "@/features/auth/session/AuthSessionProvider";
import { isAppError } from "@/shared/api/appError";
import { Button } from "@/shared/ui/Button/Button";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import { TextField } from "@/shared/ui/TextField/TextField";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { refresh } = useAuthSession();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password !== passwordConfirm) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await registerWithEmail(email.trim(), password);
      await sendVerificationEmail();
      await refresh();
    } catch (caughtError: unknown) {
      setError(
        isAppError(caughtError)
          ? caughtError.message
          : "Failed to register. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthPageLayout
      title="Create an account"
      description="Start with your email and password, then verify your address before entering the app."
      footer={
        <>
          Already have an account?{" "}
          <Link className={formStyles.footerLink} to="/login">
            Sign in
          </Link>
        </>
      }
    >
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}

      <form className={formStyles.form} onSubmit={handleSubmit}>
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
          required
        />

        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          required
        />

        <TextField
          label="Confirm password"
          type="password"
          value={passwordConfirm}
          onChange={setPasswordConfirm}
          autoComplete="new-password"
          required
        />

        <Button type="submit" disabled={isSubmitting} fullWidth>
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>
    </AuthPageLayout>
  );
}
