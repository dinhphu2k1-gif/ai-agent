"""Security helpers; bearer validation is implemented via IAM (Epic 4 — see `app/iam/`)."""


def placeholder_auth_note() -> str:
    return "Bearer tokens are validated by the IAM client (Epic 4)."
