"""RAG（Retrieval-Augmented Generation）ユーティリティ"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from app.embedding_util import EmbeddingManager
from app.epub_util import chunk_text, extract_text_from_epub, get_epub_files

_logger = logging.getLogger(__name__)


class RAGManager:
    """RAG機能の管理クラス"""

    def __init__(
        self,
        cache_dir: Path,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """初期化

        Args:
            cache_dir: キャッシュディレクトリ
            embedding_model: 埋め込みモデル名
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_manager = EmbeddingManager(embedding_model)
        self.book_indices: Dict[str, str] = {}  # book_name -> index_path

    def index_epub_file(
        self, epub_path: Path, chunk_size: int = 500, overlap: int = 50
    ) -> str:
        """EPUBファイルをインデックス化

        Args:
            epub_path: EPUBファイルのパス
            chunk_size: チャンクサイズ
            overlap: オーバーラップサイズ

        Returns:
            インデックス化された書籍名
        """
        try:
            # EPUBからテキストを抽出
            book_title, chapters = extract_text_from_epub(epub_path)
            _logger.info(f"EPUBを読み込み: {book_title}")

            # チャプター毎にチャンク分割
            all_chunks = []
            all_metadata = []

            for chapter_title, chapter_text in chapters.items():
                chunks = chunk_text(chapter_text, chunk_size, overlap)

                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadata.append(
                        {
                            "book_title": book_title,
                            "chapter_title": chapter_title,
                            "chunk_index": str(i),
                            "file_path": str(epub_path),
                            "text": chunk,
                        }
                    )

            if not all_chunks:
                raise ValueError(f"有効なテキストが見つかりません: {epub_path}")

            # インデックスを構築
            embedding_manager = EmbeddingManager(self.embedding_manager.model_name)
            embedding_manager.build_index(all_chunks, all_metadata)

            # インデックスを保存
            index_path = self.cache_dir / f"{book_title}.index"
            embedding_manager.save_index(index_path)

            # 書籍インデックスに追加
            self.book_indices[book_title] = str(index_path)

            _logger.info(
                f"インデックス化完了: {book_title} ({len(all_chunks)}チャンク)"
            )
            return book_title

        except Exception as e:
            _logger.error(f"EPUBインデックス化エラー: {e}")
            raise

    def index_directory(
        self, epub_dir: Path, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """ディレクトリ内の全EPUBファイルをインデックス化

        Args:
            epub_dir: EPUBファイルが格納されたディレクトリ
            chunk_size: チャンクサイズ
            overlap: オーバーラップサイズ

        Returns:
            インデックス化された書籍名のリスト
        """
        epub_files = get_epub_files(epub_dir)
        indexed_books = []

        for epub_path in epub_files:
            try:
                book_title = self.index_epub_file(epub_path, chunk_size, overlap)
                indexed_books.append(book_title)
            except Exception as e:
                _logger.error(f"ファイル処理エラー {epub_path}: {e}")
                continue

        return indexed_books

    def load_book_index(self, book_name: str) -> bool:
        """指定された書籍のインデックスを読み込み

        Args:
            book_name: 書籍名

        Returns:
            読み込み成功の可否
        """
        if book_name in self.book_indices:
            index_path = Path(self.book_indices[book_name])
            return self.embedding_manager.load_index(index_path)

        # キャッシュディレクトリから検索
        index_path = self.cache_dir / f"{book_name}.index"
        if index_path.with_suffix(".pkl").exists():
            success = self.embedding_manager.load_index(index_path)
            if success:
                self.book_indices[book_name] = str(index_path)
            return success

        return False

    def search_in_book(
        self, book_name: str, query: str, top_k: int = 5, min_score: float = 0.1
    ) -> List[Tuple[str, Dict[str, str], float]]:
        """特定の書籍内で検索

        Args:
            book_name: 書籍名
            query: 検索クエリ
            top_k: 返す結果数
            min_score: 最小類似度スコア

        Returns:
            検索結果のリスト
        """
        if not self.load_book_index(book_name):
            return []

        return self.embedding_manager.search(query, top_k, min_score)

    def search_all_books(
        self, query: str, top_k: int = 5, min_score: float = 0.1
    ) -> Dict[str, List[Tuple[str, Dict[str, str], float]]]:
        """全書籍で検索

        Args:
            query: 検索クエリ
            top_k: 書籍ごとの返す結果数
            min_score: 最小類似度スコア

        Returns:
            書籍名をキーとした検索結果の辞書
        """
        results = {}

        # 利用可能な書籍インデックスを探索
        available_books = list(self.book_indices.keys())

        # キャッシュディレクトリから追加の書籍を探索
        for index_file in self.cache_dir.glob("*.pkl"):
            if index_file.stem.endswith(".index"):
                book_name = index_file.stem[:-6]  # ".index"を除去
                if book_name not in available_books:
                    available_books.append(book_name)

        for book_name in available_books:
            try:
                book_results = self.search_in_book(book_name, query, top_k, min_score)
                if book_results:
                    results[book_name] = book_results
            except Exception as e:
                _logger.error(f"書籍検索エラー {book_name}: {e}")
                continue

        return results

    def get_available_books(self) -> List[str]:
        """利用可能な書籍名のリストを取得

        Returns:
            書籍名のリスト
        """
        books = set(self.book_indices.keys())

        # キャッシュディレクトリから追加
        for index_file in self.cache_dir.glob("*.pkl"):
            if index_file.stem.endswith(".index"):
                book_name = index_file.stem[:-6]  # ".index"を除去
                books.add(book_name)

        return sorted(list(books))

    def delete_book_index(self, book_name: str) -> bool:
        """書籍のインデックスを削除

        Args:
            book_name: 書籍名

        Returns:
            削除成功の可否
        """
        try:
            if book_name in self.book_indices:
                index_path = Path(self.book_indices[book_name])
                del self.book_indices[book_name]
            else:
                index_path = self.cache_dir / f"{book_name}.index"

            # ファイルを削除
            pkl_file = index_path.with_suffix(".pkl")

            if pkl_file.exists():
                pkl_file.unlink()

            return True

        except Exception as e:
            _logger.error(f"インデックス削除エラー {book_name}: {e}")
            return False

    def format_search_results(
        self, results: List[Tuple[str, Dict[str, str], float]]
    ) -> str:
        """検索結果を文字列にフォーマット

        Args:
            results: 検索結果

        Returns:
            フォーマットされた文字列
        """
        if not results:
            return "関連する情報が見つかりませんでした。"

        formatted = ["関連情報:"]

        for i, (text, metadata, score) in enumerate(results, 1):
            book_title = metadata.get("book_title", "不明")
            chapter_title = metadata.get("chapter_title", "不明")

            formatted.append(
                f"\n{i}. [{book_title} - {chapter_title}] (類似度: {score:.3f})"
            )
            formatted.append(f"   {text[:200]}{'...' if len(text) > 200 else ''}")

        return "\n".join(formatted)
