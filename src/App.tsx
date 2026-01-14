import React, { useEffect, useContext, useCallback } from "react";

import Header from "./Components/Headers";
import Products from "./Components/ProductTypes/Products";
import Items from "./Components/ProductTypes/Items";
import Context from "./Context";

import styles from "./App.module.scss";
// import { Products as PlaidProducts } from "plaid";

const App = () => {
  const { linkSuccess, itemId, dispatch } = useContext(Context);

  const getInfo = useCallback(async () => {
    const response = await fetch("/api/info", { method: "POST" });
    if (!response.ok) {
      dispatch({ type: "SET_STATE", state: { backend: false } });
    }
    const data = await response.json();

    dispatch({
      type: "SET_STATE",
      state: {
        products: data.products,
      },
    });
  }, [dispatch]);

  const generateUserToken = useCallback(async () => {
    const response = await fetch("api/create_user_token", { method: "POST" });
    if (!response.ok) {
      dispatch({ type: "SET_STATE", state: { userToken: null, userId: null } });
      return;
    }
    const data = await response.json();
    if (data) {
      if (data.error != null) {
        dispatch({
          type: "SET_STATE",
          state: {
            linkToken: null,
            linkTokenError: data.error,
          },
        });
        return;
      }
      dispatch({
        type: "SET_STATE",
        state: {
          userToken: data.user_token || null,
          userId: data.user_id || null,
        },
      });
      return data.user_token || data.user_id;
    }
  }, [dispatch]);

  const generateToken = useCallback(async () => {
    // Link tokens for 'payment_initiation' use a different creation flow in your backend.
    const path = "/api/create_link_token";
    const response = await fetch(path, {
      method: "POST",
    });
    if (!response.ok) {
      dispatch({ type: "SET_STATE", state: { linkToken: null } });
      return;
    }
    const data = await response.json();
    if (data) {
      if (data.error != null) {
        dispatch({
          type: "SET_STATE",
          state: {
            linkToken: null,
            linkTokenError: data.error,
          },
        });
        return;
      }
      dispatch({ type: "SET_STATE", state: { linkToken: data.link_token } });
    }
    // Save the link_token to be used later in the Oauth flow.
    localStorage.setItem("link_token", data.link_token);
  }, [dispatch]);

  useEffect(() => {
    const init = async () => {
      getInfo();
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
  }, [dispatch, generateToken, generateUserToken, getInfo]);

  return (
    <div className={styles.App}>
      <div className={styles.container}>
        <Header />
        {linkSuccess && (
          <>
            <Products />
            {itemId && <Items />}
          </>
        )}
      </div>
    </div>
  );
};

export default App;
