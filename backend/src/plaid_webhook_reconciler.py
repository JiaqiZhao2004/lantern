import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.infrastructure import get_kms_service, get_plaid_client
from src.infrastructure.db.database import SessionLocal
from src.modules.institution_connections.plaid_webhook_reconciler import (
    PlaidWebhookReconciler,
)
from src.modules.institution_connections.repository import InstitutionConnectionRepository


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Reconcile Plaid Item webhook URLs for active institution connections."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Report active connections without decrypting tokens or calling Plaid.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Repair missing or stale Plaid Item webhook URLs.",
    )
    return parser.parse_args(argv)


def build_reconciler(apply: bool) -> PlaidWebhookReconciler:
    return PlaidWebhookReconciler(
        connection_repo=InstitutionConnectionRepository(),
        kms=get_kms_service() if apply else None,
        plaid_client=get_plaid_client() if apply else None,
        webhook_url=os.getenv("PLAID_WEBHOOK_URL"),
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    args = parse_args(argv)

    try:
        reconciler = build_reconciler(apply=args.apply)
        with SessionLocal() as db:
            if args.dry_run:
                result = reconciler.dry_run(db=db)
            else:
                result = reconciler.apply(db=db)
    except Exception:
        logging.exception("Plaid webhook reconciliation failed")
        return 1

    logging.info(
        "Plaid webhook reconciliation complete: checked=%s updated=%s skipped=%s",
        result.checked,
        result.updated,
        result.skipped,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
