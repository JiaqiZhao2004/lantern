import { useEffect, useReducer } from "react";
import { AuthState, AuthStateAction, initialAuthState } from "./auth.types";
import { AuthContext } from "./AuthContext";
import {
  refreshAuthUser,
  subscribeToAuthChanges,
  userHasSms2FA,
} from "./auth.api";
import { User as FirebaseUser } from "firebase/auth";

function reducer(state: AuthState, action: AuthStateAction): AuthState {
  switch (action.type) {
    case "SET_STATE":
      return {
        ...state,
        ...action.payload,
      };
    case "RESET":
      return initialAuthState;
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialAuthState);

  const syncWithfbUser = async (fbUser: FirebaseUser | null) => {
    if (!fbUser) {
      dispatch({ type: "RESET" });
    } else {
      await fbUser.reload();
      dispatch({
        type: "SET_STATE",
        payload: {
          user: {
            firebase_uid: fbUser.uid,
            email: fbUser.email!,
            emailVerified: fbUser.emailVerified,
            hasSms2FA: await userHasSms2FA(),
          },
          isLoading: false,
        },
      });
    }
  };

  const refresh = async () => {
    const fbUser = await refreshAuthUser();
    await syncWithfbUser(fbUser);
  };

  useEffect(() => {
    dispatch({ type: "SET_STATE", payload: { isLoading: true } });
    const unsubscribe = subscribeToAuthChanges(syncWithfbUser);
    return unsubscribe;
  }, []);

  return (
    <AuthContext.Provider value={{ state, dispatch, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
