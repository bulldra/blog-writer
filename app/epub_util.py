"""EPUB処理ユーティリティ"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def extract_text_from_epub(epub_path: Path) -> Tuple[str, Dict[str, str]]:
    """EPUBファイルからテキストを抽出する
    
    Args:
        epub_path: EPUBファイルのパス
        
    Returns:
        タイトルと抽出されたテキストの辞書のタプル
    """
    try:
        book = epub.read_epub(str(epub_path))
        
        # メタデータからタイトルを取得
        title = book.get_metadata('DC', 'title')
        book_title = title[0][0] if title else epub_path.stem
        
        chapters = {}
        chapter_num = 1
        
        # 各アイテムからテキストを抽出
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # HTMLタグを除去してテキストのみ抽出
                text = soup.get_text(strip=True)
                
                # 空白の正規化
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                
                if text and len(text) > 50:  # 意味のあるコンテンツのみ
                    chapter_title = f"Chapter {chapter_num}"
                    
                    # チャプタータイトルを抽出
                    h_tags = soup.find_all(['h1', 'h2', 'h3'])
                    if h_tags:
                        first_heading = h_tags[0].get_text(strip=True)
                        if first_heading and len(first_heading) < 100:
                            chapter_title = first_heading
                    
                    chapters[chapter_title] = text
                    chapter_num += 1
        
        return book_title, chapters
        
    except Exception as e:
        raise ValueError(f"EPUB読み込みエラー: {e}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """テキストをチャンクに分割する
    
    Args:
        text: 分割するテキスト
        chunk_size: チャンクサイズ（文字数）
        overlap: チャンク間のオーバーラップ（文字数）
        
    Returns:
        分割されたテキストのリスト
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # 文の境界で分割を試みる
        if end < len(text):
            # 最後の句読点を探す
            for i in range(end, max(start + chunk_size // 2, 0), -1):
                if text[i] in '。．！？\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # オーバーラップを考慮して次の開始点を決定
        if end >= len(text):
            break
        start = max(start + chunk_size - overlap, end)
    
    return chunks


def get_epub_files(directory: Path) -> List[Path]:
    """指定ディレクトリ内のEPUBファイルを取得する
    
    Args:
        directory: 検索ディレクトリ
        
    Returns:
        EPUBファイルのパスのリスト
    """
    if not directory.exists():
        return []
    
    epub_files = []
    for pattern in ['*.epub', '*.EPUB']:
        epub_files.extend(directory.glob(pattern))
        # サブディレクトリも検索
        epub_files.extend(directory.rglob(pattern))
    
    # 重複を除去して返す
    return list(set(epub_files))


def extract_metadata(epub_path: Path) -> Dict[str, Optional[str]]:
    """EPUBファイルからメタデータを抽出する
    
    Args:
        epub_path: EPUBファイルのパス
        
    Returns:
        メタデータの辞書
    """
    try:
        book = epub.read_epub(str(epub_path))
        
        metadata = {}
        
        # タイトル
        title = book.get_metadata('DC', 'title')
        metadata['title'] = title[0][0] if title else None
        
        # 著者
        creator = book.get_metadata('DC', 'creator')
        metadata['author'] = creator[0][0] if creator else None
        
        # 出版社
        publisher = book.get_metadata('DC', 'publisher')
        metadata['publisher'] = publisher[0][0] if publisher else None
        
        # 言語
        language = book.get_metadata('DC', 'language')
        metadata['language'] = language[0][0] if language else None
        
        # 説明
        description = book.get_metadata('DC', 'description')
        metadata['description'] = description[0][0] if description else None
        
        return metadata
        
    except Exception:
        return {}