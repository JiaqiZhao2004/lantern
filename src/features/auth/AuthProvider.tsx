import { useEffect, useState } from "react";
import { AuthState, User } from "./auth.types";
import { getCurrentUser } from "./auth.api";
import { AuthContext } from "./AuthContext";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });
  useEffect(() => {
    getCurrentUser()
      .then((user: User | null) => {
        setState({
          user,
          isAuthenticated: !!user,
          isLoading: false,
        });
      })
      .catch(() =>
        setState({ user: null, isAuthenticated: false, isLoading: false })
      );
  }, []);

  return <AuthContext.Provider value={state}>{children}</AuthContext.Provider>;
}
