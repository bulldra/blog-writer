import os
from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import BaseModel

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
)

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"


class UserInfo(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserInfo


def create_jwt_token(user_data: Dict[str, Any]) -> str:
    return jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request) -> Dict[str, Any]:
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get("userinfo")
        if not user:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_info = UserInfo(
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
        )

        jwt_token = create_jwt_token(
            {
                "email": user_info.email,
                "name": user_info.name,
                "picture": user_info.picture,
            }
        )

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": user_info.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")


@router.get("/me")
async def get_current_user(token: Dict[str, Any] = Depends(verify_jwt_token)) -> UserInfo:
    return UserInfo(**token)


@router.post("/logout")
async def logout() -> Dict[str, str]:
    return {"message": "Logged out successfully"}
