import os

from fastapi import HTTPException, status


def get_auth_mode() -> str:
    return os.getenv("AUTH_MODE", "open").strip().lower()


def get_access_contact() -> str:
    return os.getenv("ACCESS_CONTACT", "Roy Zhao").strip() or "Roy Zhao"


def get_authorized_emails() -> set[str]:
    raw_value = os.getenv("AUTHORIZED_EMAILS", "")
    return {
        email.strip().lower()
        for email in raw_value.split(",")
        if email.strip()
    }


def is_restricted_auth_mode() -> bool:
    return get_auth_mode() == "restricted"


def is_authorized_email(email: str | None) -> bool:
    if not is_restricted_auth_mode():
        return True

    if not email:
        return False

    return email.strip().lower() in get_authorized_emails()


def restricted_access_detail() -> str:
    return (
        "Access to this Lantern deployment is limited to approved email addresses. "
        f"Contact {get_access_contact()} for access."
    )


def ensure_identity_authorized(firebase_identity: dict) -> None:
    email = firebase_identity.get("email")

    if is_authorized_email(email):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=restricted_access_detail(),
    )
