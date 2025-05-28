from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.business import UVal
from app.business.user.user_admin import AdminService
from app.dependencies import get_db, get_current_admin
from app.models import User
from app.schemas import UserPublicResponse
from app.schemas.admin import UpdateUserStatus

router = APIRouter(tags=["Admin"])


@router.get("/", response_model=UserPublicResponse)
def admin_root(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Get information about your admin profile.
    :param db: database session
    :param admin: your profile as User object
    :return: information about your admin profile
    """
    return admin


@router.put("/users/status", response_model=None)
def update_user_status(update_data: UpdateUserStatus, admin=Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    Updates the provided user's status to active (approve pending user or unblock user), blocked (block user) or deactivated (deactivate user).
    :param update_data: user (username or id), status and (optionally) reason for status change.
    :param admin: the currently logged in admin user (automatically fetched)
    :param db: database sessions (automatically fetched)
    :return: the updated user object
    """
    return AdminService.update_user_status(db, update_data, admin)
