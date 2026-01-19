export type User = {
  firebase_uid: string;
  email: string;
  emailVerified: boolean;
  hasSms2FA: boolean;
};

export type AuthState = {
  user: User | null;
  isAuthenticated: boolean;

  isLoading: boolean;
  errorCode?: string;
  errorMessage?: string;
};

export type AuthStateAction =
  | {
      type: "SET_STATE";
      state?: Partial<AuthState>;
    }
  | { type: "RESET" };

export const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
};
