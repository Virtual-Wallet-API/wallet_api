from typing import Optional
from app.dependencies import oauth2_scheme
from app.infrestructure import auth
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse


api_base = "/api/v1"
frontend_base = "/fe"

unauthorized_redirect = RedirectResponse(url=f"{frontend_base}/",
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            headers={"WWW-Authenticate": "Bearer"})


def get_valid_user_data(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    """Auth token dependency for protected dependencies."""
    if token:
        try:
            return auth.verify_token(token)
        except HTTPException as e:
            raise unauthorized_redirect

    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer"):
            try:
                return auth.verify_token(auth_header)
            except HTTPException as e:
                raise unauthorized_redirect

    raise unauthorized_redirect