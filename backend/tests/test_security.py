import pytest
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.api.auth import hash_password, verify_password, verify_and_update_password, create_access_token

client = TestClient(app)

def test_bcrypt_password_hashing():
    """Verify password hashing uses bcrypt with $2b$ prefix and dynamic salting."""
    plain = "SecureP@ssw0rd2026!"
    hashed1 = hash_password(plain)
    hashed2 = hash_password(plain)

    # Must start with bcrypt prefix
    assert hashed1.startswith("$2b$") or hashed1.startswith("$2a$")
    # Dynamic salt means two hashes of same password must be distinct
    assert hashed1 != hashed2
    # Verification must succeed
    assert verify_password(plain, hashed1) is True
    assert verify_password("WrongPassword", hashed1) is False


def test_legacy_sha256_password_migration():
    """Verify legacy SHA-256 hashes are verified and automatically upgraded to bcrypt upon login."""
    db = SessionLocal()
    try:
        email = "legacy_user@nutritwin.ai"
        plain_pw = "LegacySecret123!"
        legacy_hash = hashlib.sha256(plain_pw.encode()).hexdigest()

        # Delete existing if any
        db.query(User).filter(User.email == email).delete()
        db.commit()

        # Create user with legacy SHA-256 hash
        user = User(
            email=email,
            hashed_password=legacy_hash,
            full_name="Legacy User",
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.hashed_password == legacy_hash

        # Perform login which triggers verify_and_update_password
        res = client.post("/api/v1/auth/login", json={"email": email, "password": plain_pw})
        assert res.status_code == 200

        # Refresh from DB and verify hash was upgraded to bcrypt
        db.refresh(user)
        assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")
    finally:
        db.close()


def test_no_hardcoded_admin_registration():
    """Verify registering with admin@nutritwin.ai does NOT grant admin privileges."""
    email = "admin@nutritwin.ai"
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "AdminPassword123!",
        "full_name": "Fake Admin"
    })
    assert res.status_code == 200

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        # Must be False, not True
        assert user.is_admin is False
    finally:
        db.close()


def test_role_based_admin_authorization():
    """Verify non-admin users are blocked with 403 Forbidden from admin endpoints."""
    from app.api.auth import get_current_user
    
    # 1. Regular non-admin user must be rejected with 403 Forbidden
    mock_normal_user = User(id=9991, email="normal@test.com", is_admin=False)
    app.dependency_overrides[get_current_user] = lambda: mock_normal_user
    try:
        res_normal = client.get("/api/v1/admin/models/metrics")
        assert res_normal.status_code == 403
        assert "Administrative privileges required" in res_normal.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    # 2. Granted admin user must be accepted with 200 OK
    mock_admin_user = User(id=9992, email="admin@test.com", is_admin=True)
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        res_admin = client.get("/api/v1/admin/models/metrics")
        assert res_admin.status_code == 200
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_cors_restricted_origins():
    """Verify CORS middleware restricts origins to configured trusted list."""
    # Request from allowed origin
    headers_allowed = {"Origin": "http://localhost:3000"}
    res_allowed = client.options("/api/v1/auth/login", headers=headers_allowed)
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    # Request from unauthorized origin
    headers_untrusted = {"Origin": "http://malicious-attacker-site.com"}
    res_untrusted = client.options("/api/v1/auth/login", headers=headers_untrusted)
    assert res_untrusted.headers.get("access-control-allow-origin") != "http://malicious-attacker-site.com"


def test_sql_injection_resilience():
    """Verify SQL injection payloads in input fields are sanitized safely via ORM."""
    sqli_payload = "test@nutritwin.ai' OR '1'='1"
    res = client.post("/api/v1/auth/login", json={"email": sqli_payload, "password": "password"})
    assert res.status_code == 401
