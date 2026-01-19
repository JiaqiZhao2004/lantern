import { createContext } from "react";
import {
  DashboardStateAction,
  DashboardState,
  initialDashboardState,
} from "./DashboardModels";

interface IDashboardContext extends DashboardState {
  dispatch: React.Dispatch<DashboardStateAction>;
}

export const DashboardContext = createContext<IDashboardContext>(
  initialDashboardState as IDashboardContext
);
