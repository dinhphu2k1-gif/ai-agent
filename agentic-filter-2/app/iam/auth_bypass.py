from __future__ import annotations

import uuid

from app.core.config import Settings
from app.iam.schemas import IamUserClaims


def claims_from_auth_bypass(settings: Settings) -> IamUserClaims:
    return IamUserClaims(
        user_id=uuid.UUID(settings.auth_bypass_user_id),
        username=settings.auth_bypass_username,
        email=settings.auth_bypass_email,
        is_active=True,
    )
