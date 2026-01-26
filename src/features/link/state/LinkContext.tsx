import { createContext, useReducer, Dispatch, ReactNode } from "react";

interface LinkState {
  linkSuccess: boolean;
  linkToken: string | null;
  accessToken: string | null;
  itemId: string | null;
  products: string[];
  error: {
    error_message: string;
    error_code: string;
  };
}

const initialState: LinkState = {
  linkSuccess: false,
  linkToken: "", // Don't set to null or error message will show up briefly when site loads
  accessToken: null,
  itemId: null,
  products: [],
  error: {
    error_code: "",
    error_message: "",
  },
};

type LinkAction = {
  type: "SET_STATE" | "RESET";
  state?: Partial<LinkState>;
};

interface ILinkContext extends LinkState {
  dispatch: Dispatch<LinkAction>;
}

const LinkContext = createContext<ILinkContext>(initialState as ILinkContext);

const { Provider } = LinkContext;
export const LinkProvider: React.FC<{ children: ReactNode }> = (props) => {
  const reducer = (state: LinkState, action: LinkAction): LinkState => {
    switch (action.type) {
      case "SET_STATE":
        return { ...state, ...action.state };
      case "RESET":
        return { ...initialState };
      default:
        return { ...state };
    }
  };
  const [state, dispatch] = useReducer(reducer, initialState);
  return <Provider value={{ ...state, dispatch }}>{props.children}</Provider>;
};

export default LinkContext;
