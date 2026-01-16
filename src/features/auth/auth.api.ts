import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  User,
  multiFactor,
  PhoneAuthProvider,
  RecaptchaVerifier,
  PhoneMultiFactorGenerator,
} from "firebase/auth";
import { auth } from "./firebase";

export async function registerWithEmail(
  email: string,
  password: string
): Promise<User> {
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  return cred.user;
}

export async function loginWithEmail(
  email: string,
  password: string
): Promise<User> {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

export async function logoutFirebase(): Promise<void> {
  await signOut(auth);
}

export async function enrollSmsMfa(phoneE164: string) {
  const user = auth.currentUser;
  if (!user) throw new Error("Not signed in");

  // Ensure a div with id="recaptcha-container" exists in the page.
  const recaptchaVerifier = new RecaptchaVerifier(auth, "recaptcha-container", {
    size: "invisible",
  });

  // Start MFA enrollment session
  const mfaSession = await multiFactor(user).getSession();

  const phoneInfoOptions = {
    phoneNumber: phoneE164, // e.g. "+14155552671"
    session: mfaSession,
  };

  const phoneAuthProvider = new PhoneAuthProvider(auth);
  const verificationId = await phoneAuthProvider.verifyPhoneNumber(
    phoneInfoOptions,
    recaptchaVerifier
  );

  const code = window.prompt("Enter the SMS code");
  if (!code) throw new Error("No code entered");

  const cred = PhoneAuthProvider.credential(verificationId, code);
  const assertion = PhoneMultiFactorGenerator.assertion(cred);

  await multiFactor(user).enroll(assertion, "Phone");
}
