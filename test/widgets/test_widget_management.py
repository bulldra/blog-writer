from typing import Any, Dict

from app.storage import (
    WIDGET_TYPES,
    get_article_template,
    get_available_widgets,
    save_article_template,
)


def test_widget_types_defined() -> None:
    """ウィジェットタイプが正しく定義されていることを確認"""
    expected_widgets = {
        "url_context",
        "kindle",
        "past_posts",
        "epub",
        "x",
        "scrape",
    }
    assert set(WIDGET_TYPES.keys()) == expected_widgets

    for widget_id, widget_info in WIDGET_TYPES.items():
        assert widget_info["id"] == widget_id
        assert isinstance(widget_info["name"], str)
        assert isinstance(widget_info["description"], str)
        assert len(widget_info["name"]) > 0
        assert len(widget_info["description"]) > 0


def test_get_available_widgets() -> None:
    """利用可能なウィジェット一覧の取得をテスト"""
    widgets = get_available_widgets()
    assert isinstance(widgets, list)
    assert len(widgets) == 7

    widget_ids = [w["id"] for w in widgets]
    assert set(widget_ids) == {
        "url_context",
        "kindle",
        "past_posts",
        "epub",
        "notion",
        "x",
        "scrape",
    }

    for widget in widgets:
        assert "id" in widget
        assert "name" in widget
        assert "description" in widget


def test_save_template_with_widgets() -> None:
    """ウィジェット付きテンプレートの保存をテスト"""
    payload: Dict[str, Any] = {
        "name": "ウィジェットテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["url_context", "kindle"],
    }

    result = save_article_template("test_widget", payload)
    assert result is not None
    assert result["widgets"] == ["url_context", "kindle"]

    # 保存されたテンプレートを取得して確認
    saved = get_article_template("test_widget")
    assert saved is not None
    assert saved["widgets"] == ["url_context", "kindle"]


def test_save_template_with_invalid_widgets() -> None:
    """無効なウィジェットを含むテンプレートの保存をテスト"""
    payload: Dict[str, Any] = {
        "name": "無効ウィジェットテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["url_context", "invalid_widget", "kindle"],
    }

    result = save_article_template("test_invalid_widget", payload)
    assert result is not None
    # 無効なウィジェットは除外される
    assert result["widgets"] == ["url_context", "kindle"]


def test_save_template_with_duplicate_widgets() -> None:
    """重複ウィジェットを含むテンプレートの保存をテスト"""
    payload: Dict[str, Any] = {
        "name": "重複ウィジェットテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["url_context", "kindle", "url_context"],
    }

    result = save_article_template("test_duplicate_widget", payload)
    assert result is not None
    # 重複は除去される
    assert result["widgets"] == ["url_context", "kindle"]


def test_save_template_widget_order_preserved() -> None:
    """ウィジェットの順序が保持されることをテスト"""
    payload: Dict[str, Any] = {
        "name": "順序テスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": ["past_posts", "url_context", "kindle"],
    }

    result = save_article_template("test_widget_order", payload)
    assert result is not None
    assert result["widgets"] == ["past_posts", "url_context", "kindle"]

    # 保存されたテンプレートを取得して順序確認
    saved = get_article_template("test_widget_order")
    assert saved is not None
    assert saved["widgets"] == ["past_posts", "url_context", "kindle"]


def test_template_without_widgets() -> None:
    """ウィジェットなしのテンプレートの保存をテスト"""
    payload: Dict[str, Any] = {
        "name": "ウィジェットなしテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
        "widgets": [],
    }

    result = save_article_template("test_no_widget", payload)
    assert result is not None
    assert result["widgets"] == []

    # ウィジェットプロパティがない場合
    payload_no_widgets = {
        "name": "ウィジェットプロパティなしテスト",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
        ],
        "prompt_template": "{{title}}について書いてください",
    }

    result = save_article_template("test_no_widget_prop", payload_no_widgets)
    assert result is not None
    assert result["widgets"] == []
