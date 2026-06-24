import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithEmailAndPassword,
  signInWithPopup,
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

const googleProvider = new GoogleAuthProvider();

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

  if (code === "auth/account-exists-with-different-credential") {
    return new AppError(
      "auth/invalid-credential",
      "An account already exists for this email. Sign in with your existing method."
    );
  }

  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") {
    return new AppError(
      "unknown",
      "Google sign-in was cancelled. You can try again when you are ready."
    );
  }

  if (code === "auth/popup-blocked") {
    return new AppError(
      "unknown",
      "Your browser blocked the Google sign-in popup. Allow popups for this site and try again."
    );
  }

  if (code === "auth/network-request-failed") {
    return new AppError(
      "network/offline",
      "Unable to reach Google sign-in. Check your connection and try again."
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

export async function loginWithGoogle() {
  try {
    await signInWithPopup(auth, googleProvider);
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
