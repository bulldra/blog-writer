"""EPUBハイライト機能のテスト"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models import EpubHighlight
from app.routers.epub import (
    create_highlight,
    delete_highlight,
    get_highlights,
    get_selected_highlights_for_context,
    update_highlight,
)


@pytest.fixture
def mock_db():
    """モックデータベースセッション"""
    return Mock(spec=Session)


@pytest.fixture
def sample_highlight_data():
    """サンプルハイライトデータ"""
    return {
        "book_title": "テストブック",
        "chapter_title": "第1章",
        "highlighted_text": "これは重要なテキストです。",
        "context_before": "前の文章。",
        "context_after": "後の文章。",
        "position_start": 100,
        "position_end": 150,
    }


def test_create_highlight(mock_db, sample_highlight_data):
    """ハイライト作成のテスト"""
    from app.routers.epub import HighlightCreate

    # モックハイライトオブジェクト
    mock_highlight = Mock()
    mock_highlight.id = 1

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    mock_highlight.id = 1

    # ハイライト作成データ
    highlight_data = HighlightCreate(**sample_highlight_data)

    with patch("app.routers.epub.EpubHighlight") as mock_epub_highlight:
        mock_epub_highlight.return_value = mock_highlight

        result = create_highlight(highlight_data, mock_db)

        assert result["id"] == 1
        assert "作成しました" in result["message"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


def test_get_highlights_empty(mock_db):
    """空のハイライト一覧取得テスト"""
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_highlights(db=mock_db)

    assert result["highlights"] == []


def test_get_highlights_with_book_filter(mock_db):
    """書籍フィルタ付きハイライト取得テスト"""
    mock_highlight = Mock()
    mock_highlight.id = 1
    mock_highlight.book_title = "テストブック"
    mock_highlight.chapter_title = "第1章"
    mock_highlight.highlighted_text = "テストテキスト"
    mock_highlight.context_before = ""
    mock_highlight.context_after = ""
    mock_highlight.position_start = 0
    mock_highlight.position_end = 10
    mock_highlight.selected_for_context = False
    mock_highlight.created_at.isoformat.return_value = "2024-01-01T00:00:00"

    mock_query = Mock()
    mock_query.filter.return_value.order_by.return_value.all.return_value = [
        mock_highlight
    ]
    mock_db.query.return_value = mock_query

    result = get_highlights(book_title="テストブック", db=mock_db)

    assert len(result["highlights"]) == 1
    assert result["highlights"][0]["book_title"] == "テストブック"


def test_update_highlight_success(mock_db):
    """ハイライト更新成功テスト"""
    from app.routers.epub import HighlightUpdate

    mock_highlight = Mock()
    mock_highlight.id = 1
    mock_highlight.selected_for_context = False

    mock_db.query.return_value.filter.return_value.first.return_value = mock_highlight
    mock_db.commit.return_value = None

    update_data = HighlightUpdate(selected_for_context=True)

    result = update_highlight(1, update_data, mock_db)

    assert "更新しました" in result["message"]
    assert mock_highlight.selected_for_context
    mock_db.commit.assert_called_once()


def test_update_highlight_not_found(mock_db):
    """存在しないハイライト更新テスト"""
    from fastapi import HTTPException

    from app.routers.epub import HighlightUpdate

    mock_db.query.return_value.filter.return_value.first.return_value = None

    update_data = HighlightUpdate(selected_for_context=True)

    with pytest.raises(HTTPException) as exc_info:
        update_highlight(999, update_data, mock_db)

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)


def test_delete_highlight_success(mock_db):
    """ハイライト削除成功テスト"""
    mock_highlight = Mock()
    mock_highlight.id = 1

    mock_db.query.return_value.filter.return_value.first.return_value = mock_highlight
    mock_db.delete.return_value = None
    mock_db.commit.return_value = None

    result = delete_highlight(1, mock_db)

    assert "削除しました" in result["message"]
    mock_db.delete.assert_called_once_with(mock_highlight)
    mock_db.commit.assert_called_once()


def test_delete_highlight_not_found(mock_db):
    """存在しないハイライト削除テスト"""
    from fastapi import HTTPException

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        delete_highlight(999, mock_db)

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)


def test_get_selected_highlights_for_context(mock_db):
    """コンテキスト用ハイライト取得テスト"""
    mock_highlight1 = Mock()
    mock_highlight1.id = 1
    mock_highlight1.book_title = "ブック1"
    mock_highlight1.chapter_title = "第1章"
    mock_highlight1.highlighted_text = "重要なテキスト1"
    mock_highlight1.created_at.isoformat.return_value = "2024-01-01T00:00:00"

    mock_highlight2 = Mock()
    mock_highlight2.id = 2
    mock_highlight2.book_title = "ブック2"
    mock_highlight2.chapter_title = "第2章"
    mock_highlight2.highlighted_text = "重要なテキスト2"
    mock_highlight2.created_at.isoformat.return_value = "2024-01-02T00:00:00"

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_highlight1,
        mock_highlight2,
    ]

    result = get_selected_highlights_for_context(mock_db)

    assert len(result["highlights"]) == 2
    assert "formatted_context" in result
    assert "ブック1 - 第1章" in result["formatted_context"]
    assert "重要なテキスト1" in result["formatted_context"]
    assert "ブック2 - 第2章" in result["formatted_context"]
    assert "重要なテキスト2" in result["formatted_context"]


def test_get_selected_highlights_empty_context(mock_db):
    """空のコンテキスト用ハイライト取得テスト"""
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_selected_highlights_for_context(mock_db)

    assert result["highlights"] == []
    assert result["formatted_context"] == ""


@patch("app.models.init_db")
def test_init_db_called(mock_init_db):
    """データベース初期化の呼び出しテスト"""
    # routers パッケージのフラグをリセット（他のテストの影響を排除）
    import app.routers as routers_pkg

    if hasattr(routers_pkg, "_epub_init_called_once"):
        delattr(routers_pkg, "_epub_init_called_once")

    # epub.pyをインポートした時にinit_dbが呼ばれることを確認
    from app.routers import epub  # noqa: F401

    mock_init_db.assert_called_once()


def test_epub_highlight_model():
    """EpubHighlightモデルのテスト"""
    highlight = EpubHighlight(
        book_title="テストブック",
        chapter_title="第1章",
        highlighted_text="テストテキスト",
        context_before="前文",
        context_after="後文",
        position_start=0,
        position_end=10,
        selected_for_context=True,
    )

    assert highlight.book_title == "テストブック"
    assert highlight.chapter_title == "第1章"
    assert highlight.highlighted_text == "テストテキスト"
    assert highlight.context_before == "前文"
    assert highlight.context_after == "後文"
    assert highlight.position_start == 0
    assert highlight.position_end == 10
    assert highlight.selected_for_context
