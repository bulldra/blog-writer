"""Obsidian API拡張のテスト"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client for the app"""
    return TestClient(app)


@pytest.fixture
def temp_obsidian_api_structure():
    """API テスト用のObsidian構造を作成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        
        # ディレクトリ構造作成
        articles_dir = root / "articles"
        highlights_dir = root / "kindle_highlights"
        articles_dir.mkdir()
        highlights_dir.mkdir()
        
        # 記事ファイル作成
        (articles_dir / "test_article.md").write_text(
            "# Test Article\n\nThis is a test article content.", encoding="utf-8"
        )
        
        # ハイライトファイル作成
        (highlights_dir / "test_book.md").write_text(
            "---\ntitle: Test Book API\nauthor: API Author\n---\n\n"
            "> This is a test highlight\n\nLocation: 42",
            encoding="utf-8"
        )
        
        yield root


@pytest.fixture
def api_settings(temp_obsidian_api_structure):
    """API テスト用の設定"""
    with tempfile.TemporaryDirectory() as settings_dir:
        settings_path = Path(settings_dir) / "settings.json"
        
        with patch("app.obsidian._settings_path", return_value=settings_path):
            yield {
                "settings_path": settings_path,
                "obsidian_root": temp_obsidian_api_structure,
            }


def test_health_endpoint_with_config(client, api_settings):
    """設定ありでのhealthエンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 設定を保存
    settings_data = {
        "obsidian": {
            "root_dir": root_dir,
            "articles_dir": "articles",
            "highlights_dir": "kindle_highlights"
        }
    }
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["obsidianDir"] == root_dir
    assert data["highlightsDir"] == str(Path(root_dir) / "kindle_highlights")
    assert data["articlesDir"] == str(Path(root_dir) / "articles")


def test_get_config_endpoint_new_format(client, api_settings):
    """新形式設定の取得エンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 新形式で設定を保存
    settings_data = {
        "obsidian": {
            "root_dir": root_dir,
            "articles_dir": "my_articles",
            "highlights_dir": "my_highlights"
        }
    }
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/config")
    assert response.status_code == 200
    
    data = response.json()
    assert data["rootDir"] == root_dir
    assert data["articlesDir"] == "my_articles"
    assert data["highlightsDir"] == "my_highlights"


def test_get_config_endpoint_legacy_format(client, api_settings):
    """旧形式設定の取得エンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 旧形式で設定を保存
    settings_data = {"obsidian_dir": root_dir}
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/config")
    assert response.status_code == 200
    
    data = response.json()
    assert data["rootDir"] == root_dir
    assert data["articlesDir"] == "articles"  # デフォルト値
    assert data["highlightsDir"] == "kindle_highlights"  # デフォルト値


def test_set_config_endpoint(client, api_settings):
    """設定保存エンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    config_data = {
        "root_dir": root_dir,
        "articles_dir": "custom_articles",
        "highlights_dir": "custom_highlights"
    }
    
    response = client.post("/api/obsidian/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["configured"]["rootDir"] == root_dir
    assert data["configured"]["articlesDir"] == "custom_articles"
    assert data["configured"]["highlightsDir"] == "custom_highlights"


def test_set_config_endpoint_invalid_dir(client, api_settings):
    """無効なディレクトリでの設定保存エンドポイントテスト"""
    config_data = {
        "root_dir": "/nonexistent/directory",
        "articles_dir": "articles",
        "highlights_dir": "highlights"
    }
    
    response = client.post("/api/obsidian/config", json=config_data)
    assert response.status_code == 400
    assert "Invalid directory" in response.json()["detail"]



def test_articles_endpoint(client, api_settings):
    """記事一覧エンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 設定を保存
    settings_data = {
        "obsidian": {
            "root_dir": root_dir,
            "articles_dir": "articles",
            "highlights_dir": "kindle_highlights"
        }
    }
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/articles")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_article"
    assert data[0]["relative_path"] == "test_article.md"


def test_highlights_endpoint_with_new_structure(client, api_settings):
    """新構造でのハイライトエンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 設定を保存
    settings_data = {
        "obsidian": {
            "root_dir": root_dir,
            "articles_dir": "articles",
            "highlights_dir": "kindle_highlights"
        }
    }
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/highlights")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) > 0
    highlight = data[0]
    assert highlight["book"] == "Test Book API"
    assert highlight["author"] == "API Author"
    assert "This is a test highlight" in highlight["text"]


def test_books_endpoint_with_new_structure(client, api_settings):
    """新構造での書籍一覧エンドポイントテスト"""
    root_dir = str(api_settings["obsidian_root"])
    
    # 設定を保存
    settings_data = {
        "obsidian": {
            "root_dir": root_dir,
            "articles_dir": "articles",
            "highlights_dir": "kindle_highlights"
        }
    }
    api_settings["settings_path"].write_text(
        json.dumps(settings_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    response = client.get("/api/obsidian/books")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    book = data[0]
    assert book["title"] == "Test Book API"
    assert book["author"] == "API Author"


def test_endpoints_without_config(client, api_settings):
    """設定なしでのエンドポイントテスト"""
    # 設定ファイルを削除または空にする
    api_settings["settings_path"].write_text("{}", encoding="utf-8")
    
    # ハイライト関連は404
    response = client.get("/api/obsidian/highlights")
    assert response.status_code == 404
    assert "highlights dir not found" in response.json()["detail"]
    
    response = client.get("/api/obsidian/books")
    assert response.status_code == 404
    assert "highlights dir not found" in response.json()["detail"]
    
    # 記事関連も404
    response = client.get("/api/obsidian/articles")
    assert response.status_code == 404
    assert "articles dir not found" in response.json()["detail"]