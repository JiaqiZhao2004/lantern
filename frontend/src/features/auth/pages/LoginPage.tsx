import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { AuthPageLayout } from "@/features/auth/components/AuthPageLayout";
import formStyles from "@/features/auth/components/AuthForm.module.css";
import { RestrictedAccessPanel } from "@/features/auth/components/RestrictedAccessPanel";
import { isRestrictedAuthMode } from "@/features/auth/config/access";
import { SocialAuthOptions } from "@/features/auth/components/SocialAuthOptions";
import { loginWithEmail } from "@/features/auth/api/firebase/client";
import { isAppError } from "@/shared/api/appError";
import { Button } from "@/shared/ui/Button/Button";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import { TextField } from "@/shared/ui/TextField/TextField";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isProviderSubmitting, setIsProviderSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await loginWithEmail(email.trim(), password);
    } catch (caughtError: unknown) {
      setError(
        isAppError(caughtError)
          ? caughtError.message
          : "Failed to sign in. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthPageLayout
      title="Sign in"
      description={
        isRestrictedAuthMode
          ? "This production Lantern deployment is limited to approved email addresses."
          : "Use your Lantern account to get back to your dashboard."
      }
      footer={
        isRestrictedAuthMode ? (
          "Need access? Contact the site owner to be added to the allowlist."
        ) : (
          <>
            Don&apos;t have an account?{" "}
            <Link className={formStyles.footerLink} to="/register">
              Register
            </Link>
          </>
        )
      }
    >
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}

      {isRestrictedAuthMode ? (
        <RestrictedAccessPanel showSignInHint />
      ) : null}

      <SocialAuthOptions
        disabled={isSubmitting || isProviderSubmitting}
        onBusyChange={setIsProviderSubmitting}
        onError={setError}
      />

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
          autoComplete="current-password"
          required
        />

        <Button
          type="submit"
          disabled={isSubmitting || isProviderSubmitting}
          fullWidth
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </AuthPageLayout>
  );
}
