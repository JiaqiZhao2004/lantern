import { createContext, useContext } from "react";
import { DashboardStateAction, DashboardState } from "./DashboardModels";

export const DashboardContext = createContext<{
  state: DashboardState;
  dispatch: React.Dispatch<DashboardStateAction>;
} | null>(null);

export function useDashboard(): DashboardState {
  const ctx = useContext(DashboardContext);
  if (!ctx) {
    throw new Error("useDashboard must be used within DashboardProvider");
  }
  return ctx.state;
}
