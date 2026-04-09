import { createContext, useReducer, Dispatch, ReactNode } from "react";

interface QuickstartState {
  linkSuccess: boolean;
  isItemAccess: boolean;
  // isPaymentInitiation: boolean;                    // Not supported in this app
  // isUserTokenFlow: boolean;                    // Not supported in this app
  // isCraProductsExclusively: boolean;                     // Not supported in this app
  linkToken: string | null;
  accessToken: string | null;
  // userToken: string | null;
  userId: string | null;
  itemId: string | null;
  isError: boolean;
  products: string[];
  error: {
    error_message: string;
    error_code: string;
  };
}

const initialState: QuickstartState = {
  linkSuccess: false,
  isItemAccess: true,
  linkToken: "", // Don't set to null or error message will show up briefly when site loads
  userId: null,
  accessToken: null,
  itemId: null,
  isError: false,
  products: ["transactions"],
  error: {
    error_code: "",
    error_message: "",
  },
};

type QuickstartAction = {
  type: "SET_STATE";
  state: Partial<QuickstartState>;
};

interface QuickstartContext extends QuickstartState {
  dispatch: Dispatch<QuickstartAction>;
}

const Context = createContext<QuickstartContext>(
  initialState as QuickstartContext
);

const { Provider } = Context;
export const QuickstartProvider: React.FC<{ children: ReactNode }> = (
  props
) => {
  const reducer = (
    state: QuickstartState,
    action: QuickstartAction
  ): QuickstartState => {
    switch (action.type) {
      case "SET_STATE":
        return { ...state, ...action.state };
      default:
        return { ...state };
    }
  };
  const [state, dispatch] = useReducer(reducer, initialState);
  return <Provider value={{ ...state, dispatch }}>{props.children}</Provider>;
};

export default Context;
