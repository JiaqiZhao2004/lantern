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
import { auth } from "../../../../core/firebaseConfig";
import { AppError } from "../../../../core/appErrors";

// Auth state listener wrapper (just a tiny pass-through)
export function subscribeToAuthChanges(
  handler: (user: FirebaseUser | null) => void
) {
  return onAuthStateChanged(auth, handler);
}
function fbErrorToAppError(e: any): AppError {
  // console.log(JSON.stringify(e));
  const code = e?.code ?? "unknown";
  if (code === "auth/too-many-requests") {
    throw new AppError(
      "auth/too-many-requests",
      "Too many requests. Please try again later."
    );
  } else if (code === "auth/no-current-user") {
    throw new AppError(
      "auth/no-current-user",
      "This user does not exist. Have you registered yet?"
    );
  } else if (code === "auth/invalid-credential") {
    throw new AppError(
      "auth/invalid-credential",
      "The username or password is incorrect. Have you registered yet?"
    );
  } else if (code === "auth/multi-factor-auth-required") {
    throw new AppError(
      "auth/multi-factor-auth-required",
      "Move on to MFA verification."
    );
  } else {
    throw new AppError(
      "unknown",
      "An unknown error occurred while sending the verification email."
    );
  }
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

// export async function userHasSms2FA() {
//   const fbUser = auth.currentUser;
//   if (!fbUser) return false;

//   // Make sure data is fresh
//   await fbUser.reload();

//   const mfa = multiFactor(fbUser);
//   const enrolledFactors = mfa.enrolledFactors; // MultiFactorInfo[]

//   const hasSms2FA = enrolledFactors.some(
//     (factor) => factor.factorId === PhoneMultiFactorGenerator.FACTOR_ID
//   );

//   return hasSms2FA;
// }

// export async function enrollSMSMFA(phoneNumber: string): Promise<string> {
//   const recaptchaVerifier = new RecaptchaVerifier(auth, "recaptcha-container", {
//     size: "invisible",
//   });
//   recaptchaVerifier.render();

//   const multiFactorSession = await multiFactor(auth.currentUser!).getSession();
//   // Specify the phone number and pass the MFA session.
//   const phoneInfoOptions = {
//     phoneNumber: phoneNumber,
//     session: multiFactorSession,
//   };
//   // Send the phone
//   const phoneAuthProvider = new PhoneAuthProvider(auth);
//   while (true) {
//     try {
//       const verificationId = await phoneAuthProvider.verifyPhoneNumber(
//         phoneInfoOptions,
//         recaptchaVerifier
//       );
//       return verificationId;
//     } catch (e: any) {
//       console.log(JSON.stringify(e));
//       recaptchaVerifier.clear();
//     }
//   }
// }

// export async function verifySMSMFA(
//   verificationId: string,
//   verificationCode: string
// ) {
//   // Ask user for the verification code. Then:
//   const cred = PhoneAuthProvider.credential(verificationId, verificationCode);
//   const multiFactorAssertion = PhoneMultiFactorGenerator.assertion(cred);
//   await multiFactor(auth.currentUser!).enroll(
//     multiFactorAssertion,
//     "My personal phone number"
//   );
// }
