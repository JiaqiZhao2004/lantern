import { useEffect, useContext, useCallback } from "react";
import { usePlaidLink } from "react-plaid-link";
import Button from "plaid-threads/Button";
import styles from "./index.module.css";
import LinkContext from "../../state/LinkContext";
import { PlaidService } from "../../api/plaid/client";

const PlaidLinkButton = () => {
  const { linkToken, dispatch } = useContext(LinkContext);

  const onSuccess = useCallback(
    (public_token: string) => {
      PlaidService.addItem(public_token).then(() =>
        dispatch({ type: "SET_STATE", state: { linkSuccess: true } })
      );
      // window.history.pushState("", "", "/");
    },
    [dispatch]
  );

  let isOauth = false;
  const config: Parameters<typeof usePlaidLink>[0] = {
    token: linkToken!,
    onSuccess,
  };

  if (window.location.href.includes("?oauth_state_id=")) {
    // TODO: figure out how to delete this ts-ignore
    // @ts-ignore
    config.receivedRedirectUri = window.location.href;
    isOauth = true;
  }

  const { open, ready } = usePlaidLink(config);

  useEffect(() => {
    if (isOauth && ready) {
      open();
    }
  }, [ready, open, isOauth]);

  return (
    <>
      {linkToken === "" ? (
        <div className={styles.linkButton}>
          <Button large disabled>
            Loading...
          </Button>
        </div>
      ) : (
        <div className={styles.linkButton}>
          <Button type="button" large onClick={() => open()} disabled={!ready}>
            Launch Link
          </Button>
        </div>
      )}
    </>
  );
};

PlaidLinkButton.displayName = "Link";

export default PlaidLinkButton;
