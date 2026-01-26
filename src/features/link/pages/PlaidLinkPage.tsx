import React, { useEffect, useContext, useCallback } from "react";

import PlaidLinkButton from "./PlaidLinkButton";
import {
  plaidCreateLinkToken,
  plaidGetInfo,
} from "../../link/api/plaid/client";
import { isAppError } from "../../../core/appErrors";
import LinkContext, { LinkProvider } from "../state/LinkContext";

import styles from "./PlaidLinkApp.module.scss";

export default function PlaidLinkPage() {
  return (
    <LinkProvider>
      <PlaidLinkApp></PlaidLinkApp>
    </LinkProvider>
  );
}

const PlaidLinkApp = () => {
  const { linkSuccess, itemId, dispatch } = useContext(LinkContext);

  const getInfo = useCallback(async () => {
    try {
      const data = (await plaidGetInfo()) as unknown as Object; // TODO: fix type
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
    const linkToken = await plaidCreateLinkToken()
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
      // await getInfo();
      // console.log("Initializing Plaid Link");
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

  return <PlaidLinkButton />;
};
