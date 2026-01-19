import { useReducer } from "react";
import {
  DashboardState,
  DashboardStateAction,
  initialDashboardState,
} from "./DashboardModels";
import { DashboardContext } from "./DashboardContext";

function reducer(
  state: DashboardState,
  action: DashboardStateAction
): DashboardState {
  switch (action.type) {
    case "SET_STATE":
      console.log("Dashboard state updated");
      return {
        ...state,
        ...action.state,
      };
    case "RESET":
      console.log("Dashboard state reset");
      return initialDashboardState;
    default:
      return state;
  }
}

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialDashboardState);

  return (
    <DashboardContext.Provider value={{ state, dispatch }}>
      {children}
    </DashboardContext.Provider>
  );
}
