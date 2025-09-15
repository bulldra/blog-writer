"""KindleHighlightWidgetコンポーネントのUIテスト"""

import unittest
from unittest.mock import Mock, patch
from app.main import create_app
from fastapi.testclient import TestClient


def test_kindle_widget_ui_messaging():
    """Kindleウィジェットが適切なメッセージを表示することをテスト"""
    # この実装はReactコンポーネントなので、フロントエンドのテストフレームワークが必要
    # ここでは、バックエンドが適切なデータを提供することを確認
    app = create_app()
    client = TestClient(app)
    
    # 書籍リストが正しく返されることを確認
    with patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir, \
         patch("app.routers.obsidian.collect_highlights") as mock_collect:
        
        mock_find_dir.return_value = "/mock/path"
        mock_highlights = [
            Mock(
                id="highlight_1",
                book="テスト書籍A",
                author="著者A",
                text="ハイライト1",
                location="位置1",
                added_on="2024-01-01",
                file="test.md",
                asin="A123456789"
            ),
            Mock(
                id="highlight_2",
                book="テスト書籍B",
                author="著者B",
                text="ハイライト2",
                location="位置2",
                added_on="2024-01-02",
                file="test.md",
                asin="B123456789"
            )
        ]
        mock_collect.return_value = mock_highlights
        
        # 書籍リストAPIの確認
        response = client.get("/api/obsidian/books")
        assert response.status_code == 200
        
        books = response.json()
        assert len(books) == 2
        assert any(book["title"] == "テスト書籍A" for book in books)
        assert any(book["title"] == "テスト書籍B" for book in books)


def test_kindle_widget_highlight_count_accuracy():
    """選択した書籍のハイライト数が正確に報告されることをテスト"""
    app = create_app()
    client = TestClient(app)
    
    # 特定の書籍に500件のハイライトを持つケース
    mock_highlights = []
    for i in range(500):
        mock_highlights.append(Mock(
            id=f"highlight_{i}",
            book="大量ハイライト書籍",
            author="著者",
            text=f"ハイライトテキスト {i}",
            location=f"位置 {i}",
            added_on="2024-01-01",
            file="test.md",
            asin="H123456789"
        ))
    
    with patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir, \
         patch("app.routers.obsidian.collect_highlights") as mock_collect:
        
        mock_find_dir.return_value = "/mock/path"
        mock_collect.return_value = mock_highlights
        
        # 500件のハイライトがすべて返されることを確認
        response = client.get("/api/obsidian/highlights?book=大量ハイライト書籍")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 500
        
        # すべてが同じ書籍のものであることを確認
        for highlight in data:
            assert highlight["book"] == "大量ハイライト書籍"


def test_kindle_widget_handles_no_obsidian_directory():
    """Obsidianディレクトリが見つからない場合の処理をテスト"""
    app = create_app()
    client = TestClient(app)
    
    with patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir:
        mock_find_dir.return_value = None
        
        # 書籍リストAPIが404を返すことを確認
        response = client.get("/api/obsidian/books")
        assert response.status_code == 404
        assert "obsidian dir not found" in response.json()["detail"]
        
        # ハイライトAPIも404を返すことを確認
        response = client.get("/api/obsidian/highlights")
        assert response.status_code == 404
        assert "obsidian dir not found" in response.json()["detail"]