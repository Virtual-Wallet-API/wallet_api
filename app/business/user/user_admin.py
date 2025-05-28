from datetime import datetime
from typing import Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.business import UVal, NService, NType
from app.models import User, UStatus, Transaction
from app.schemas.admin import UpdateUserStatus, AdminUserResponse, AdminTransactionResponse


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

    @classmethod
    def get_all_users(cls, db: Session, admin: User, search_data: Dict) -> Dict:
        """
        Returns a list of all users in the database with pagination and the option to search by username, email or phone number.
        :param db: database session
        :param admin: currently logged in admin user
        :param search_data: the search data provided by the client
        :return: pagination data with a list of all users per per the criterion
        """
        # Pagination setup
        page = search_data.get("page", 0)
        page = page - 1 if page > 0 else 0
        limit = search_data.get("limit", 30)
        limit = limit if 10 <= limit <= 100 else 30
        offset = page * limit

        # Search setup
        search_by = search_data.get("search_by")

        if not search_by:
            users = db.query(User).offset(offset).limit(limit).all()
        else:
            query = search_data.get("search_query", "")

            match search_by:
                case "username":
                    users = (db.query(User)
                             .filter(User.username.ilike(f"%{query}%"))
                             .offset(offset).limit(limit).all())

                case "email":
                    users = (db.query(User)
                             .filter(User.email.ilike(f"%{query}%"))
                             .offset(offset).limit(limit).all())

                case "phone":
                    users = (db.query(User)
                             .filter(User.phone_number.ilike(f"%{query}%"))
                             .offset(offset).limit(limit).all())

                case _:
                    raise HTTPException(status_code=400,
                                        detail=f"Invalid search_by parameter provided: {search_by}")

        # Response setup
        response = {"results_per_page": limit}

        if not users:
            response["users"] = []
            response["page"] = 0
            response["pages_with_matches"] = 0
            response["matching_records"] = 0
        else:
            response["users"] = [AdminUserResponse.model_validate(user) for user in users]
            response["page"] = page + 1
            response["pages_with_matches"] = len(users) // limit + 1 if len(users) % limit > 0 else len(users) // limit
            response["matching_records"] = len(users)

        return response

    @classmethod
    def get_user_transactions(cls, db: Session, admin: User, search_data: Dict) -> Dict:
        # User data setup
        user = UVal.find_user_with_or_raise_exception("id", search_data.get("user_id"), db)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {search_data.get("user_id")} not found")

        # Sort setup
        sort_by = search_data.get("order_by", "date_desc")
        print(sort_by)

        # Pagination setup
        page = search_data.get("page", 0)
        page = page - 1 if page > 0 else 0
        limit = search_data.get("limit", 30)
        limit = limit if 10 <= limit <= 100 else 30
        offset = page * limit

        # Search by setup
        search_by = search_data.get("search_by")

        query_transactions = user.get_transactions(db, order_by=sort_by, offset=offset, limit=limit)

        if not search_by:
            # transactions = db.query(User).offset(offset).limit(limit).all()
            transactions = query_transactions.all()
        else:
            query = search_data.get("search_query", "")
            transactions = []

            match search_by:
                case "period":
                    date_from, date_to = query.split("_")
                    try:
                        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

                        if date_to < date_from:
                            date_from, date_to = date_to, date_from
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date format provided")

                    # transactions = (user.transactions.filter(date_from <= Transaction.date <= date_to)
                    #                 .offset(offset).limit(limit).order_by(sort_filter).all())

                    transactions = user.get_transactions(db, date_from, date_to, sort_by, offset, limit).all()

                case "sender":
                    transactions = (query_transactions.filter(Transaction.sender_id == user.id)
                                    .offset(offset).limit(limit).all())

                case "receiver":
                    transactions = (query_transactions.filter(Transaction.receiver_id == user.id)
                                    .offset(offset).limit(limit).all())

                case "direction":
                    if query not in ("incoming", "outgoing"):
                        raise HTTPException(status_code=400,
                                            detail="Invalid direction provided, options are outgoing and incoming")

                    if query == "incoming":
                        transactions = (query_transactions.filter(Transaction.receiver_id == user.id)
                                        .offset(offset).limit(limit).all())
                    else:
                        transactions = (query_transactions.filter(Transaction.sender_id == user.id)
                                        .offset(offset).limit(limit).all())

                case _:
                    raise HTTPException(status_code=400, detail=f"Invalid search_query parameter provided: {search_by}")

        response = {
            "transactions": [AdminTransactionResponse.model_validate(t) for t in transactions],
            "results_per_page": limit
        }

        if len(transactions) == 0:
            response["page"] = 0
            response["pages_with_matches"] = 0
            response["matching_records"] = 0
        else:
            response["page"] = page + 1
            response["pages_with_matches"] = len(transactions) // limit + 1 if len(transactions) % limit > 0 else len(
                transactions) // limit
            response["matching_records"] = len(transactions)

        return response
