from __future__ import annotations

import anyio
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.cache.redis_client import UserContextCache
from app.core.config import get_settings
from app.core.errors import ErrorCode, error_response
from app.iam.auth_bypass import claims_from_auth_bypass
from app.iam.client import IamHttpClient, IamInvalidTokenError, IamUnavailableError
from app.schemas.runtime import (
    AuthorizeRequest,
    ColumnMaskPolicyOut,
    PolicyDecisionOut,
    UserContextResponse,
)
from app.services.audit_service import record_runtime_access
from app.services.authorization_service import resolve_access
from app.services.permission_resolver import DecisionType
from app.services.row_filter_service import combine_row_filters
from app.services.user_context_service import UserContext, build_user_context

router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])


def _get_iam(request: Request) -> IamHttpClient:
    return request.app.state.iam_client


def _get_cache(request: Request) -> UserContextCache:
    return request.app.state.user_context_cache


async def _user_context_from_bearer(
    request: Request,
    authorization: str | None,
    db: Session,
) -> UserContext | JSONResponse:
    if not authorization or not authorization.lower().startswith("bearer "):
        return error_response(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Missing bearer token",
            detail=None,
        )
    parts = authorization.split(None, 1)
    token = parts[1].strip() if len(parts) > 1 else ""
    if not token:
        return error_response(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Missing bearer token",
            detail=None,
        )

    cache = _get_cache(request)
    cfg = get_settings()

    def _work() -> UserContext:
        if cfg.auth_bypass_enabled:
            claims = claims_from_auth_bypass(cfg)
        else:
            claims = _get_iam(request).validate_bearer_token(token)
        return build_user_context(db, claims, cache, cfg.user_context_ttl_seconds)

    try:
        ctx = await anyio.to_thread.run_sync(_work)
    except IamInvalidTokenError:
        return error_response(
            status_code=401,
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired token",
            detail=None,
        )
    except IamUnavailableError as e:
        msg = str(e).lower()
        if "timed out" in msg:
            return error_response(
                status_code=504,
                code=ErrorCode.GATEWAY_TIMEOUT,
                message="IAM request timed out",
                detail=None,
            )
        return error_response(
            status_code=502,
            code=ErrorCode.BAD_GATEWAY,
            message="IAM unavailable",
            detail=None,
        )

    if not ctx.is_active:
        return error_response(
            status_code=403,
            code=ErrorCode.FORBIDDEN,
            message="User is inactive",
            detail=None,
        )

    return ctx


@router.get("/user-context", response_model=None)
async def get_user_context(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserContextResponse | JSONResponse:
    ctx = await _user_context_from_bearer(request, authorization, db)
    if isinstance(ctx, JSONResponse):
        return ctx
    return UserContextResponse(
        user_id=ctx.user_id,
        username=ctx.username,
        email=ctx.email,
        is_active=ctx.is_active,
        group_ids=ctx.group_ids,
        direct_role_ids=ctx.direct_role_ids,
        inherited_role_ids=ctx.inherited_role_ids,
    )


@router.post("/authorize", response_model=None)
async def authorize(
    request: Request,
    body: AuthorizeRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> PolicyDecisionOut | JSONResponse:
    ctx = await _user_context_from_bearer(request, authorization, db)
    if isinstance(ctx, JSONResponse):
        return ctx

    cfg = get_settings()
    cache = _get_cache(request)

    def _resolve():
        return resolve_access(
            db,
            ctx,
            body.resource_id,
            body.action,
            cache,
            cfg.permission_snapshot_ttl_seconds,
        )

    decision = await anyio.to_thread.run_sync(_resolve)
    rid = getattr(request.state, "request_id", None)
    result = "allow" if decision.decision != DecisionType.DENY else "deny"
    record_runtime_access(
        db,
        user_id=ctx.user_id,
        resource_id=body.resource_id,
        action="AUTHORIZE",
        result=result,
        decision=decision.decision.value,
        request_id=rid,
    )
    combined = combine_row_filters(decision.row_filter_exprs)
    return PolicyDecisionOut(
        decision=decision.decision.value,
        row_filter_exprs=list(decision.row_filter_exprs),
        column_masks=[
            ColumnMaskPolicyOut(
                permission_id=m.permission_id,
                mask_type=m.mask_type,
                mask_pattern=m.mask_pattern,
            )
            for m in decision.column_masks
        ],
        combined_row_filter=combined,
        deny_reason=decision.deny_reason,
    )
