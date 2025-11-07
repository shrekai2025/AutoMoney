"""Firebase Admin SDK initialization and utilities"""

import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import UserRecord

from app.core.config import settings


# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK

    Returns:
        Firebase app instance
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        # Try to use service account if path is provided
        if settings.FIREBASE_SERVICE_ACCOUNT_PATH and os.path.exists(
            settings.FIREBASE_SERVICE_ACCOUNT_PATH
        ):
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase initialized with service account")
        else:
            # Use default credentials or project ID
            _firebase_app = firebase_admin.initialize_app(
                options={"projectId": settings.FIREBASE_PROJECT_ID}
            )
            print(f"Firebase initialized with project ID: {settings.FIREBASE_PROJECT_ID}")

    except ValueError as e:
        # App already initialized
        if "already exists" in str(e):
            _firebase_app = firebase_admin.get_app()
        else:
            raise

    return _firebase_app


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token claims or None if invalid
    """
    try:
        # Ensure Firebase is initialized
        if _firebase_app is None:
            initialize_firebase()

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token

    except auth.InvalidIdTokenError:
        print("Invalid Firebase ID token")
        return None
    except auth.ExpiredIdTokenError:
        print("Expired Firebase ID token")
        return None
    except Exception as e:
        print(f"Error verifying Firebase token: {e}")
        return None


def get_firebase_user(uid: str) -> Optional[UserRecord]:
    """
    Get Firebase user by UID

    Args:
        uid: Firebase user UID

    Returns:
        Firebase UserRecord or None
    """
    try:
        if _firebase_app is None:
            initialize_firebase()

        user = auth.get_user(uid)
        return user

    except auth.UserNotFoundError:
        print(f"User {uid} not found in Firebase")
        return None
    except Exception as e:
        print(f"Error getting Firebase user: {e}")
        return None


def create_custom_token(uid: str, additional_claims: Optional[dict] = None) -> str:
    """
    Create a custom Firebase token

    Args:
        uid: User UID
        additional_claims: Additional claims to include in token

    Returns:
        Custom token string
    """
    try:
        if _firebase_app is None:
            initialize_firebase()

        custom_token = auth.create_custom_token(uid, additional_claims)
        return custom_token.decode("utf-8")

    except Exception as e:
        print(f"Error creating custom token: {e}")
        raise
