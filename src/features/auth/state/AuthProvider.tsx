import { useEffect, useReducer } from "react";
import { AuthState, AuthStateAction, initialAuthState } from "./AuthModels";
import { AuthContext } from "./AuthContext";
import {
  refreshAuthUser,
  subscribeToAuthChanges,
  // userHasSms2FA,
} from "../api/firebase/client";
import { User as FirebaseUser } from "firebase/auth";

function reducer(state: AuthState, action: AuthStateAction): AuthState {
  switch (action.type) {
    case "SET_STATE":
      console.log("auth state updated");
      return {
        ...state,
        ...action.state,
      };
    case "RESET":
      console.log("auth state reset");
      return initialAuthState;
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialAuthState);

  const syncWithfbUser = (fbUser: FirebaseUser | null) => {
    if (!fbUser) {
      dispatch({ type: "RESET" });
    } else {
      dispatch({
        type: "SET_STATE",
        state: {
          user: {
            firebase_uid: fbUser.uid,
            email: fbUser.email!,
            emailVerified: fbUser.emailVerified,
            hasSms2FA: false /* TODO: await userHasSms2FA() */,
          },
          isLoading: false,
          isAuthenticated: fbUser.emailVerified,
        },
      });
    }
  };

  const refresh = async () => {
    const fbUser = await refreshAuthUser();
    syncWithfbUser(fbUser);
  };

  useEffect(() => {
    dispatch({ type: "SET_STATE", state: { isLoading: true } });
    const unsubscribe = subscribeToAuthChanges(syncWithfbUser);
    dispatch({ type: "SET_STATE", state: { isLoading: false } });
    return unsubscribe;
  }, [dispatch]);

  return (
    <AuthContext.Provider value={{ ...state, dispatch, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
