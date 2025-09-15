"""埋め込み処理ユーティリティ"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingManager:
    """埋め込みベクトルの管理クラス"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """初期化
        
        Args:
            model_name: 使用する埋め込みモデル名
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.IndexFlatIP] = None
        self.texts: List[str] = []
        self.metadata: List[Dict[str, str]] = []
    
    def _load_model(self) -> None:
        """埋め込みモデルを遅延ロード"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """テキストを埋め込みベクトルに変換
        
        Args:
            texts: 埋め込み対象のテキストリスト
            
        Returns:
            埋め込みベクトルの配列
        """
        self._load_model()
        if not self.model:
            raise RuntimeError("埋め込みモデルの読み込みに失敗しました")
        
        # バッチ処理で効率化
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=True)
        
        # 正規化（コサイン類似度用）
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings
    
    def build_index(
        self, 
        texts: List[str], 
        metadata: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """FAISSインデックスを構築
        
        Args:
            texts: インデックス対象のテキストリスト
            metadata: 各テキストのメタデータ
        """
        if not texts:
            raise ValueError("テキストが空です")
        
        self.texts = texts
        self.metadata = metadata or [{"text": text} for text in texts]
        
        # 埋め込みベクトルを生成
        embeddings = self.encode_texts(texts)
        
        # FAISSインデックスを作成（内積用）
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # ベクトルを追加
        self.index.add(embeddings.astype(np.float32))
    
    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        min_score: float = 0.1
    ) -> List[Tuple[str, Dict[str, str], float]]:
        """クエリに類似するテキストを検索
        
        Args:
            query: 検索クエリ
            top_k: 返す結果数
            min_score: 最小類似度スコア
            
        Returns:
            (テキスト, メタデータ, スコア)のタプルのリスト
        """
        if not self.index or not self.texts:
            return []
        
        # クエリの埋め込みベクトルを生成
        query_embedding = self.encode_texts([query])
        
        # 検索実行
        scores, indices = self.index.search(
            query_embedding.astype(np.float32), 
            min(top_k, len(self.texts))
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and score >= min_score:
                results.append((
                    self.texts[idx],
                    self.metadata[idx],
                    float(score)
                ))
        
        return results
    
    def save_index(self, filepath: Path) -> None:
        """インデックスをファイルに保存
        
        Args:
            filepath: 保存先ファイルパス
        """
        if not self.index:
            raise ValueError("保存するインデックスがありません")
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # FAISSインデックスを保存
        faiss.write_index(self.index, str(filepath.with_suffix('.faiss')))
        
        # メタデータを保存
        metadata_file = filepath.with_suffix('.pkl')
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'texts': self.texts,
                'metadata': self.metadata,
                'model_name': self.model_name
            }, f)
    
    def load_index(self, filepath: Path) -> bool:
        """ファイルからインデックスを読み込み
        
        Args:
            filepath: インデックスファイルパス
            
        Returns:
            読み込み成功の可否
        """
        try:
            faiss_file = filepath.with_suffix('.faiss')
            metadata_file = filepath.with_suffix('.pkl')
            
            if not faiss_file.exists() or not metadata_file.exists():
                return False
            
            # FAISSインデックスを読み込み
            self.index = faiss.read_index(str(faiss_file))
            
            # メタデータを読み込み
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.texts = data['texts']
                self.metadata = data['metadata']
                self.model_name = data.get('model_name', self.model_name)
            
            return True
            
        except Exception:
            return False
    
    def add_texts(
        self, 
        new_texts: List[str], 
        new_metadata: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """既存のインデックスに新しいテキストを追加
        
        Args:
            new_texts: 追加するテキストリスト
            new_metadata: 追加するメタデータ
        """
        if not new_texts:
            return
        
        if not self.index:
            # インデックスが存在しない場合は新規作成
            self.build_index(new_texts, new_metadata)
            return
        
        # 新しいテキストの埋め込みを生成
        new_embeddings = self.encode_texts(new_texts)
        
        # インデックスに追加
        self.index.add(new_embeddings.astype(np.float32))
        
        # メタデータを追加
        self.texts.extend(new_texts)
        if new_metadata:
            self.metadata.extend(new_metadata)
        else:
            self.metadata.extend([{"text": text} for text in new_texts])
    
    def get_stats(self) -> Dict[str, int]:
        """インデックスの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'total_texts': len(self.texts),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.index.d if self.index else 0
        }