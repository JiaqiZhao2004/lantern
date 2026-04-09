import { User as FirebaseUser } from "firebase/auth";
import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { logoutFirebase, refreshAuthUser } from "@/features/auth/api/firebase/client";
import { subscribeToAuthChanges } from "@/features/auth/api/firebase/client";

type AuthSessionValue = {
  user: FirebaseUser | null;
  isLoading: boolean;
  refresh: () => Promise<FirebaseUser | null>;
  logout: () => Promise<void>;
};

const AuthSessionContext = createContext<AuthSessionValue | undefined>(undefined);

type AuthSessionProviderProps = {
  children: ReactNode;
};

export function AuthSessionProvider({ children }: AuthSessionProviderProps) {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((nextUser) => {
      setUser(nextUser);
      setIsLoading(false);
    });

    return unsubscribe;
  }, []);

  const refresh = async () => {
    const refreshedUser = await refreshAuthUser();
    setUser(refreshedUser);
    return refreshedUser;
  };

  const value = useMemo<AuthSessionValue>(
    () => ({
      user,
      isLoading,
      refresh,
      logout: logoutFirebase,
    }),
    [isLoading, user]
  );

  return (
    <AuthSessionContext.Provider value={value}>
      {children}
    </AuthSessionContext.Provider>
  );
}

export function useAuthSession() {
  const context = useContext(AuthSessionContext);

  if (!context) {
    throw new Error("useAuthSession must be used within AuthSessionProvider.");
  }

  return context;
}
