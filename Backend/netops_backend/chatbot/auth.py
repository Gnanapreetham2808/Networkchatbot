"""Firebase authentication & role permissions for Django REST Framework.

Usage:
 - Provide a Firebase ID token in Authorization header: 'Bearer <token>'.
 - Admin detection: email present in ADMIN_EMAILS (comma-separated) env var OR custom claim 'admin': True.
 - Non-admin users may access only whitelisted user endpoints (e.g. network command API) while admins can access everything.

Environment variables:
 FIREBASE_CREDENTIALS: Path to service account JSON. If omitted, will attempt default credentials.
 ADMIN_EMAILS: Comma-separated list of admin emails.
"""
from __future__ import annotations
import os, threading
from typing import Optional, Tuple
from django.utils.functional import cached_property
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from rest_framework.permissions import BasePermission

_firebase_app_lock = threading.Lock()
_firebase_initialized = False

def _init_firebase_once():
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
            else:
                firebase_admin.initialize_app()
            print("[firebase] Initialized Firebase Admin SDK")
        except Exception as e:
            print("[firebase] Initialization failed (auth will reject tokens):", e)
        _firebase_initialized = True

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
        if self.claims.get("admin") is True:
            return True
        return False
    @property
    def is_authenticated(self):
        return True
    def __str__(self):
        return f"FirebaseUser<{self.uid}>"

class FirebaseAuthentication(BaseAuthentication):
    keyword = "Bearer"
    def authenticate(self, request) -> Optional[Tuple[FirebaseUser, None]]:
        _init_firebase_once()
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid Authorization header format. Expected: Bearer <token>")
        token = parts[1]
        try:
            import firebase_admin
            from firebase_admin import auth as fb_auth
            decoded = fb_auth.verify_id_token(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Invalid Firebase token: {e}")
        user = FirebaseUser(uid=decoded.get('uid'), email=decoded.get('email'), claims=decoded)
        return (user, None)

class IsFirebaseAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False))

class IsAdminOrChatUser(BasePermission):
    USER_ALLOWED_PATHS = {"/api/nlp/network-command/", "/api/nlp/auth/me/"}
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_admin', False):
            return True
        path = request.path
        if not path.endswith('/'):
            path = path + '/'
        return path in self.USER_ALLOWED_PATHS
