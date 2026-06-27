import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.infrastructure import KMSService, PlaidClient, Session
from src.infrastructure import get_kms_service, get_plaid_client
from src.infrastructure.db.database import SessionLocal
from src.modules.accounts.repository import AccountRepository
from src.modules.institution_connections.repository import InstitutionConnectionRepository
from src.modules.model_registry import load_all_models
from src.modules.plaid_transactions.repository import TransactionRepository
from src.modules.plaid_transactions.service import TransactionService
from src.modules.sync_jobs.execution_service import SyncJobsExecutionService
from src.modules.sync_jobs.repository import SyncJobsRepository

logger = logging.getLogger(__name__)


def _write_text_atomically(path: Path, content: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def write_heartbeat(now: float | None = None):
    heartbeat_path = os.getenv("SYNC_RUNNER_HEARTBEAT_PATH")
    if not heartbeat_path:
        return

    timestamp = time.time() if now is None else now
    path = Path(heartbeat_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".prom":
        stack = os.getenv("SYNC_RUNNER_HEARTBEAT_STACK")
        labels = ""
        if stack:
            escaped_stack = stack.replace("\\", "\\\\").replace('"', '\\"')
            labels = f'{{stack="{escaped_stack}"}}'
        _write_text_atomically(
            path=path,
            content=(
                "# HELP lantern_sync_runner_last_heartbeat_timestamp_seconds "
                "Unix timestamp for the latest sync runner heartbeat.\n"
                "# TYPE lantern_sync_runner_last_heartbeat_timestamp_seconds gauge\n"
                f"lantern_sync_runner_last_heartbeat_timestamp_seconds{labels} {timestamp:.6f}\n"
            ),
        )
        return

    path.touch()


@dataclass(frozen=True)
class RunnerServices:
    kms: KMSService
    plaid_client: PlaidClient
    sync_jobs_execution_service: SyncJobsExecutionService
    transaction_service: TransactionService


def build_runner_services() -> RunnerServices:
    load_all_models()

    connection_repo = InstitutionConnectionRepository()
    sync_jobs_repo = SyncJobsRepository()

    return RunnerServices(
        kms=get_kms_service(),
        plaid_client=get_plaid_client(),
        sync_jobs_execution_service=SyncJobsExecutionService(
            connection_repo=connection_repo,
            sync_jobs_repo=sync_jobs_repo,
        ),
        transaction_service=TransactionService(
            connection_repo=connection_repo,
            account_repo=AccountRepository(),
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

        connection = job.institution_connection

        try:
            transaction_service.sync(
                db=db, kms=kms, plaid_client=plaid_client, connection=connection
            )
        except Exception as e:
            sync_jobs_execution_service.handle_failure(
                db=db, job=job, connection=connection, error=e
            )
        else:
            sync_jobs_execution_service.handle_success(
                db=db, job=job, connection=connection
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
        did_process = False
        try:
            did_process = process_once(services=services)
        except Exception:
            logger.exception("Unhandled sync runner error")
        finally:
            write_heartbeat()

        if not did_process:
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run_forever()
