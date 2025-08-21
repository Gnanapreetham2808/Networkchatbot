"""
Firebase authentication & role permissions for Django REST Framework.

Usage:
 - Provide a Firebase ID token in Authorization header: 'Bearer <token>'.
 - Admin detection: email present in ADMIN_EMAILS (comma-separated) env var OR custom claim 'admin': True.
 - Non-admin users may access only whitelisted user endpoints (e.g. network command API) while admins can access everything.

Environment variables:
 FIREBASE_CREDENTIALS: Path to service account JSON. If omitted, will attempt default credentials.
 ADMIN_EMAILS: Comma-separated list of admin emails.
"""

from __future__ import annotations
import os
import threading
from typing import Optional, Tuple
from django.utils.functional import cached_property
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

# -------------------
# Firebase Init Logic
# -------------------
_firebase_app_lock = threading.Lock()
_firebase_initialized = False

def _init_firebase_once():
    """Initialize Firebase Admin SDK only once for the lifetime of the process."""
    global _firebase_initialized
    if _firebase_initialized:
        return
    with _firebase_app_lock:
        if _firebase_initialized:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials
            cred_path = os.getenv("FIREBASE_CREDENTIALS")

            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"[firebase] Initialized with service account: {cred_path}")
            else:
                firebase_admin.initialize_app()
                print("[firebase] Initialized with default credentials")

        except Exception as e:
            print("[firebase] Initialization failed:", e)
        _firebase_initialized = True


# -------------------
# User Wrapper
# -------------------
class FirebaseUser:
    def __init__(self, uid: str, email: Optional[str], claims: dict):
        self.uid = uid
        self.email = email
        self.claims = claims or {}

    @cached_property
    def is_admin(self) -> bool:
        admin_emails = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(',') if e.strip()}
        if self.email and self.email.lower() in admin_emails:
            return True
        return self.claims.get("admin") is True

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"FirebaseUser<{self.uid}>"


# -------------------
# Authentication Class
# -------------------
class FirebaseAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request) -> Optional[Tuple[FirebaseUser, None]]:
        _init_firebase_once()

        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] No Authorization header present")
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] Bad auth header format:", auth_header)
            raise exceptions.AuthenticationFailed("Invalid Authorization header format. Expected: Bearer <token>")

        token = parts[1]
        try:
            import firebase_admin
            from firebase_admin import auth as fb_auth
            decoded = fb_auth.verify_id_token(token)
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] Token verified uid=", decoded.get("uid"), "email=", decoded.get("email"))
        except Exception as e:
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] Token verification failed:", e)
            raise exceptions.AuthenticationFailed(f"Invalid Firebase token: {e}")

        user = FirebaseUser(uid=decoded.get("uid"), email=decoded.get("email"), claims=decoded)
        return (user, None)


# -------------------
# Permissions
# -------------------
class IsFirebaseAuthenticated(BasePermission):
    """Allow access only to Firebase-authenticated users."""
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] IsFirebaseAuthenticated: missing/anon user -> 401")
            raise NotAuthenticated("Missing Firebase token. Provide Authorization: Bearer <ID_TOKEN> or disable auth (DISABLE_AUTH=1).")
        return True


class IsAdminOrChatUser(BasePermission):
    """Admins have full access; normal users can only hit allowed endpoints."""
    USER_ALLOWED_PATHS = {
        "/api/nlp/network-command/",
        "/api/nlp/auth/me/"
    }

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        path_norm = request.path if request.path.endswith("/") else f"{request.path}/"
        if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
            print(f"[auth] has_permission path={path_norm} user={getattr(user,'email',None)} admin={getattr(user,'is_admin',None)} auth={getattr(user,'is_authenticated',None)}")

        # Optional development bypass
        if os.getenv("BYPASS_AUTH_NETWORK", "0") == "1" and path_norm in self.USER_ALLOWED_PATHS:
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] BYPASS_AUTH_NETWORK=1 allowing access to", path_norm)
            return True

        if not user or not getattr(user, "is_authenticated", False):
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] NotAuthenticated path=", path_norm)
            raise NotAuthenticated("Missing or invalid Firebase token. Add Authorization: Bearer <ID_TOKEN> header.")

        if getattr(user, "is_admin", False):
            if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
                print("[auth] Admin granted path=", path_norm, "email=", getattr(user,'email',None))
            return True

        if path_norm in self.USER_ALLOWED_PATHS:
            return True

        if os.getenv("FIREBASE_AUTH_DEBUG") == "1":
            print("[auth] PermissionDenied path=", path_norm, "allowed=", sorted(self.USER_ALLOWED_PATHS))
        raise PermissionDenied("You are authenticated but not authorized for this endpoint.")
