"""EPUBチャプター取得機能のテスト"""

import pytest
from unittest.mock import patch
from pathlib import Path

from app.routers.epub import get_book_chapters


@patch("app.routers.epub.get_epub_settings")
@patch("app.routers.epub.get_epub_files")
@patch("app.routers.epub.extract_text_from_epub")
def test_get_book_chapters_success(mock_extract, mock_get_files, mock_get_settings):
    """書籍チャプター取得成功テスト"""
    # モック設定
    mock_get_settings.return_value = {"epub_directory": "/test/epub"}

    mock_epub_file = Path("/test/epub/test.epub")
    mock_get_files.return_value = [mock_epub_file]

    # 最初の呼び出しで正しい書籍を見つける
    mock_extract.return_value = (
        "テストブック",
        {"第1章": "第1章の内容です。", "第2章": "第2章の内容です。"},
    )

    result = get_book_chapters("テストブック")

    assert result["book_title"] == "テストブック"
    assert len(result["chapters"]) == 2
    assert result["chapters"][0]["chapter_title"] == "第1章"
    assert result["chapters"][0]["content"] == "第1章の内容です。"
    assert result["chapters"][1]["chapter_title"] == "第2章"
    assert result["chapters"][1]["content"] == "第2章の内容です。"


@patch("app.routers.epub.get_epub_settings")
def test_get_book_chapters_no_directory(mock_get_settings):
    """EPUBディレクトリ未設定のテスト"""
    from fastapi import HTTPException

    mock_get_settings.return_value = {"epub_directory": ""}

    with pytest.raises(HTTPException) as exc_info:
        get_book_chapters("テストブック")

    assert exc_info.value.status_code == 400
    assert "設定されていません" in str(exc_info.value.detail)


@patch("app.routers.epub.get_epub_settings")
def test_get_book_chapters_directory_not_exists(mock_get_settings):
    """存在しないディレクトリのテスト"""
    from fastapi import HTTPException

    mock_get_settings.return_value = {"epub_directory": "/nonexistent/directory"}

    with pytest.raises(HTTPException) as exc_info:
        get_book_chapters("テストブック")

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)


@patch("app.routers.epub.get_epub_settings")
@patch("app.routers.epub.get_epub_files")
@patch("app.routers.epub.extract_text_from_epub")
def test_get_book_chapters_book_not_found(
    mock_extract, mock_get_files, mock_get_settings
):
    """書籍が見つからない場合のテスト"""
    from fastapi import HTTPException

    mock_get_settings.return_value = {"epub_directory": "/test/epub"}

    mock_epub_file = Path("/test/epub/test.epub")
    mock_get_files.return_value = [mock_epub_file]

    # 違う書籍名を返す
    mock_extract.return_value = ("別のブック", {})

    with pytest.raises(HTTPException) as exc_info:
        get_book_chapters("テストブック")

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)


@patch("app.routers.epub.get_epub_settings")
@patch("app.routers.epub.get_epub_files")
@patch("app.routers.epub.extract_text_from_epub")
def test_get_book_chapters_extraction_error(
    mock_extract, mock_get_files, mock_get_settings
):
    """テキスト抽出エラーのテスト"""
    from fastapi import HTTPException

    mock_get_settings.return_value = {"epub_directory": "/test/epub"}

    mock_epub_file = Path("/test/epub/test.epub")
    mock_get_files.return_value = [mock_epub_file]

    # テキスト抽出でエラーが発生
    mock_extract.side_effect = Exception("抽出エラー")

    with pytest.raises(HTTPException) as exc_info:
        get_book_chapters("テストブック")

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)


@patch("app.routers.epub.get_epub_settings")
@patch("app.routers.epub.get_epub_files")
@patch("app.routers.epub.extract_text_from_epub")
def test_get_book_chapters_multiple_files(
    mock_extract, mock_get_files, mock_get_settings
):
    """複数のEPUBファイルがある場合のテスト"""
    mock_get_settings.return_value = {"epub_directory": "/test/epub"}

    mock_epub_file1 = Path("/test/epub/book1.epub")
    mock_epub_file2 = Path("/test/epub/book2.epub")
    mock_get_files.return_value = [mock_epub_file1, mock_epub_file2]

    # 最初のファイルは違う書籍、2番目のファイルが対象書籍
    mock_extract.side_effect = [
        ("別のブック", {}),  # 1回目の呼び出し
        ("テストブック", {"第1章": "内容"}),  # 2回目の呼び出し
    ]

    result = get_book_chapters("テストブック")

    assert result["book_title"] == "テストブック"
    assert len(result["chapters"]) == 1
    assert result["chapters"][0]["chapter_title"] == "第1章"
    assert result["chapters"][0]["content"] == "内容"

    # extract_text_from_epubが2回呼ばれることを確認
    assert mock_extract.call_count == 2


@patch("app.routers.epub.get_epub_settings")
@patch("app.routers.epub.get_epub_files")
def test_get_book_chapters_no_epub_files(mock_get_files, mock_get_settings):
    """EPUBファイルが存在しない場合のテスト"""
    from fastapi import HTTPException

    mock_get_settings.return_value = {"epub_directory": "/test/epub"}
    mock_get_files.return_value = []  # 空のリスト

    with pytest.raises(HTTPException) as exc_info:
        get_book_chapters("テストブック")

    assert exc_info.value.status_code == 404
    assert "見つかりません" in str(exc_info.value.detail)
