"""EPUB管理とRAG検索のAPIエンドポイント"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag_util import RAGManager
from app.storage import EPUB_CACHE_DIR, get_epub_settings, save_epub_settings

router = APIRouter()
_logger = logging.getLogger(__name__)

# グローバルRAGマネージャー
_rag_manager: Optional[RAGManager] = None


def get_rag_manager() -> RAGManager:
    """RAGマネージャーのシングルトンインスタンスを取得"""
    global _rag_manager
    if _rag_manager is None:
        settings = get_epub_settings()
        _rag_manager = RAGManager(
            cache_dir=EPUB_CACHE_DIR, embedding_model=settings["embedding_model"]
        )
    return _rag_manager


class EpubSettingsUpdate(BaseModel):
    epub_directory: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 500
    overlap_size: int = 50
    search_top_k: int = 5
    min_similarity_score: float = 0.1


class IndexRequest(BaseModel):
    epub_directory: Optional[str] = None
    chunk_size: Optional[int] = None
    overlap_size: Optional[int] = None


class SearchRequest(BaseModel):
    query: str
    book_name: Optional[str] = None
    top_k: Optional[int] = None
    min_score: Optional[float] = None


@router.get("/settings")
def get_settings():
    """EPUB設定を取得"""
    return get_epub_settings()


@router.post("/settings")
def update_settings(settings: EpubSettingsUpdate):
    """EPUB設定を更新"""
    try:
        save_epub_settings(
            epub_directory=settings.epub_directory,
            embedding_model=settings.embedding_model,
            chunk_size=settings.chunk_size,
            overlap_size=settings.overlap_size,
            search_top_k=settings.search_top_k,
            min_similarity_score=settings.min_similarity_score,
        )

        # RAGマネージャーをリセット（新しい設定で再初期化）
        global _rag_manager
        _rag_manager = None

        return {"status": "success", "message": "設定を更新しました"}
    except Exception as e:
        _logger.error(f"設定更新エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books")
def list_books():
    """利用可能な書籍一覧を取得"""
    try:
        rag_manager = get_rag_manager()
        books = rag_manager.get_available_books()
        return {"books": books}
    except Exception as e:
        _logger.error(f"書籍一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
def index_epub_files(request: IndexRequest):
    """EPUBファイルをインデックス化"""
    try:
        settings = get_epub_settings()

        # リクエストパラメータまたは設定値を使用
        epub_directory = request.epub_directory or settings["epub_directory"]
        chunk_size = request.chunk_size or settings["chunk_size"]
        overlap_size = request.overlap_size or settings["overlap_size"]

        if not epub_directory:
            raise HTTPException(
                status_code=400, detail="EPUBディレクトリが設定されていません"
            )

        epub_dir = Path(epub_directory)
        if not epub_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"ディレクトリが見つかりません: {epub_directory}",
            )

        rag_manager = get_rag_manager()
        indexed_books = rag_manager.index_directory(epub_dir, chunk_size, overlap_size)

        return {
            "status": "success",
            "message": f"{len(indexed_books)}冊の書籍をインデックス化しました",
            "indexed_books": indexed_books,
        }

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"インデックス化エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def search_books(request: SearchRequest):
    """書籍内検索"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="検索クエリが空です")

        settings = get_epub_settings()
        top_k = request.top_k or settings["search_top_k"]
        min_score = request.min_score or settings["min_similarity_score"]

        rag_manager = get_rag_manager()

        if request.book_name:
            # 特定の書籍で検索
            results = rag_manager.search_in_book(
                request.book_name, request.query, top_k, min_score
            )

            formatted_results = []
            for text, metadata, score in results:
                formatted_results.append(
                    {"text": text, "metadata": metadata, "score": score}
                )

            return {
                "query": request.query,
                "book_name": request.book_name,
                "results": formatted_results,
                "total_results": len(formatted_results),
            }
        else:
            # 全書籍で検索
            all_results = rag_manager.search_all_books(request.query, top_k, min_score)

            formatted_results = {}
            total_count = 0

            for book_name, book_results in all_results.items():
                formatted_book_results = []
                for text, metadata, score in book_results:
                    formatted_book_results.append(
                        {"text": text, "metadata": metadata, "score": score}
                    )
                formatted_results[book_name] = formatted_book_results
                total_count += len(formatted_book_results)

            return {
                "query": request.query,
                "results": formatted_results,
                "total_results": total_count,
            }

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/books/{book_name}")
def delete_book_index(book_name: str):
    """書籍のインデックスを削除"""
    try:
        rag_manager = get_rag_manager()
        success = rag_manager.delete_book_index(book_name)

        if success:
            return {
                "status": "success",
                "message": f"書籍「{book_name}」のインデックスを削除しました",
            }
        else:
            raise HTTPException(status_code=404, detail="書籍が見つかりません")

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"インデックス削除エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/format")
def format_search_results(
    query: str, book_name: Optional[str] = None, top_k: int = 5, min_score: float = 0.1
):
    """検索結果をフォーマットして返す（変数展開用）"""
    try:
        if not query.strip():
            return {"formatted_text": "検索クエリが空です。"}

        rag_manager = get_rag_manager()

        if book_name:
            results = rag_manager.search_in_book(book_name, query, top_k, min_score)
        else:
            all_results = rag_manager.search_all_books(query, top_k, min_score)
            # 全書籍の結果を統合してスコア順にソート
            results = []
            for book_results in all_results.values():
                results.extend(book_results)
            results.sort(key=lambda x: x[2], reverse=True)
            results = results[:top_k]

        formatted_text = rag_manager.format_search_results(results)

        return {
            "query": query,
            "formatted_text": formatted_text,
            "result_count": len(results),
        }

    except Exception as e:
        _logger.error(f"フォーマット済み検索エラー: {e}")
        return {"formatted_text": f"検索エラー: {e}"}


@router.get("/health")
def health_check():
    """ヘルスチェック"""
    try:
        settings = get_epub_settings()
        available_books = []

        if EPUB_CACHE_DIR.exists():
            rag_manager = get_rag_manager()
            available_books = rag_manager.get_available_books()

        return {
            "status": "healthy",
            "epub_directory": settings["epub_directory"],
            "cache_directory": str(EPUB_CACHE_DIR),
            "available_books_count": len(available_books),
            "embedding_model": settings["embedding_model"],
        }
    except Exception as e:
        _logger.error(f"ヘルスチェックエラー: {e}")
        return {"status": "error", "error": str(e)}
