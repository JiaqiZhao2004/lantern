import { useCallback, useContext, useEffect } from "react";
import Header from "../../../Components/Header";
import PlaidLinkPage from "../../link/pages/PlaidLinkPage";
import { DashboardProvider } from "../state/DashboardProvider";
import { DashboardContext } from "../state/DashboardContext";
import { get_or_create_me } from "../api/backend/client";
import { AuthContext } from "../../auth/state/AuthContext";
import ConnectionsPanel from "./ConnectionsPanel";

export default function DashboardPage() {
  return (
    <DashboardProvider>
      <Content></Content>
    </DashboardProvider>
  );
}

function Content() {
  const { user, dispatch } = useContext(DashboardContext);
  const { isAuthenticated } = useContext(AuthContext);

  const getOrCreateMe = useCallback(async () => {
    if (!isAuthenticated) {
      return;
    }
    const data = await get_or_create_me();
    dispatch({
      type: "SET_STATE",
      state: {
        user: { email: data.email, name: data.name },
      },
    });
  }, [isAuthenticated, dispatch]);

  useEffect(() => {
    getOrCreateMe();
  }, [getOrCreateMe]);

  useEffect(() => {
    console.log("user changed:", user);
  }, [user]);

  return (
    <div>
      <Header userName={user?.name} userEmail={user?.email}></Header>
      <PlaidLinkPage></PlaidLinkPage>
      <ConnectionsPanel></ConnectionsPanel>
    </div>
  );
}
