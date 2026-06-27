import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from ..dependencies import RequestContext, get_request_context
from src.exceptions import InternalError
from src.infrastructure.llm import LLMClient, get_llm_client
from src.modules.named_queries import (
    NamedQueryGenerationService,
    NamedQueryGenerationUsageRepository,
    NamedQueryService,
    NamedQueryCreateRequest,
    NamedQueryGenerateRequest,
    NamedQueryGenerateResponse,
    NamedQueryGenerationFailureResponse,
    NamedQueryPatchRequest,
    NamedQueryPreviewRequest,
    NamedQueryResponse,
    NamedQueryDataResponse,
)
from src.modules.household_membership.repository import MembershipRepository
from src.modules.named_queries.repository import NamedQueryRepository

router = APIRouter(prefix="/api/v1/named-queries", tags=["named-queries"])
logger = logging.getLogger(__name__)


def _provider_failure_response(detail: str) -> NamedQueryGenerationFailureResponse:
    normalized = detail.strip().lower()

    if "not configured" in normalized:
        return NamedQueryGenerationFailureResponse(
            message="AI assist is not configured yet. Set a valid OPENAI_API_KEY for the backend and try again.",
            reason="provider_not_configured",
        )

    if "exceeded your current quota" in normalized or "billing" in normalized:
        return NamedQueryGenerationFailureResponse(
            message="AI assist is unavailable because the configured OpenAI account has no remaining quota or billing is not active. Check the account's billing details, then try again.",
            reason="provider_quota_exceeded",
        )

    return NamedQueryGenerationFailureResponse(
        message="I could not generate a query right now because the AI provider is unavailable. Please try again.",
        reason="provider_unavailable",
    )


def get_named_query_repository() -> NamedQueryRepository:
    return NamedQueryRepository()


def get_named_query_generation_usage_repository() -> NamedQueryGenerationUsageRepository:
    return NamedQueryGenerationUsageRepository()


def get_named_query_service(
    repo: NamedQueryRepository = Depends(get_named_query_repository),
) -> NamedQueryService:
    return NamedQueryService(named_query_repo=repo)


def get_named_query_generation_service(
    usage_repo: NamedQueryGenerationUsageRepository = Depends(
        get_named_query_generation_usage_repository
    ),
    llm_client: LLMClient = Depends(get_llm_client),
) -> NamedQueryGenerationService:
    return NamedQueryGenerationService(
        usage_repo=usage_repo,
        llm_client=llm_client,
    )


def _resolve_household_id(ctx: RequestContext, membership_repo: MembershipRepository) -> UUID:
    from src.exceptions import NotFoundError
    membership = membership_repo.get_membership_for_user(db=ctx.db, user_id=ctx.user.id)
    if membership is None:
        raise NotFoundError(detail="Household not found")
    return membership.household_id


def get_membership_repository() -> MembershipRepository:
    return MembershipRepository()


@router.post("/generate", response_model=NamedQueryGenerateResponse)
def generate_named_query(
    request: NamedQueryGenerateRequest,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryGenerationService = Depends(get_named_query_generation_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        result = service.generate(
            db=ctx.db,
            household_id=household_id,
            messages=request.messages,
        )
        ctx.db.commit()
    except InternalError as exc:
        ctx.db.commit()
        logger.warning(
            "Named Query generation provider failure for household %s: %s",
            household_id,
            exc.detail,
        )
        return _provider_failure_response(exc.detail)
    except Exception:
        ctx.db.rollback()
        raise
    return result


@router.post("/preview", response_model=NamedQueryDataResponse)
def preview_named_query(
    request: NamedQueryPreviewRequest,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        result = service.preview(
            db=ctx.db,
            household_id=household_id,
            sql_query=request.sql_query,
            transaction_preview_filters=request.transaction_preview_filters,
        )
        ctx.db.rollback()
    except Exception:
        ctx.db.rollback()
        raise
    return result


@router.post("", response_model=NamedQueryResponse, status_code=status.HTTP_201_CREATED)
def create_named_query(
    request: NamedQueryCreateRequest,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        nq = service.create(
            db=ctx.db,
            household_id=household_id,
            name=request.name,
            sql_query=request.sql_query,
            chart_type=request.chart_type,
        )
        ctx.db.commit()
        ctx.db.refresh(nq)
    except Exception:
        ctx.db.rollback()
        raise
    return nq


@router.get("", response_model=list[NamedQueryResponse])
def list_named_queries(
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    return service.list_for_household(db=ctx.db, household_id=household_id)


@router.get("/{named_query_id}/data", response_model=NamedQueryDataResponse)
def get_named_query_data(
    named_query_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        result = service.get_data(db=ctx.db, household_id=household_id, named_query_id=named_query_id)
        ctx.db.rollback()
    except Exception:
        ctx.db.rollback()
        raise
    return result


@router.patch("/{named_query_id}", response_model=NamedQueryResponse)
def patch_named_query(
    named_query_id: UUID,
    request: NamedQueryPatchRequest,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        nq = service.patch(
            db=ctx.db,
            household_id=household_id,
            named_query_id=named_query_id,
            name=request.name,
            sql_query=request.sql_query,
            chart_type=request.chart_type,
        )
        ctx.db.commit()
        ctx.db.refresh(nq)
    except Exception:
        ctx.db.rollback()
        raise
    return nq


@router.delete("/{named_query_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_named_query(
    named_query_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    service: NamedQueryService = Depends(get_named_query_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
):
    household_id = _resolve_household_id(ctx, membership_repo)
    try:
        service.delete(db=ctx.db, household_id=household_id, named_query_id=named_query_id)
        ctx.db.commit()
    except Exception:
        ctx.db.rollback()
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)
