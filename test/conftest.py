import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# テスト用にappパスを追加
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from test.helpers.api import ApiTestHelper
from test.helpers.common import create_test_client


@pytest.fixture
def client():
    """FastAPIのテストクライアントを作成"""
    return create_test_client()


@pytest.fixture
def api_helper(client):
    """API テスト用ヘルパーを作成"""
    return ApiTestHelper(client)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """一時的なデータディレクトリを作成し、ストレージを初期化"""
    from app.storage import init_storage

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("BLOGWRITER_DATA_DIR", tmpdir)
        init_storage()
        yield Path(tmpdir)


@pytest.fixture
def mock_env(monkeypatch):
    """テスト用環境変数を設定"""
    env_vars = {
        "GOOGLE_OAUTH_CLIENT_ID": "test_client_id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "test_client_secret",
        "JWT_SECRET_KEY": "test_secret_key_for_jwt_tokens_minimum_32_characters",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
