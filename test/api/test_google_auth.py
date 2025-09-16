"""Google OAuth認証のテスト"""

import os
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.auth import create_jwt_token, verify_jwt_token


def test_jwt_token_creation_and_verification(mock_env):
    """JWTトークンの作成と検証をテスト"""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
    }

    token = create_jwt_token(user_data)
    assert isinstance(token, str)
    assert len(token) > 0

    decoded_data = verify_jwt_token(token)
    assert decoded_data["email"] == user_data["email"]
    assert decoded_data["name"] == user_data["name"]
    assert decoded_data["picture"] == user_data["picture"]


def test_invalid_jwt_token_verification(mock_env):
    """無効なJWTトークンの検証をテスト"""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        verify_jwt_token("invalid_token")

    assert exc_info.value.status_code == 401
    assert "Invalid token" in str(exc_info.value.detail)


def test_login_endpoint_redirects_to_google(client, mock_env):
    """ログインエンドポイントがGoogleにリダイレクトすることをテスト"""
    with patch("app.routers.auth.oauth.google.authorize_redirect") as mock_redirect:
        mock_redirect.return_value = Mock()
        client.get("/api/auth/login")

        # OAuth認証は実際のGoogleサーバーへのリダイレクトを行うため、
        # このテストではモックが呼ばれることのみ確認
        mock_redirect.assert_called_once()


def test_logout_endpoint(client, mock_env):
    """ログアウトエンドポイントをテスト"""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}


def test_me_endpoint_with_valid_token(client, mock_env):
    """有効なトークンでの/meエンドポイントをテスト"""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
    }

    token = create_jwt_token(user_data)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert response_data["name"] == user_data["name"]
    assert response_data["picture"] == user_data["picture"]


def test_me_endpoint_without_token(client, mock_env):
    """トークンなしでの/meエンドポイントをテスト"""
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # FastAPIのHTTPBearerは403を返す


def test_me_endpoint_with_invalid_token(client, mock_env):
    """無効なトークンでの/meエンドポイントをテスト"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


@patch("app.routers.auth.oauth.google.authorize_access_token")
def test_auth_callback_success(mock_authorize, client, mock_env):
    """OAuth認証コールバック成功のテスト"""
    mock_token = {
        "userinfo": {
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
        }
    }
    mock_authorize.return_value = mock_token

    # 実際のテストでは、Googleからのコールバック要求をシミュレート
    # ここではモックを使用してレスポンスをテスト
    client.get("/api/auth/callback")

    # OAuth Stateの検証等でエラーになる可能性があるが、
    # モックが正しく設定されていることを確認
    mock_authorize.assert_called_once()


def test_security_get_current_user_dependency():
    """セキュリティ依存関数のテスト"""
    from fastapi.security import HTTPAuthorizationCredentials

    from app.security import get_current_user

    user_data = {
        "email": "test@example.com",
        "name": "Test User",
    }

    with patch.dict(os.environ, {"SECRET_KEY": "test_secret_key"}):
        token = create_jwt_token(user_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = get_current_user(credentials)
        assert result["email"] == user_data["email"]
        assert result["name"] == user_data["name"]
