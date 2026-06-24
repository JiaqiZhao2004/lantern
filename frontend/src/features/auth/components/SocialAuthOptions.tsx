import { loginWithGoogle } from "@/features/auth/api/firebase/client";
import formStyles from "@/features/auth/components/AuthForm.module.css";
import { isAppError } from "@/shared/api/appError";
import { Button } from "@/shared/ui/Button/Button";

type SocialAuthOptionsProps = {
  disabled?: boolean;
  onBusyChange: (isBusy: boolean) => void;
  onError: (message: string | null) => void;
};

export function SocialAuthOptions({
  disabled = false,
  onBusyChange,
  onError,
}: SocialAuthOptionsProps) {
  const handleGoogleSignIn = async () => {
    onError(null);
    onBusyChange(true);

    try {
      await loginWithGoogle();
    } catch (caughtError: unknown) {
      onError(
        isAppError(caughtError)
          ? caughtError.message
          : "Failed to sign in with Google. Please try again."
      );
    } finally {
      onBusyChange(false);
    }
  };

  return (
    <div className={formStyles.socialOptions}>
      <Button
        type="button"
        variant="secondary"
        fullWidth
        disabled={disabled}
        onClick={handleGoogleSignIn}
      >
        Continue with Google
      </Button>

      <div className={formStyles.divider}>
        <span>or continue with email</span>
      </div>
    </div>
  );
}
