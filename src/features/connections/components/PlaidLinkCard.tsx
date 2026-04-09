import { useCallback, useEffect, useMemo, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import {
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
      _publicToken: string,
      metadata: { institution: { name?: string } | null }
    ) => {
      const institutionName = metadata.institution?.name ?? "your institution";

      setStatusMessage(
        `Plaid Link completed for ${institutionName}. This frontend now follows the generated backend contract, which exposes token creation and data reads but not a public-token exchange route yet, so no new connection is persisted until the backend adds that endpoint.`
      );
      setErrorMessage(null);
      setLinkToken(null);
      window.localStorage.removeItem(LINK_TOKEN_STORAGE_KEY);
      await refreshConnections();
    },
    [refreshConnections]
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
          The generated backend contract currently supports Plaid link-token creation
          plus connection and account reads. It does not yet expose a public-token
          exchange endpoint, so this card opens Plaid Link and refreshes cached data,
          but completed links will not persist until that backend route exists.
        </InlineMessage>

        {errorMessage ? <InlineMessage tone="error">{errorMessage}</InlineMessage> : null}
        {statusMessage ? (
          <InlineMessage tone="success">{statusMessage}</InlineMessage>
        ) : null}

        <div className={styles.actions}>
          <Button
            onClick={handleLaunch}
            disabled={createLinkTokenMutation.isPending || (Boolean(linkToken) && !ready)}
          >
            {createLinkTokenMutation.isPending ? "Preparing Plaid Link..." : "Launch Plaid Link"}
          </Button>
        </div>

        <p className={styles.caption}>
          Once the backend exposes token exchange, this card can invalidate and show
          newly linked institutions without another architecture change.
        </p>
      </div>
    </Card>
  );
}
