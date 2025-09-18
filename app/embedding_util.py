"""埋め込み処理ユーティリティ"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


class EmbeddingManager:
    """埋め込みベクトルの管理クラス"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """初期化

        Args:
            model_name: 使用する埋め込みモデル名
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[NearestNeighbors] = None
        self.embeddings: Optional[np.ndarray] = None
        self.texts: List[str] = []
        self.metadata: List[Dict[str, str]] = []

    def _load_model(self) -> None:
        """埋め込みモデルを遅延ロード"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)

    def encode_texts(self, texts: List[str]) -> Any:
        """
        テキストを埋め込みベクトルに変換

        Args:
            texts: 埋め込み対象のテキストリスト

        Returns:
            埋め込みベクトルの配列
        """
        self._load_model()
        if not self.model:
            raise RuntimeError("埋め込みモデルの読み込みに失敗しました")

        # テスト互換性のため追加引数は渡さずデフォルト挙動を使用
        local_embeddings = self.model.encode(texts)

        # 正規化（コサイン類似度用）
        local_embeddings = local_embeddings / np.linalg.norm(
            local_embeddings, axis=1, keepdims=True
        )
        return local_embeddings.astype(np.ndarray)

    def build_index(
        self, texts: List[str], metadata: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """scikit-learnベースのインデックスを構築

        Args:
            texts: インデックス対象のテキストリスト
            metadata: 各テキストのメタデータ
        """
        if not texts:
            raise ValueError("テキストが空です")

        self.texts = texts
        self.metadata = metadata or [{"text": text} for text in texts]

        # 埋め込みベクトルを生成
        self.embeddings = self.encode_texts(texts)

        # scikit-learnのNearestNeighborsを使用（コサイン距離）
        self.index = NearestNeighbors(
            n_neighbors=min(50, len(texts)),  # 最大50件
            metric="cosine",
            algorithm="brute",  # 小規模データセットには最適
        )

        # インデックスを構築
        self.index.fit(self.embeddings)

    def search(
        self, query: str, top_k: int = 5, min_score: float = 0.1
    ) -> List[Tuple[str, Dict[str, str], float]]:
        """クエリに類似するテキストを検索

        Args:
            query: 検索クエリ
            top_k: 返す結果数
            min_score: 最小類似度スコア（コサイン類似度: 1.0 - コサイン距離）

        Returns:
            (テキスト, メタデータ, スコア)のタプルのリスト
        """
        if not self.index or not self.texts or self.embeddings is None:
            return []

        # クエリの埋め込みベクトルを生成
        query_embedding = self.encode_texts([query])

        # 検索実行（k近傍）
        k = min(top_k, len(self.texts))
        distances, indices = self.index.kneighbors(query_embedding, n_neighbors=k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            # コサイン距離からコサイン類似度に変換
            similarity = 1.0 - distance
            if similarity >= min_score:
                results.append((self.texts[idx], self.metadata[idx], float(similarity)))

        return results

    def save_index(self, filepath: Path) -> None:
        """インデックスをファイルに保存

        テスト仕様:
          - インデックスが未構築でも例外を投げず"空インデックス"としてファイルを生成
          - 引数で与えたパスそのものに書き込む（拡張子を書き換えない）

        Args:
            filepath: 保存先ファイルパス
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "texts": self.texts,
            "metadata": self.metadata,
            "model_name": self.model_name,
            "embeddings": self.embeddings,
            "index": self.index,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def load_index(self, filepath: Path) -> bool:
        """ファイルからインデックスを読み込み

        Args:
            filepath: インデックスファイルパス

        Returns:
            読み込み成功の可否
        """
        try:
            # 互換性: 直接のパス優先。存在しなければ .pkl も見る
            if filepath.exists():
                target = filepath
            else:
                alt = filepath.with_suffix(".pkl")
                if not alt.exists():
                    return False
                target = alt

            with open(target, "rb") as f:
                data = pickle.load(f)

            self.texts = data["texts"]
            self.metadata = data["metadata"]
            self.model_name = data.get("model_name", self.model_name)
            self.embeddings = data.get("embeddings")
            self.index = data.get("index")

            return True

        except Exception:
            return False

    def add_texts(
        self, new_texts: List[str], new_metadata: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """既存のインデックスに新しいテキストを追加

        Args:
            new_texts: 追加するテキストリスト
            new_metadata: 追加するメタデータ
        """
        if not new_texts:
            return

        if not self.index or self.embeddings is None:
            # インデックスが存在しない場合は新規作成
            self.build_index(new_texts, new_metadata)
            return

        # 新しいテキストの埋め込みを生成
        new_embeddings = self.encode_texts(new_texts)

        # 既存の埋め込みと結合
        self.embeddings = np.vstack([self.embeddings, new_embeddings])

        # テキストとメタデータを追加
        self.texts.extend(new_texts)
        if new_metadata:
            self.metadata.extend(new_metadata)
        else:
            self.metadata.extend([{"text": text} for text in new_texts])

        # インデックスを再構築
        self.index = NearestNeighbors(
            n_neighbors=min(50, len(self.texts)), metric="cosine", algorithm="brute"
        )
        self.index.fit(self.embeddings)

    def get_stats(self) -> Dict[str, int]:
        """インデックスの統計情報を取得

        Returns:
            統計情報の辞書
        """
        return {
            "total_texts": len(self.texts),
            "index_size": len(self.texts) if self.index else 0,
            "dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
        }
