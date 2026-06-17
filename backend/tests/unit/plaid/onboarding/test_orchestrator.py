from types import SimpleNamespace
from uuid import uuid4

from src.workflows.link_institution_connection import LinkInstitutionConnectionWorkflow


class FakeConnectionService:
    def __init__(self, connection):
        self.connection = connection
        self.connection_repo = self

    def exchange_public_token(self, plaid_client, link_public_token):
        return "plaid-item-1", "access-token"

    def get_institution_info(self, plaid_client, plaid_access_token):
        return "ins_1", "Test Bank"

    def create_encrypted(
        self,
        db,
        kms,
        user,
        household_id,
        plaid_item_id,
        plaid_access_token,
        institution_id,
        institution_name,
    ):
        self.connection.plaid_item_id = plaid_item_id
        return self.connection


class FakeAccountService:
    def __init__(self):
        self.synced_connections = []

    def sync_accounts_for_connection(self, plaid_client, connection, db, kms):
        self.synced_connections.append(connection)


class FakeMembershipService:
    def get_my_membership(self, db, user_id):
        return SimpleNamespace(household_id=uuid4())


class FakeSyncJobsRequestService:
    def __init__(self):
        self.initial_link_connections = []

    def create_initial_link_sync_job(self, db, connection):
        self.initial_link_connections.append(connection)


def test_link_enqueues_initial_sync_job():
    connection = SimpleNamespace(id=uuid4())
    account_service = FakeAccountService()
    sync_jobs_request_service = FakeSyncJobsRequestService()
    workflow = LinkInstitutionConnectionWorkflow(
        connection_service=FakeConnectionService(connection=connection),
        account_service=account_service,
        membership_service=FakeMembershipService(),
        sync_jobs_request_service=sync_jobs_request_service,
    )

    result = workflow.link_new_connection(
        db=SimpleNamespace(),
        kms=SimpleNamespace(),
        user=SimpleNamespace(id=uuid4()),
        plaid_client=SimpleNamespace(),
        link_public_token="public-token",
    )

    assert result is connection
    assert account_service.synced_connections == [connection]
    assert sync_jobs_request_service.initial_link_connections == [connection]
