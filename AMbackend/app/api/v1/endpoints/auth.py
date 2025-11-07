"""Authentication API endpoints - Firebase based"""

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import User as UserSchema, FirebaseConfig


router = APIRouter()


@router.get("/config", response_model=FirebaseConfig)
async def get_firebase_config():
    """
    Get Firebase client configuration

    Returns:
        Firebase configuration for frontend
    """
    from app.core.config import settings

    return FirebaseConfig(
        apiKey=settings.FIREBASE_API_KEY,
        authDomain=settings.FIREBASE_AUTH_DOMAIN,
        projectId=settings.FIREBASE_PROJECT_ID,
        storageBucket=settings.FIREBASE_STORAGE_BUCKET,
        messagingSenderId=settings.FIREBASE_MESSAGING_SENDER_ID,
        appId=settings.FIREBASE_APP_ID,
        measurementId=settings.FIREBASE_MEASUREMENT_ID,
    )


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal)
    Firebase handles token invalidation on client side

    Returns:
        Success message
    """
    return {"message": "Successfully logged out. Please remove Firebase token on client."}
