import sys
import tempfile
from pathlib import Path

import pytest


def _ensure_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    test_dir = Path(__file__).resolve().parent
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))


_ensure_paths()

from .helpers.api import ApiTestHelper  # noqa: E402
from .helpers.common import create_test_client  # noqa: E402


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


# pytest では local LLM/外部LLM へ直接到達しないように共通モックを適用
@pytest.fixture(autouse=True)
def _patch_llm_calls(monkeypatch):
    async def _fake_call_ai(prompt: str) -> str:
        # 生成系は常にスタブ文字列を返す
        return "[stub-test]"

    async def _fake_call_ai_stream(prompt: str):
        # ストリームは小さな塊を2回返す
        yield "[stub-stream-1] "
        yield "[stub-stream-2]\n"

    # ai_utils 側をパッチ
    monkeypatch.setattr("app.ai_utils.call_ai", _fake_call_ai, raising=True)
    monkeypatch.setattr(
        "app.ai_utils.call_ai_stream", _fake_call_ai_stream, raising=True
    )

    # routers.ai の互換ラッパーも同時にパッチ（早期経路に入るため）
    try:
        monkeypatch.setattr("app.routers.ai.call_ai", _fake_call_ai, raising=True)
        monkeypatch.setattr(
            "app.routers.ai.call_ai_stream", _fake_call_ai_stream, raising=True
        )
    except Exception:
        # ルータ未ロードのケースは無視
        pass

    # storage.get_ai_settings をスタブ化して、常に外部呼び出し不能な設定に固定
    def _fake_get_ai_settings():
        return {
            "provider": "gemini",  # lmstudio 分岐を避ける
            "model": "gemini-2.5-flash",
            "api_key": "",  # APIキー無し → 生成系はスタブ経路
            "max_prompt_len": 32768,
        }

    monkeypatch.setattr(
        "app.storage.get_ai_settings", _fake_get_ai_settings, raising=True
    )
