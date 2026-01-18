import { QuickstartProvider } from "../../plaid/Context";
import PlaidLinkApp from "../../plaid/PlaidLinkApp";

export default function DashboardPage() {
  return (
    <div>
      Dashboard Page
      <QuickstartProvider>
        <PlaidLinkApp></PlaidLinkApp>
      </QuickstartProvider>
    </div>
  );
}
