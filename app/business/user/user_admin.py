from typing import Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.business import UVal, NService, NType
from app.models import User, UStatus
from app.schemas.admin import UpdateUserStatus


class AdminService:

    @classmethod
    def verify_admin(cls, db: Session, admin: User | str) -> bool:
        """
        Verify if a user is an admin
        :param db: database session
        :param admin: User's account to verify
        :return bool: True if the user is an admin, False otherwise
        """
        if isinstance(admin, str):
            admin = UVal.find_user_with_or_raise_exception("username", admin, db)

        if not admin.admin:
            raise HTTPException(status_code=403, detail="You do not have permission to approve users")

        return True

    @classmethod
    def update_user_status(cls, db: Session, update_data: UpdateUserStatus, admin: User) -> Dict:
        """
        Approve a pending user account
        :param db: database session
        :param user: Pending User object, username or id
        :param admin: Admin's user object
        """
        cls.verify_admin(db, admin)
        user = update_data.user

        if isinstance(user, str):
            user = UVal.find_user_with_or_raise_exception("username", user, db)
        elif isinstance(user, int):
            user = UVal.find_user_with_or_raise_exception("id", user, db)

        match update_data.status:
            case UStatus.ACTIVE.value:
                if user.status == UStatus.ACTIVE:
                    return {"user": user, "message": "User is already with status " + UStatus.ACTIVE.value}
                if user.status == UStatus.PENDING and len(user.cards) == 0:
                    raise HTTPException(status_code=400,
                                        detail="Pending users must have a debit or credit card to be approved")

                user.status = UStatus.ACTIVE
                NService.notify(user, {
                    "title": "Your account has been activated",
                    "body": f"Hello, {user.username}! Your account has been activated and is ready for use.",
                    "type": NType.IMPORTANT
                })

                db.commit()
                db.refresh(user)
                return {"user": user, "message": "User approved successfully"}

            case UStatus.BLOCKED.value:
                if user.status == UStatus.BLOCKED:
                    return {"user": user, "message": "User is already blocked"}
                else:
                    user.status = UStatus.BLOCKED
                    reason = update_data.reason
                    NService.notify(user, {
                        "title": "Your account has been blocked",
                        "body": f"Hello, {user.username}! Your account has been blocked {"due to " + reason if reason else ""}. If you would like to appeal our decision, please reply to this email.",
                        "type": NType.IMPORTANT
                    })

                    db.commit()
                    db.refresh(user)
                    return {"user": user, "message": "User blocked successfully"}

            case UStatus.DEACTIVATED.value:
                if user.status == UStatus.DEACTIVATED:
                    return {"user": user, "message": "User is already deactivated"}
                else:
                    user.status = UStatus.DEACTIVATED
                    NService.notify(user, {
                        "title": "Your account has been deactivated",
                        "body": f"Hello, {user.username}! Your account has been deactivated. If you would like to reactivate it, simply log in again.",
                        "type": NType.IMPORTANT
                    })

                    db.commit()
                    db.refresh(user)
                    return {"user": user, "message": "User deactivated successfully"}

            case _:
                err_message = f"Invalid user status provided, available options include '{UStatus.ACTIVE}', '{UStatus.BLOCKED}', and '{UStatus.DEACTIVATED}'"
                raise HTTPException(status_code=400, detail=err_message)

    @classmethod
    def block(cls, db: Session, user: User | str, reason: str, admin: User) -> User:
        """
        Block a user account
        :param db: database session
        :param user: User object or username
        :param reason: the reason for the account block
        :param admin: Admin's user object
        """
        cls.verify_admin(db, admin)

        if isinstance(user, str):
            user = UVal.find_user_with_or_raise_exception("username", user, db)

        db.refresh(user)

        return user
