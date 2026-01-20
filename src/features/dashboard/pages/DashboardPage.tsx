import { useCallback, useContext, useEffect } from "react";
import Header from "../../../Components/Header";
import PlaidLinkPage from "../../plaid/pages/PlaidLinkPage";
import { DashboardProvider } from "../state/DashboardProvider";
import { DashboardContext } from "../state/DashboardContext";
import { get_or_create_me } from "../api/backend/client";
import { AuthContext } from "../../auth/state/AuthContext";

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
      <Header></Header>
      <PlaidLinkPage></PlaidLinkPage>
    </div>
  );
}
