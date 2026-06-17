import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  User as FirebaseUser,
  // multiFactor,
  // PhoneAuthProvider,
  // RecaptchaVerifier,
  // PhoneMultiFactorGenerator,
  sendEmailVerification,
  onAuthStateChanged,
} from "firebase/auth";
import { auth } from "@/features/auth/api/firebase/firebaseApp";
import { AppError } from "@/shared/api/appError";

// Auth state listener wrapper (just a tiny pass-through)
export function subscribeToAuthChanges(
  handler: (user: FirebaseUser | null) => void
) {
  return onAuthStateChanged(auth, handler);
}
function fbErrorToAppError(e: any): AppError {
  const code = e?.code ?? "unknown";

  if (code === "auth/email-already-in-use") {
    return new AppError(
      "unknown",
      "An account already exists for this email address."
    );
  }

  if (code === "auth/weak-password") {
    return new AppError(
      "unknown",
      "Choose a stronger password and try again."
    );
  }

  if (code === "auth/invalid-email") {
    return new AppError("unknown", "Enter a valid email address.");
  }

  if (code === "auth/too-many-requests") {
    return new AppError(
      "auth/too-many-requests",
      "Too many requests. Please try again later."
    );
  }

  if (code === "auth/no-current-user") {
    return new AppError(
      "auth/no-current-user",
      "This user does not exist. Have you registered yet?"
    );
  }

  if (code === "auth/invalid-credential") {
    return new AppError(
      "auth/invalid-credential",
      "The username or password is incorrect. Have you registered yet?"
    );
  }

  if (code === "auth/multi-factor-auth-required") {
    return new AppError(
      "auth/multi-factor-auth-required",
      "Move on to MFA verification."
    );
  }

  return new AppError(
    "unknown",
    "An unknown error occurred while sending the verification email."
  );
}

export async function registerWithEmail(email: string, password: string) {
  try {
    await createUserWithEmailAndPassword(auth, email, password);
  } catch (e: any) {
    throw fbErrorToAppError(e);
  }
}

export async function loginWithEmail(email: string, password: string) {
  try {
    await signInWithEmailAndPassword(auth, email, password);
  } catch (e: any) {
    throw fbErrorToAppError(e);
  }
}

export async function logoutFirebase() {
  await signOut(auth);
}

export async function refreshAuthUser() {
  const fbUser = auth.currentUser;
  if (!fbUser) return null;
  await fbUser.reload();
  return fbUser;
}

export async function sendVerificationEmail() {
  const fbUser = auth.currentUser;
  if (!fbUser)
    throw new AppError(
      "auth/no-current-user",
      "No user is currently signed in."
    );
  try {
    await sendEmailVerification(fbUser);
  } catch (e: any) {
    throw fbErrorToAppError(e);
  }
}
