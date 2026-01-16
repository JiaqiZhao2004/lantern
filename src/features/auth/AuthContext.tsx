import { createContext, useContext } from "react";
import { AuthStateAction, AuthState } from "./auth.types";

export const AuthContext = createContext<{
  state: AuthState;
  dispatch: React.Dispatch<AuthStateAction>;
} | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx.state;
}
