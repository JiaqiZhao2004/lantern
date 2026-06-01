import logging
import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

from src.infrastructure import KMSService, PlaidClient, Session
from src.infrastructure import get_kms_service, get_plaid_client
from src.infrastructure.db.database import SessionLocal
from src.modules.plaid_accounts.repository import PlaidAccountRepository
from src.modules.plaid_items.repository import PlaidItemRepository
from src.modules.plaid_transactions.repository import TransactionRepository
from src.modules.plaid_transactions.service import TransactionService
from src.modules.plaid_transaction_sync_jobs.execution_service import SyncJobsExecutionService
from src.modules.plaid_transaction_sync_jobs.repository import SyncJobsRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunnerServices:
    kms: KMSService
    plaid_client: PlaidClient
    sync_jobs_execution_service: SyncJobsExecutionService
    transaction_service: TransactionService


def build_runner_services() -> RunnerServices:
    plaid_item_repo = PlaidItemRepository()
    sync_jobs_repo = SyncJobsRepository()

    return RunnerServices(
        kms=get_kms_service(),
        plaid_client=get_plaid_client(),
        sync_jobs_execution_service=SyncJobsExecutionService(
            plaid_items_repo=plaid_item_repo,
            sync_jobs_repo=sync_jobs_repo,
        ),
        transaction_service=TransactionService(
            plaid_item_repo=plaid_item_repo,
            plaid_account_repo=PlaidAccountRepository(),
            transaction_repo=TransactionRepository(),
        ),
    )


def process(
    db: Session,
    kms: KMSService,
    plaid_client: PlaidClient,
    sync_jobs_execution_service: SyncJobsExecutionService,
    transaction_service: TransactionService,
) -> bool:
    with db.begin():
        job = sync_jobs_execution_service.claim_next_due_job(db=db)
        if job is None:
            return False

        plaid_item = job.institution_connection

        try:
            transaction_service.sync(
                db=db, kms=kms, plaid_client=plaid_client, plaid_item=plaid_item
            )
        except Exception as e:
            sync_jobs_execution_service.handle_failure(
                db=db, job=job, plaid_item=plaid_item, error=e
            )
        else:
            sync_jobs_execution_service.handle_success(
                db=db, job=job, plaid_item=plaid_item
            )
        return True


def process_once(services: RunnerServices | None = None) -> bool:
    services = services or build_runner_services()
    with SessionLocal() as db:
        return process(
            db=db,
            kms=services.kms,
            plaid_client=services.plaid_client,
            sync_jobs_execution_service=services.sync_jobs_execution_service,
            transaction_service=services.transaction_service,
        )


def run_forever(
    services: RunnerServices | None = None,
    sleep_seconds: float | None = None,
):
    services = services or build_runner_services()
    if sleep_seconds is None:
        sleep_seconds = float(os.getenv("SYNC_RUNNER_SLEEP_SECONDS", "10"))

    while True:
        try:
            process_once(services=services)
        except Exception:
            logger.exception("Unhandled sync runner error")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_forever()
