export type User = {
  email: string;
  name?: string | null;
};

export type DashboardState = {
  user: User | null;
  householdName: string | null;
  linkedDataRefreshKey: number;

  isLoading: boolean;
  errorCode?: string;
  errorMessage?: string;
};

export type DashboardStateAction =
  | {
      type: "SET_STATE";
      state?: Partial<DashboardState>;
    }
  | { type: "REFRESH_LINKED_DATA" }
  | { type: "RESET" };

export const initialDashboardState: DashboardState = {
  user: null,
  householdName: null,
  linkedDataRefreshKey: 0,
  isLoading: false,
};
