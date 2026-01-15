// import { QuickstartProvider } from "../features/plaid/Context";
// import PlaidLinkApp from "../features/plaid/PlaidLinkApp";
// // import { Products as PlaidProducts } from "plaid";

// const App = () => {
//   return (
//     <div>
//       <QuickstartProvider>
//         <PlaidLinkApp />
//       </QuickstartProvider>
//     </div>
//   );
// };

// export default App;

// src/app/App.tsx
import React from "react";
import { BrowserRouter } from "react-router-dom";

import { AppRoutes } from "./routes";
import { AuthProvider } from "../features/auth/AuthProvider";

// If you use React Query, uncomment these
// import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// const queryClient = new QueryClient();

export default function App() {
  return (
    // <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
    // </QueryClientProvider>
  );
}
