"""文体テンプレートAPIのテスト"""
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import init_storage


@pytest.fixture
def temp_data_dir(monkeypatch):
    """一時的なデータディレクトリを作成"""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("BLOGWRITER_DATA_DIR", tmpdir)
        init_storage()
        yield Path(tmpdir)


@pytest.fixture
def client():
    """テスト用のFastAPIクライアント"""
    return TestClient(app)


def test_list_writing_styles_empty(client, temp_data_dir):
    """空の文体テンプレート一覧取得のテスト"""
    response = client.get("/api/writing-styles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_writing_style(client, temp_data_dir):
    """文体テンプレート作成のテスト"""
    style_data = {
        "name": "テスト文体",
        "properties": {
            "tone": "フレンドリー",
            "formality": "カジュアル",
        },
        "source_text": "元のテキストです。",
        "description": "テスト用の文体テンプレート",
    }
    
    response = client.post("/api/writing-styles/test_style", json=style_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == "test_style"
    assert data["name"] == "テスト文体"
    assert data["properties"]["tone"] == "フレンドリー"


def test_get_writing_style(client, temp_data_dir):
    """文体テンプレート取得のテスト"""
    # まず作成
    style_data = {
        "name": "取得テスト文体",
        "properties": {"tone": "丁寧"},
        "source_text": "サンプルテキスト",
        "description": "取得テスト用",
    }
    
    client.post("/api/writing-styles/get_test", json=style_data)
    
    # 取得
    response = client.get("/api/writing-styles/get_test")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == "get_test"
    assert data["name"] == "取得テスト文体"


def test_get_nonexistent_writing_style(client, temp_data_dir):
    """存在しない文体テンプレート取得のテスト"""
    response = client.get("/api/writing-styles/nonexistent")
    assert response.status_code == 404


def test_update_writing_style(client, temp_data_dir):
    """文体テンプレート更新のテスト"""
    # 作成
    original_data = {
        "name": "更新前文体",
        "properties": {"tone": "フォーマル"},
        "source_text": "元テキスト",
        "description": "更新前",
    }
    
    client.post("/api/writing-styles/update_test", json=original_data)
    
    # 更新
    updated_data = {
        "name": "更新後文体",
        "properties": {"tone": "カジュアル"},
        "source_text": "更新テキスト",
        "description": "更新後",
    }
    
    response = client.post("/api/writing-styles/update_test", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "更新後文体"
    assert data["properties"]["tone"] == "カジュアル"


def test_delete_writing_style(client, temp_data_dir):
    """文体テンプレート削除のテスト"""
    # 作成
    style_data = {
        "name": "削除テスト文体",
        "properties": {"tone": "ニュートラル"},
        "source_text": "削除テスト",
        "description": "削除テスト用",
    }
    
    client.post("/api/writing-styles/delete_test", json=style_data)
    
    # 削除
    response = client.delete("/api/writing-styles/delete_test")
    assert response.status_code == 200
    
    data = response.json()
    assert data["ok"] is True
    
    # 削除確認
    response = client.get("/api/writing-styles/delete_test")
    assert response.status_code == 404


def test_delete_nonexistent_writing_style(client, temp_data_dir):
    """存在しない文体テンプレート削除のテスト"""
    response = client.delete("/api/writing-styles/nonexistent")
    assert response.status_code == 400


def test_list_writing_styles_with_data(client, temp_data_dir):
    """データがある場合の文体テンプレート一覧取得のテスト"""
    # 複数のスタイルを作成
    styles = [
        {
            "id": "style1",
            "data": {
                "name": "スタイル1",
                "properties": {"tone": "フレンドリー"},
                "source_text": "テキスト1",
                "description": "説明1",
            }
        },
        {
            "id": "style2", 
            "data": {
                "name": "スタイル2",
                "properties": {"tone": "フォーマル"},
                "source_text": "テキスト2",
                "description": "説明2",
            }
        }
    ]
    
    for style in styles:
        client.post(f"/api/writing-styles/{style['id']}", json=style['data'])
    
    # 一覧取得
    response = client.get("/api/writing-styles")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    
    # IDでソートして確認
    data.sort(key=lambda x: x["id"])
    assert data[0]["name"] == "スタイル1"
    assert data[1]["name"] == "スタイル2"


def test_create_writing_style_invalid_data(client, temp_data_dir):
    """無効なデータでの文体テンプレート作成のテスト"""
    # 必須フィールドが不足
    invalid_data = {
        "name": "不完全文体",
        # propertiesが欠如
        "source_text": "テキスト",
        "description": "説明",
    }
    
    response = client.post("/api/writing-styles/invalid", json=invalid_data)
    assert response.status_code == 400