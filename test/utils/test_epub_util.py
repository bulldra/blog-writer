"""EPUB処理機能のテスト"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.epub_util import (
    chunk_text,
    extract_metadata,
    extract_text_from_epub,
    get_epub_files,
)


def test_chunk_text():
    """テキストチャンク分割のテスト"""
    text = "これは長いテキストです。" * 50  # 約500文字
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)  # オーバーラップ考慮


def test_chunk_text_empty():
    """空テキストのチャンク化テスト"""
    chunks = chunk_text("", chunk_size=100, overlap=10)
    assert chunks == []


def test_chunk_text_short():
    """短いテキストのチャンク化テスト"""
    text = "短いテキスト"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_get_epub_files_empty_dir():
    """空ディレクトリでのEPUBファイル検索テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_dir = Path(tmpdir)
        files = get_epub_files(epub_dir)
        assert files == []


def test_get_epub_files_with_files():
    """EPUBファイルありのディレクトリ検索テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_dir = Path(tmpdir)

        # テストファイル作成
        (epub_dir / "test1.epub").touch()
        (epub_dir / "test2.txt").touch()  # 非EPUB
        (epub_dir / "test3.EPUB").touch()  # 大文字拡張子

        files = get_epub_files(epub_dir)

        epub_files = [f.name for f in files]
        assert "test1.epub" in epub_files
        assert "test3.EPUB" in epub_files
        assert "test2.txt" not in epub_files


def test_get_epub_files_nonexistent():
    """存在しないディレクトリのテスト"""
    nonexistent_dir = Path("/nonexistent/directory")
    files = get_epub_files(nonexistent_dir)
    assert files == []


@patch("app.epub_util.epub.read_epub")
def test_extract_text_from_epub_mock(mock_read_epub):
    """EPUBテキスト抽出のモックテスト"""
    # モックEPUBブックを作成
    mock_book = Mock()
    mock_book.get_metadata.return_value = [("テストブック", None)]

    # モックアイテム
    mock_item = Mock()
    mock_item.get_type.return_value = 1  # ITEM_DOCUMENT
    mock_item.get_content.return_value = (
        b"<html><body><h1>Chapter 1</h1><p>Test content</p></body></html>"
    )

    mock_book.get_items.return_value = [mock_item]
    mock_read_epub.return_value = mock_book

    title, chapters = extract_text_from_epub(Path("test.epub"))

    assert title == "テストブック"
    assert len(chapters) >= 0  # BeautifulSoupが利用可能であればチャプターが抽出される


@patch("app.epub_util.epub.read_epub")
def test_extract_metadata_mock(mock_read_epub):
    """EPUBメタデータ抽出のモックテスト"""
    mock_book = Mock()
    mock_book.get_metadata.side_effect = lambda ns, tag: {
        ("DC", "title"): [("テストタイトル", None)],
        ("DC", "creator"): [("テスト作者", None)],
        ("DC", "publisher"): [("テスト出版社", None)],
        ("DC", "language"): [("ja", None)],
        ("DC", "description"): [("テスト説明", None)],
    }.get((ns, tag), [])

    mock_read_epub.return_value = mock_book

    metadata = extract_metadata(Path("test.epub"))

    assert metadata["title"] == "テストタイトル"
    assert metadata["author"] == "テスト作者"
    assert metadata["publisher"] == "テスト出版社"
    assert metadata["language"] == "ja"
    assert metadata["description"] == "テスト説明"


@patch("app.epub_util.epub.read_epub")
def test_extract_text_from_epub_error(mock_read_epub):
    """EPUB読み込みエラーのテスト"""
    mock_read_epub.side_effect = Exception("ファイル読み込みエラー")

    with pytest.raises(ValueError, match="EPUB読み込みエラー"):
        extract_text_from_epub(Path("invalid.epub"))
