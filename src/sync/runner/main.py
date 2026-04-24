from ...plaid.transactions.service import TransactionService
from ..jobs.execution_service import SyncJobsExecutionService
from ...infrastructure import Session, KMSService, PlaidClient


def process(
    db: Session,
    kms: KMSService,
    plaid_client: PlaidClient,
    sync_jobs_execution_service: SyncJobsExecutionService,
    transaction_service: TransactionService,
):
    with db.begin():
        job = sync_jobs_execution_service.claim_next_due_job(db=db)
        if job is None:
            return

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
