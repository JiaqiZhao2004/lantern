import { createContext } from "react";
import { AuthStateAction, AuthState, initialAuthState } from "./AuthModels";

interface IAuthContext extends AuthState {
  dispatch: React.Dispatch<AuthStateAction>;
  refresh: Function;
}

export const AuthContext = createContext<IAuthContext>(
  initialAuthState as IAuthContext
);
