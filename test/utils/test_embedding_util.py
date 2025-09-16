"""Embedding機能の追加テスト"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.embedding_util import EmbeddingManager


def test_embedding_manager_init():
    """EmbeddingManagerの初期化テスト"""
    manager = EmbeddingManager("sentence-transformers/all-MiniLM-L6-v2")
    assert manager.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert manager.texts == []
    assert manager.metadata == []


@patch("app.embedding_util.SentenceTransformer")
def test_encode_texts_success(mock_sentence_transformer):
    """テキストエンコーディング成功テスト"""
    mock_model = Mock()
    mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_sentence_transformer.return_value = mock_model

    manager = EmbeddingManager("test-model")
    texts = ["テスト文章1", "テスト文章2"]

    result = manager.encode_texts(texts)

    assert len(result) == 2
    mock_model.encode.assert_called_once_with(texts)


def test_build_index_with_data():
    """データありでのインデックス構築テスト"""
    with patch("app.embedding_util.SentenceTransformer") as mock_transformer:
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2], [0.4, 0.5]]
        mock_transformer.return_value = mock_model

        manager = EmbeddingManager("test-model")
        texts = ["テスト1", "テスト2"]
        metadata = [{"id": "1"}, {"id": "2"}]

        manager.build_index(texts, metadata)

        assert manager.texts == texts
        assert manager.metadata == metadata
        assert manager.index is not None


def test_build_index_empty_data():
    """空データでのインデックス構築テスト"""
    manager = EmbeddingManager("test-model")

    with pytest.raises(ValueError, match="テキストが空です"):
        manager.build_index([], [])


def test_search_no_index():
    """インデックスがない状態での検索テスト"""
    manager = EmbeddingManager("test-model")

    result = manager.search("クエリ")

    assert result == []


@patch("app.embedding_util.SentenceTransformer")
def test_search_with_results(mock_sentence_transformer):
    """検索結果ありのテスト"""
    mock_model = Mock()
    # インデックス構築時のembedding
    mock_model.encode.side_effect = [
        [[0.1, 0.2], [0.4, 0.5]],  # インデックス構築時
        [[0.2, 0.3]],  # 検索時
    ]
    mock_sentence_transformer.return_value = mock_model

    manager = EmbeddingManager("test-model")
    texts = ["関連テキスト", "無関係テキスト"]
    metadata = [{"source": "doc1"}, {"source": "doc2"}]

    manager.build_index(texts, metadata)

    # 検索実行
    results = manager.search("関連", top_k=1, min_score=0.5)

    assert len(results) <= 1


def test_save_and_load_index():
    """インデックスの保存・読み込みテスト"""
    with patch("app.embedding_util.SentenceTransformer"):
        manager = EmbeddingManager("test-model")

        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test.index"

            # 保存テスト（インデックスなし）
            manager.save_index(index_path)
            assert index_path.exists()

            # 読み込みテスト
            new_manager = EmbeddingManager("test-model")
            result = new_manager.load_index(index_path)
            assert result is True


def test_load_nonexistent_index():
    """存在しないインデックスの読み込みテスト"""
    manager = EmbeddingManager("test-model")

    result = manager.load_index(Path("/nonexistent/path"))

    assert result is False
