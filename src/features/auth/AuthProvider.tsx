import { useReducer } from "react";
import { AuthState, AuthStateAction, initialAuthState } from "./auth.types";
import { AuthContext } from "./AuthContext";

function reducer(state: AuthState, action: AuthStateAction): AuthState {
  switch (action.type) {
    case "SET_STATE":
      return {
        ...state,
        ...action.payload,
      };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialAuthState);

  return (
    <AuthContext.Provider value={{ state, dispatch }}>
      {children}
    </AuthContext.Provider>
  );
}
