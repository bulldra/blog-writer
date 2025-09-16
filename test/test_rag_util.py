"""RAG機能のテスト"""

from pathlib import Path
from unittest.mock import Mock, patch
from app.rag_util import RAGManager


def test_rag_manager_init():
    """RAGマネージャーの初期化テスト"""
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    assert rag_manager.cache_dir == cache_dir
    assert rag_manager.embedding_manager is not None
    assert rag_manager.book_indices == {}


@patch("app.rag_util.extract_text_from_epub")
@patch("app.rag_util.EmbeddingManager")
def test_index_epub_file(mock_embedding_manager, mock_extract_text):
    """EPUBファイルのインデックス化テスト"""
    # モックの設定
    mock_extract_text.return_value = ("テストブック", {"Chapter 1": "テスト内容" * 100})

    mock_embedding_instance = Mock()
    mock_embedding_manager.return_value = mock_embedding_instance

    # RAGマネージャーの作成
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    # テスト実行
    epub_path = Path("test.epub")
    result = rag_manager.index_epub_file(epub_path)

    # 検証
    assert result == "テストブック"
    mock_embedding_instance.build_index.assert_called_once()
    mock_embedding_instance.save_index.assert_called_once()


@patch("app.rag_util.get_epub_files")
def test_index_directory(mock_get_epub_files):
    """ディレクトリインデックス化テスト"""
    mock_get_epub_files.return_value = []

    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    result = rag_manager.index_directory(Path("/test/dir"))

    assert result == []
    mock_get_epub_files.assert_called_once()


def test_search_in_book_no_index():
    """インデックスがない場合の検索テスト"""
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    result = rag_manager.search_in_book("存在しない本", "テストクエリ")

    assert result == []


def test_get_available_books_empty():
    """利用可能な書籍がない場合のテスト"""
    cache_dir = Path("/tmp/test_cache_empty")
    rag_manager = RAGManager(cache_dir)

    books = rag_manager.get_available_books()

    assert books == []


def test_format_search_results_empty():
    """空の検索結果のフォーマットテスト"""
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    formatted = rag_manager.format_search_results([])

    assert "関連する情報が見つかりませんでした" in formatted


def test_format_search_results_with_data():
    """検索結果ありのフォーマットテスト"""
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    results = [
        ("テスト文章1", {"book_title": "テスト本1", "chapter_title": "第1章"}, 0.8),
        ("テスト文章2", {"book_title": "テスト本2", "chapter_title": "第2章"}, 0.7),
    ]

    formatted = rag_manager.format_search_results(results)

    assert "関連情報:" in formatted
    assert "テスト本1" in formatted
    assert "テスト本2" in formatted
    assert "0.800" in formatted
    assert "0.700" in formatted


@patch("app.rag_util.Path.unlink")
@patch("app.rag_util.Path.exists")
def test_delete_book_index(mock_exists, mock_unlink):
    """書籍インデックス削除テスト"""
    mock_exists.return_value = True

    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    result = rag_manager.delete_book_index("テスト本")

    assert result is True
    assert mock_unlink.call_count >= 2  # .faiss と .pkl ファイル


def test_search_all_books_empty():
    """全書籍検索（書籍なし）のテスト"""
    cache_dir = Path("/tmp/test_cache")
    rag_manager = RAGManager(cache_dir)

    results = rag_manager.search_all_books("テストクエリ")

    assert results == {}
