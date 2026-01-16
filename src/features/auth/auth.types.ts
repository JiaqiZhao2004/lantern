export type PhoneNumber = {
  countryCode: number;
  number: number;
};

export type User = {
  firebase_uid: string;
  email: string;
  emailVerified: boolean;
};

export type AuthState = {
  user: User | null;
  isAuthenticated: boolean;

  isLoading: boolean;
  errorCode?: string;
  errorMessage?: string;
};

export type AuthStateAction = {
  type: "SET_STATE";
  payload?: Partial<AuthState>;
};

export const initialAuthState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
};
