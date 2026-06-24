import logging
from dataclasses import dataclass

from plaid.model.item_get_request import ItemGetRequest
from plaid.model.item_webhook_update_request import ItemWebhookUpdateRequest
from sqlalchemy.orm import Session

from src.infrastructure import KMSService, PlaidClient

from .repository import InstitutionConnectionRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlaidWebhookReconciliationResult:
    checked: int = 0
    updated: int = 0
    skipped: int = 0


class PlaidWebhookReconciler:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        kms: KMSService | None,
        plaid_client: PlaidClient | None,
        webhook_url: str | None,
    ):
        self.connection_repo = connection_repo
        self.kms = kms
        self.plaid_client = plaid_client
        self.webhook_url = webhook_url

    def dry_run(self, db: Session) -> PlaidWebhookReconciliationResult:
        connections = self.connection_repo.list_active(db=db)
        logger.info(
            "Plaid webhook dry run found %s active institution connections",
            len(connections),
        )
        return PlaidWebhookReconciliationResult(
            checked=len(connections),
            updated=0,
            skipped=len(connections),
        )

    def apply(self, db: Session) -> PlaidWebhookReconciliationResult:
        if not self.webhook_url:
            raise ValueError("PLAID_WEBHOOK_URL is required to reconcile Plaid webhooks")
        if self.kms is None or self.plaid_client is None:
            raise ValueError("KMS and Plaid client are required to apply webhook reconciliation")

        checked = 0
        updated = 0
        for connection in self.connection_repo.list_active(db=db):
            checked += 1
            access_token = self.kms.decrypt_secret(
                encrypted_data_key=connection.plaid_access_token_encrypted_data_key,
                nonce=connection.plaid_access_token_nonce,
                ciphertext=connection.plaid_access_token_ciphertext,
            )

            item_response = self.plaid_client.item_get(
                ItemGetRequest(access_token=access_token)
            )
            item = _to_dict(item_response).get("item", {})
            current_webhook = item.get("webhook")

            if current_webhook == self.webhook_url:
                logger.info(
                    "Plaid webhook already current for connection_id=%s plaid_item_id=%s",
                    connection.id,
                    connection.plaid_item_id,
                )
                continue

            self.plaid_client.item_webhook_update(
                ItemWebhookUpdateRequest(
                    access_token=access_token,
                    webhook=self.webhook_url,
                )
            )
            updated += 1
            logger.info(
                "Updated Plaid webhook for connection_id=%s plaid_item_id=%s",
                connection.id,
                connection.plaid_item_id,
            )

        return PlaidWebhookReconciliationResult(
            checked=checked,
            updated=updated,
            skipped=checked - updated,
        )


def _to_dict(response) -> dict:
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return response
