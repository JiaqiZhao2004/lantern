import React, { useEffect, useContext, useCallback } from "react";
import Context, { QuickstartProvider } from "../state/Context";

import Products from "./ProductTypes/Products";
import Items from "./ProductTypes/Items";
import LaunchLinkButton from "./LaunchLinkButton";
import { PlaidService } from "../../link/api/plaid/client";
import { isAppError } from "../../../core/appErrors";

// import styles from "./PlaidLinkApp.module.scss";

export default function PlaidLinkPage() {
  return (
    <QuickstartProvider>
      <PlaidLinkApp></PlaidLinkApp>
    </QuickstartProvider>
  );
}

const PlaidLinkApp = () => {
  const { linkSuccess, itemId, dispatch } = useContext(Context);

  const getInfo = useCallback(async () => {
    try {
      const data = (await PlaidService.getInfo()) as unknown as Object; // TODO: fix type
      dispatch({
        type: "SET_STATE",
        state: {
          products: data.hasOwnProperty("products")
            ? (data as any).products
            : [],
        },
      });
    } catch (e: any) {
      if (isAppError(e)) {
        console.error(e.message);

        dispatch({
          type: "SET_STATE",
          state: { error: { error_code: e.code, error_message: e.message } },
        });
      }
    }
  }, [dispatch]);

  const generateToken = useCallback(async () => {
    // Link tokens for 'payment_initiation' use a different creation flow in your backend.
    await PlaidService.createLinkToken()
      .catch((e: any) => {
        if (isAppError(e)) {
          console.error(e.message);
        }
        dispatch({
          type: "SET_STATE",
          state: {
            linkToken: null,
            error: { error_code: e.code, error_message: e.message },
          },
        });
      })
      .then((linkToken: string) => {
        dispatch({ type: "SET_STATE", state: { linkToken: linkToken } });
        localStorage.setItem("link_token", linkToken);
      });
  }, [dispatch]);

  useEffect(() => {
    const init = async () => {
      await getInfo();
      console.log("Initializing Plaid Link");
      // do not generate a new token for OAuth redirect; instead
      // setLinkToken from localStorage
      if (window.location.href.includes("?oauth_state_id=")) {
        dispatch({
          type: "SET_STATE",
          state: {
            linkToken: localStorage.getItem("link_token"),
          },
        });
        return;
      }
      generateToken();
    };
    init();
  }, [dispatch, generateToken, getInfo]);

  return (
    <div>
      <LaunchLinkButton />
      {linkSuccess && (
        <>
          <Products />
          {itemId && <Items />}
        </>
      )}
    </div>
  );
};
