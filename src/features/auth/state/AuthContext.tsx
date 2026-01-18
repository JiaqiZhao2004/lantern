import { createContext, useContext } from "react";
import { AuthStateAction, AuthState } from "./AuthModels";

export const AuthContext = createContext<{
  state: AuthState;
  dispatch: React.Dispatch<AuthStateAction>;
  refresh: Function;
} | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx.state;
}
