"""Row-filter validation and column-mask preview for Add Permission wizard (Phase 5)."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.column_mask_engine import mask_value, normalize_row_filter_expression
from app.repositories.permission_repo import PermissionRepository
from app.repositories.resource_repo import ResourceRepository
from app.schemas.admin_contract import (
    ColumnMaskPreviewResult,
    PermissionGrantBody,
    ResourcePathSegment,
    RowFilterValidateResult,
)
from app.services.permission_grant_service import (
    GrantValidationError,
    PermissionGrantService,
)

_FORBIDDEN_ROW_FILTER_CHARS = (";",)


class PermissionValidationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._rr = ResourceRepository(session)
        self._pr = PermissionRepository(session)
        self._grant = PermissionGrantService(session, self._rr, self._pr)

    def validate_row_filter(
        self,
        resource_path: list[ResourcePathSegment],
        condition_expression: str,
    ) -> RowFilterValidateResult:
        errors: list[str] = []
        expr = (condition_expression or "").strip()

        if not expr:
            errors.append("conditionExpression must not be empty")
            return RowFilterValidateResult(
                valid=False,
                normalized_expression=None,
                errors=errors,
            )

        for ch in _FORBIDDEN_ROW_FILTER_CHARS:
            if ch in expr:
                errors.append(f"conditionExpression must not contain '{ch}'")

        normalized = normalize_row_filter_expression(expr)

        if resource_path:
            leaf = resource_path[-1].type.strip().lower()
            if leaf != "table":
                errors.append("rowFilter validation requires a TABLE resourcePath")
            else:
                body = PermissionGrantBody(
                    resource_path=resource_path,
                    resource_type="TABLE",
                    actions=["SELECT"],
                    effect="ALLOW",
                    row_filter={
                        "enabled": True,
                        "conditionExpression": normalized,
                    },
                )
                try:
                    self._grant.validate_grant(body)
                except GrantValidationError as exc:
                    errors.append(exc.message)

        if errors:
            return RowFilterValidateResult(
                valid=False,
                normalized_expression=normalized,
                errors=errors,
            )

        return RowFilterValidateResult(
            valid=True,
            normalized_expression=normalized,
            errors=[],
        )

    def preview_column_mask(
        self,
        mask_type: str,
        mask_pattern: str | None,
        sample_value: str,
    ) -> ColumnMaskPreviewResult:
        kind = (mask_type or "PARTIAL").strip().upper()
        if kind == "PARTIAL" and not (mask_pattern or "").strip():
            raise ValueError("maskPattern is required for PARTIAL columnMask")
        if kind not in ("FULL", "NULLIFY", "HASH", "PARTIAL"):
            raise ValueError(f"Unsupported maskType: {mask_type}")

        masked = mask_value(
            sample_value or "",
            kind,
            mask_pattern,
            hash_salt=get_settings().masking_hash_salt,
            for_preview=True,
        )
        algorithm = {
            "FULL": "FULL",
            "NULLIFY": "NULLIFY",
            "HASH": "HASH",
            "PARTIAL": "PARTIAL_PATTERN",
        }[kind]
        return ColumnMaskPreviewResult(
            masked_value=str(masked),
            algorithm=algorithm,
        )
