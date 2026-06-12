from __future__ import annotations

import hashlib
import hmac
import secrets
from pathlib import Path

from src.auth.schemas import (
    ALL_ROLES,
    CLIENT_ROLES,
    INTERNAL_ROLES,
    AuthSession,
    AuthUser,
    ClientAccount,
    ClientUserLink,
    Identity,
    ProjectAccess,
    client_id_for,
    new_session_id,
    now_iso,
    session_expires_at,
    user_id_for,
)
from src.auth.storage import (
    delete_session,
    load_all_users,
    load_client_users_for_user,
    load_project_access_for_user,
    load_session,
    load_user,
    load_user_by_email,
    upsert_client,
    upsert_client_user,
    upsert_project_access,
    upsert_session,
    upsert_user,
)
from src.schemas import stable_id


PASSWORD_ITERATIONS = 240_000


def users_exist(db_path: Path) -> bool:
    return bool(load_all_users(db_path))


def create_user(
    db_path: Path,
    email: str,
    password: str,
    name: str = "",
    user_type: str = "internal",
    role: str = "viewer",
    client_id: str = "",
) -> AuthUser:
    normalized = email.strip().lower()
    if not normalized:
        raise ValueError("email is required")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    if user_type not in {"internal", "client"}:
        raise ValueError("invalid user_type")
    if role not in ALL_ROLES:
        raise ValueError("invalid role")
    if user_type == "internal" and role not in INTERNAL_ROLES:
        raise ValueError("invalid internal role")
    if user_type == "client" and role not in CLIENT_ROLES:
        raise ValueError("invalid client role")
    existing = load_user_by_email(db_path, normalized)
    if existing:
        raise ValueError("email already exists")
    user = AuthUser(
        user_id=user_id_for(normalized),
        email=normalized,
        name=name.strip() or normalized.split("@")[0],
        password_hash=hash_password(password),
        user_type=user_type,
        role=role,
        client_id=client_id,
        external_user_id=user_id_for(normalized),
    )
    upsert_user(db_path, user)
    return user


def update_user(
    db_path: Path,
    user_id: str,
    name: str | None = None,
    role: str | None = None,
    status: str | None = None,
    client_id: str | None = None,
) -> AuthUser:
    user = load_user(db_path, user_id)
    if user is None:
        raise ValueError("user not found")
    if name is not None:
        user.name = name.strip() or user.name
    if role is not None:
        if role not in ALL_ROLES:
            raise ValueError("invalid role")
        if user.user_type == "internal" and role not in INTERNAL_ROLES:
            raise ValueError("invalid internal role")
        if user.user_type == "client" and role not in CLIENT_ROLES:
            raise ValueError("invalid client role")
        user.role = role
    if status is not None:
        if status not in {"active", "disabled"}:
            raise ValueError("invalid status")
        user.status = status
    if client_id is not None:
        user.client_id = client_id
    user.updated_at = now_iso()
    upsert_user(db_path, user)
    return user


def reset_user_password(db_path: Path, user_id: str, password: str) -> AuthUser:
    user = load_user(db_path, user_id)
    if user is None:
        raise ValueError("user not found")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    user.password_hash = hash_password(password)
    user.updated_at = now_iso()
    upsert_user(db_path, user)
    return user


def authenticate_user(db_path: Path, email: str, password: str) -> AuthUser | None:
    user = load_user_by_email(db_path, email)
    if not user or user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = now_iso()
    user.updated_at = now_iso()
    upsert_user(db_path, user)
    return user


def create_session(db_path: Path, user: AuthUser, days: int = 14) -> AuthSession:
    session = AuthSession(session_id=new_session_id(), user_id=user.user_id, expires_at=session_expires_at(days))
    upsert_session(db_path, session)
    return session


def resolve_identity(db_path: Path, session_id: str) -> Identity | None:
    if not session_id:
        return None
    session = load_session(db_path, session_id)
    if session is None:
        return None
    if session.expired():
        delete_session(db_path, session_id)
        return None
    user = load_user(db_path, session.user_id)
    if user is None or user.status != "active":
        return None
    session.last_seen_at = now_iso()
    upsert_session(db_path, session)
    client_ids = [link.client_id for link in load_client_users_for_user(db_path, user.user_id)]
    if user.client_id and user.client_id not in client_ids:
        client_ids.append(user.client_id)
    return Identity(user=user, client_ids=client_ids, provider=user.identity_provider)


def logout_session(db_path: Path, session_id: str) -> None:
    if session_id:
        delete_session(db_path, session_id)


def create_client_account(db_path: Path, name: str, company: str = "", created_by: str = "") -> ClientAccount:
    client = ClientAccount(client_id=client_id_for(name), name=name.strip(), company=company.strip(), created_by=created_by)
    if not client.name:
        raise ValueError("client name is required")
    upsert_client(db_path, client)
    return client


def link_client_user(db_path: Path, client_id: str, user_id: str, role: str = "client_viewer") -> ClientUserLink:
    if role not in CLIENT_ROLES:
        raise ValueError("invalid client role")
    link = ClientUserLink(link_id=stable_id(client_id, user_id, prefix="client_user"), client_id=client_id, user_id=user_id, role=role)
    upsert_client_user(db_path, link)
    user = load_user(db_path, user_id)
    if user and user.user_type == "client" and not user.client_id:
        user.client_id = client_id
        user.role = role
        user.updated_at = now_iso()
        upsert_user(db_path, user)
    return link


def grant_project_access(
    db_path: Path,
    user_id: str,
    client_id: str = "",
    proposal_id: str = "",
    campaign_id: str = "",
    permissions: list[str] | None = None,
    created_by: str = "",
) -> ProjectAccess:
    if not user_id:
        raise ValueError("user_id is required")
    access = ProjectAccess(
        access_id=stable_id(user_id, client_id, proposal_id, campaign_id, prefix="access"),
        user_id=user_id,
        client_id=client_id,
        proposal_id=proposal_id,
        campaign_id=campaign_id,
        permissions=permissions or ["view"],
        created_by=created_by,
    )
    upsert_project_access(db_path, access)
    return access


def can_access_proposal(db_path: Path, identity: Identity | None, proposal_client_id: str, proposal_id: str, action: str = "view") -> bool:
    if identity is None:
        return False
    user = identity.user
    if user.user_type == "internal":
        return user.role in INTERNAL_ROLES
    if proposal_client_id and proposal_client_id in identity.client_ids:
        return True
    for access in load_project_access_for_user(db_path, user.user_id):
        if access.proposal_id == proposal_id and action in access.permissions:
            return True
    return False


def role_can(user: AuthUser, action: str) -> bool:
    if user.user_type == "internal":
        if user.role == "admin":
            return True
        if user.role in {"strategist", "media_buyer"}:
            return action in {"read", "write", "campaign", "proposal", "project_run"}
        if user.role == "viewer":
            return action == "read"
    if user.user_type == "client":
        if user.role in {"client_owner", "client_reviewer"}:
            return action in {"client_read", "client_comment"}
        if user.role == "client_viewer":
            return action == "client_read"
    return False


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False
