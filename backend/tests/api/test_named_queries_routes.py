from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import src.api.routes.named_queries as named_query_routes
from src.exceptions import InternalError
from src.modules.named_queries.schemas import (
    NamedQueryCandidate,
    NamedQueryCandidateResponse,
    NamedQueryClarifyingQuestionResponse,
)
from src.server import app


class FakeDb:
    def commit(self):
        pass

    def rollback(self):
        pass


class FakeMembershipRepo:
    def __init__(self, membership):
        self.membership = membership

    def get_membership_for_user(self, db, user_id):
        return self.membership


class FakeGenerationService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, db, household_id, messages):
        self.calls.append((household_id, messages))
        return self.response


class FailingGenerationService:
    def __init__(self, error):
        self.error = error

    def generate(self, db, household_id, messages):
        raise self.error


def _override_request_context():
    return SimpleNamespace(db=FakeDb(), user=SimpleNamespace(id=uuid4()))


def test_generate_named_query_returns_candidate_response():
    household_id = uuid4()
    service = FakeGenerationService(
        NamedQueryCandidateResponse(
            name="Spending by category",
            candidate=NamedQueryCandidate(
                sql_query="SELECT category_primary FROM widget_transactions",
                chart_type="bar",
            )
        )
    )
    app.dependency_overrides[named_query_routes.get_request_context] = (
        _override_request_context
    )
    app.dependency_overrides[named_query_routes.get_membership_repository] = (
        lambda: FakeMembershipRepo(SimpleNamespace(household_id=household_id))
    )
    app.dependency_overrides[named_query_routes.get_named_query_generation_service] = (
        lambda: service
    )

    try:
        response = TestClient(app).post(
            "/api/v1/named-queries/generate",
            json={"messages": [{"role": "member", "content": "show spending"}]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["type"] == "named_query_candidate"
    assert response.json()["name"] == "Spending by category"
    assert response.json()["candidate"]["chart_type"] == "bar"
    assert service.calls[0][0] == household_id


def test_generate_named_query_returns_clarifying_question_response():
    app.dependency_overrides[named_query_routes.get_request_context] = (
        _override_request_context
    )
    app.dependency_overrides[named_query_routes.get_membership_repository] = (
        lambda: FakeMembershipRepo(SimpleNamespace(household_id=uuid4()))
    )
    app.dependency_overrides[named_query_routes.get_named_query_generation_service] = (
        lambda: FakeGenerationService(
            NamedQueryClarifyingQuestionResponse(question="Which category?")
        )
    )

    try:
        response = TestClient(app).post(
            "/api/v1/named-queries/generate",
            json={"messages": [{"role": "member", "content": "show spending"}]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "type": "clarifying_question",
        "question": "Which category?",
    }


def test_generate_named_query_returns_generation_failure_on_provider_error():
    app.dependency_overrides[named_query_routes.get_request_context] = (
        _override_request_context
    )
    app.dependency_overrides[named_query_routes.get_membership_repository] = (
        lambda: FakeMembershipRepo(SimpleNamespace(household_id=uuid4()))
    )
    app.dependency_overrides[named_query_routes.get_named_query_generation_service] = (
        lambda: FailingGenerationService(InternalError(detail="provider down"))
    )

    try:
        response = TestClient(app).post(
            "/api/v1/named-queries/generate",
            json={"messages": [{"role": "member", "content": "show spending"}]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "type": "generation_failure",
        "message": "I could not generate a query right now because the AI provider is unavailable. Please try again.",
        "reason": "provider_unavailable",
    }


def test_generate_named_query_returns_quota_failure_message_for_openai_billing_errors():
    app.dependency_overrides[named_query_routes.get_request_context] = (
        _override_request_context
    )
    app.dependency_overrides[named_query_routes.get_membership_repository] = (
        lambda: FakeMembershipRepo(SimpleNamespace(household_id=uuid4()))
    )
    app.dependency_overrides[named_query_routes.get_named_query_generation_service] = (
        lambda: FailingGenerationService(
            InternalError(
                detail=(
                    "OpenAI request failed: You exceeded your current quota, "
                    "please check your plan and billing details."
                )
            )
        )
    )

    try:
        response = TestClient(app).post(
            "/api/v1/named-queries/generate",
            json={"messages": [{"role": "member", "content": "show spending"}]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "type": "generation_failure",
        "message": (
            "AI assist is unavailable because the configured OpenAI account has no "
            "remaining quota or billing is not active. Check the account's billing "
            "details, then try again."
        ),
        "reason": "provider_quota_exceeded",
    }
