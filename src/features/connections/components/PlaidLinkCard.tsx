import { useCallback, useEffect, useMemo, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import {
  useAddItemMutation,
  useCreateLinkTokenMutation,
  useRefreshConnections,
} from "@/features/connections/api/queries";
import { Card } from "@/shared/ui/Card/Card";
import { Button } from "@/shared/ui/Button/Button";
import { InlineMessage } from "@/shared/ui/InlineMessage/InlineMessage";
import styles from "@/features/connections/components/PlaidLinkCard.module.css";

const LINK_TOKEN_STORAGE_KEY = "family-finance:plaid-link-token";

export function PlaidLinkCard() {
  const createLinkTokenMutation = useCreateLinkTokenMutation();
  const addItemMutation = useAddItemMutation();
  const { mutateAsync: addItem, isPending: isAddingItem } = addItemMutation;
  const refreshConnections = useRefreshConnections();
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (window.location.href.includes("?oauth_state_id=")) {
      setLinkToken(window.localStorage.getItem(LINK_TOKEN_STORAGE_KEY));
    }
  }, []);

  const onSuccess = useCallback(
    async (
      publicToken: string,
      metadata: { institution: { name?: string } | null }
    ) => {
      const institutionName = metadata.institution?.name ?? "your institution";

      setErrorMessage(null);

      try {
        await addItem({ link_public_token: publicToken });
        setStatusMessage(
          `Linked ${institutionName}. New connection data will appear after syncing finishes.`
        );
        setLinkToken(null);
        window.localStorage.removeItem(LINK_TOKEN_STORAGE_KEY);
        await refreshConnections();
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Plaid Link completed, but the item could not be added."
        );
      }
    },
    [addItem, refreshConnections]
  );

  const onExit = useCallback((exitError: { display_message?: string } | null) => {
    if (exitError?.display_message) {
      setErrorMessage(exitError.display_message);
    }
  }, []);

  const plaidConfig = useMemo<Parameters<typeof usePlaidLink>[0]>(
    () => ({
      token: linkToken,
      onSuccess,
      onExit,
      ...(window.location.href.includes("?oauth_state_id=") && linkToken
        ? { receivedRedirectUri: window.location.href }
        : {}),
    }),
    [linkToken, onExit, onSuccess]
  );

  const { open, ready } = usePlaidLink(plaidConfig);

  useEffect(() => {
    if (linkToken && ready) {
      open();
    }
  }, [linkToken, open, ready]);

  const handleLaunch = async () => {
    setErrorMessage(null);
    setStatusMessage(null);

    try {
      const response = await createLinkTokenMutation.mutateAsync();
      setLinkToken(response.link_token);
      window.localStorage.setItem(LINK_TOKEN_STORAGE_KEY, response.link_token);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create a Plaid Link token right now."
      );
    }
  };

  return (
    <Card>
      <div className={styles.stack}>
        <div>
          <h2 className={styles.title}>Connect an institution</h2>
          <p className={styles.body}>
            Create a fresh Plaid Link token and launch the connection flow from the
            dashboard.
          </p>
        </div>

        <InlineMessage tone="info">
          Finish the Plaid flow to connect an institution. Linked accounts refresh
          automatically after the connection syncs.
        </InlineMessage>

        {errorMessage ? <InlineMessage tone="error">{errorMessage}</InlineMessage> : null}
        {statusMessage ? (
          <InlineMessage tone="success">{statusMessage}</InlineMessage>
        ) : null}

        <div className={styles.actions}>
          <Button
            onClick={handleLaunch}
            disabled={
              createLinkTokenMutation.isPending ||
              isAddingItem ||
              (Boolean(linkToken) && !ready)
            }
          >
            {createLinkTokenMutation.isPending
              ? "Preparing Plaid Link..."
              : isAddingItem
              ? "Adding institution..."
              : "Launch Plaid Link"}
          </Button>
        </div>

        <p className={styles.caption}>
          OAuth redirects resume automatically so the connection can finish after
          returning to the dashboard.
        </p>
      </div>
    </Card>
  );
}
