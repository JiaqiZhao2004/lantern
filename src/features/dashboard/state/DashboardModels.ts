export type User = {
  email: string;
  name?: string | null;
};

export type DashboardState = {
  user: User | null;

  isLoading: boolean;
  errorCode?: string;
  errorMessage?: string;
};

export type DashboardStateAction =
  | {
      type: "SET_STATE";
      state?: Partial<DashboardState>;
    }
  | { type: "RESET" };

export const initialDashboardState: DashboardState = {
  user: null,
  isLoading: false,
};
