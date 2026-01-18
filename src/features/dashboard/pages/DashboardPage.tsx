import Header from "../../../Components/Header";
import { QuickstartProvider } from "../../plaid/Context";
import PlaidLinkApp from "../../plaid/PlaidLinkApp";

export default function DashboardPage() {
  return (
    <div>
      <Header></Header>
      Dashboard Page
      <QuickstartProvider>
        <PlaidLinkApp></PlaidLinkApp>
      </QuickstartProvider>
    </div>
  );
}
