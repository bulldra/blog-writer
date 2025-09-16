"""文体テンプレートストレージのテスト"""
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from app.storage import (
    init_storage,
    save_writing_style,
    get_writing_style,
    list_writing_styles,
    delete_writing_style,
)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """一時的なデータディレクトリを作成"""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("BLOGWRITER_DATA_DIR", tmpdir)
        init_storage()
        yield Path(tmpdir)


def test_writing_style_defaults_present(temp_data_dir):
    """デフォルトの文体テンプレートが存在することをテスト"""
    styles = list_writing_styles()
    assert isinstance(styles, list)
    assert len(styles) >= 0


def test_writing_style_save_and_retrieve(temp_data_dir):
    """文体テンプレートの保存と取得をテスト"""
    style_data = {
        "name": "テスト文体",
        "properties": {
            "tone": "フレンドリー",
            "formality": "カジュアル",
            "length_preference": "簡潔",
        },
        "source_text": "元となる文章のサンプルです。",
        "description": "テスト用の文体テンプレートです。",
    }
    
    # 保存
    saved_style = save_writing_style("test_style", style_data)
    assert saved_style is not None
    assert saved_style["id"] == "test_style"
    assert saved_style["name"] == "テスト文体"
    
    # 取得
    retrieved_style = get_writing_style("test_style")
    assert retrieved_style is not None
    assert retrieved_style["id"] == "test_style"
    assert retrieved_style["name"] == "テスト文体"
    assert retrieved_style["properties"]["tone"] == "フレンドリー"


def test_writing_style_list_includes_saved(temp_data_dir):
    """保存した文体テンプレートがリストに含まれることをテスト"""
    style_data = {
        "name": "リスト確認用文体",
        "properties": {"tone": "丁寧"},
        "source_text": "サンプルテキスト",
        "description": "リスト確認用",
    }
    
    save_writing_style("list_test", style_data)
    styles = list_writing_styles()
    
    test_style = next((s for s in styles if s["id"] == "list_test"), None)
    assert test_style is not None
    assert test_style["name"] == "リスト確認用文体"


def test_writing_style_update_existing(temp_data_dir):
    """既存の文体テンプレートの更新をテスト"""
    original_data = {
        "name": "更新前文体",
        "properties": {"tone": "フォーマル"},
        "source_text": "元のテキスト",
        "description": "更新前",
    }
    
    updated_data = {
        "name": "更新後文体",
        "properties": {"tone": "カジュアル"},
        "source_text": "更新されたテキスト",
        "description": "更新後",
    }
    
    # 初期保存
    save_writing_style("update_test", original_data)
    
    # 更新
    updated_style = save_writing_style("update_test", updated_data)
    assert updated_style["name"] == "更新後文体"
    assert updated_style["properties"]["tone"] == "カジュアル"
    
    # 取得して確認
    retrieved = get_writing_style("update_test")
    assert retrieved["name"] == "更新後文体"


def test_writing_style_delete(temp_data_dir):
    """文体テンプレートの削除をテスト"""
    style_data = {
        "name": "削除テスト文体",
        "properties": {"tone": "ニュートラル"},
        "source_text": "削除されるテキスト",
        "description": "削除テスト用",
    }
    
    # 保存
    save_writing_style("delete_test", style_data)
    assert get_writing_style("delete_test") is not None
    
    # 削除
    result = delete_writing_style("delete_test")
    assert result is True
    
    # 削除確認
    assert get_writing_style("delete_test") is None


def test_writing_style_delete_nonexistent(temp_data_dir):
    """存在しない文体テンプレートの削除をテスト"""
    result = delete_writing_style("nonexistent")
    assert result is False


def test_writing_style_get_nonexistent(temp_data_dir):
    """存在しない文体テンプレートの取得をテスト"""
    result = get_writing_style("nonexistent")
    assert result is None


def test_writing_style_properties_validation(temp_data_dir):
    """文体プロパティのバリデーションをテスト"""
    # 最小限のデータ
    minimal_data = {
        "name": "最小文体",
        "properties": {},
        "source_text": "",
        "description": "",
    }
    
    style = save_writing_style("minimal", minimal_data)
    assert style is not None
    assert style["properties"] == {}
    
    # 完全なデータ
    complete_data = {
        "name": "完全文体",
        "properties": {
            "tone": "プロフェッショナル",
            "formality": "フォーマル", 
            "length_preference": "詳細",
            "target_audience": "専門家",
            "writing_style": "解説的",
        },
        "source_text": "詳細な説明を含む文章のサンプルです。",
        "description": "プロフェッショナル向けの詳細な文体テンプレート",
    }
    
    style = save_writing_style("complete", complete_data)
    assert style is not None
    assert len(style["properties"]) == 5