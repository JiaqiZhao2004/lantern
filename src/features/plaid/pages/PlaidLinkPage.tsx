import { QuickstartProvider } from "../Context";
import PlaidLinkApp from "../PlaidLinkApp";

export default function PlaidLinkPage() {
  return (
    <QuickstartProvider>
      <PlaidLinkApp></PlaidLinkApp>
    </QuickstartProvider>
  );
}
