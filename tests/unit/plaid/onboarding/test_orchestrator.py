from types import SimpleNamespace
from uuid import uuid4

from src.workflows.onboarding import OnboardingOrchestrator


class FakePlaidItemService:
    def __init__(self, item):
        self.item = item
        self.plaid_item_repo = self

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
        self.item.plaid_item_id = plaid_item_id
        return self.item


class FakePlaidAccountService:
    def __init__(self):
        self.synced_items = []

    def sync_accounts_for_item(self, plaid_client, item, db, kms):
        self.synced_items.append(item)


class FakeMembershipService:
    def get_my_membership(self, db, user_id):
        return SimpleNamespace(household_id=uuid4())


class FakeSyncJobsRequestService:
    def __init__(self):
        self.onboarding_item_ids = []

    def handle_onboarding(self, db, plaid_item):
        self.onboarding_item_ids.append(plaid_item)


def test_onboarding_enqueues_initial_sync_job():
    item = SimpleNamespace(id=uuid4())
    account_service = FakePlaidAccountService()
    sync_jobs_request_service = FakeSyncJobsRequestService()
    orchestrator = OnboardingOrchestrator(
        plaid_item_service=FakePlaidItemService(item=item),
        plaid_account_service=account_service,
        membership_service=FakeMembershipService(),
        sync_jobs_request_service=sync_jobs_request_service,
    )

    result = orchestrator.onboard_new_item(
        db=SimpleNamespace(),
        kms=SimpleNamespace(),
        user=SimpleNamespace(id=uuid4()),
        plaid_client=SimpleNamespace(),
        link_public_token="public-token",
    )

    assert result is item
    assert account_service.synced_items == [item]
    assert sync_jobs_request_service.onboarding_item_ids == [item]
