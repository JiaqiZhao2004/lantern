import { useCallback, useContext, useEffect } from "react";
import Header from "../../../Components/Header";
import PlaidLinkPage from "../../link/pages/PlaidLinkPage";
import { DashboardProvider } from "../state/DashboardProvider";
import { DashboardContext } from "../state/DashboardContext";
import { get_my_household, get_or_create_me } from "../api/backend/client";
import { AuthContext } from "../../auth/state/AuthContext";
import ConnectionsPanel from "./ConnectionsPanel";
import AccountsPanel from "./AccountsPanel";

export default function DashboardPage() {
  return (
    <DashboardProvider>
      <Content></Content>
    </DashboardProvider>
  );
}

function Content() {
  const { user, householdName, dispatch } = useContext(DashboardContext);
  const { isAuthenticated } = useContext(AuthContext);

  const loadDashboard = useCallback(async () => {
    if (!isAuthenticated) {
      return;
    }

    const [userResponse, householdResponse] = await Promise.all([
      get_or_create_me(),
      get_my_household(),
    ]);

    dispatch({
      type: "SET_STATE",
      state: {
        user: { email: userResponse.email, name: userResponse.name },
        householdName: householdResponse.name,
      },
    });
  }, [isAuthenticated, dispatch]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    console.log("user changed:", user);
  }, [user]);

  return (
    <div>
      <Header householdName={householdName} userEmail={user?.email}></Header>
      <PlaidLinkPage></PlaidLinkPage>
      <ConnectionsPanel></ConnectionsPanel>
      <AccountsPanel></AccountsPanel>
    </div>
  );
}
