"""Kindleウィジェットが書籍選択時に全体を取り込み対象とすることのテスト"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import create_app


def test_kindle_widget_imports_all_highlights_for_selected_book():
    """書籍を選択した時に、その書籍のすべてのハイライトが取得されることを確認"""
    app = create_app()
    client = TestClient(app)

    # モックハイライトデータ（同じ書籍から300件のハイライト）
    mock_highlights = []
    for i in range(300):
        mock_highlights.append(
            Mock(
                id=f"highlight_{i}",
                book="テスト書籍",
                author="テスト著者",
                text=f"ハイライトテキスト {i}",
                location=f"位置 {i}",
                added_on="2024-01-01",
                file="test.md",
                asin="B123456789",
            )
        )

    with (
        patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir,
        patch("app.routers.obsidian.collect_highlights") as mock_collect,
    ):
        mock_find_dir.return_value = "/mock/path"
        mock_collect.return_value = mock_highlights

        # 特定の書籍のハイライトを取得
        response = client.get("/api/obsidian/highlights?book=テスト書籍")
        assert response.status_code == 200

        data = response.json()
        # すべてのハイライト（300件）が返されることを確認
        assert len(data) == 300

        # すべてが同じ書籍のものであることを確認
        for highlight in data:
            assert highlight["book"] == "テスト書籍"
            assert highlight["author"] == "テスト著者"


def test_kindle_widget_filters_by_book_correctly():
    """書籍でフィルタリングが正しく動作することを確認"""
    app = create_app()
    client = TestClient(app)

    # 複数の書籍のハイライトを準備
    mock_highlights = [
        Mock(
            id="highlight_1",
            book="書籍A",
            author="著者A",
            text="書籍Aのハイライト",
            location="位置1",
            added_on="2024-01-01",
            file="book_a.md",
            asin="A123456789",
        ),
        Mock(
            id="highlight_2",
            book="書籍B",
            author="著者B",
            text="書籍Bのハイライト",
            location="位置2",
            added_on="2024-01-02",
            file="book_b.md",
            asin="B123456789",
        ),
        Mock(
            id="highlight_3",
            book="書籍A",
            author="著者A",
            text="書籍Aの別のハイライト",
            location="位置3",
            added_on="2024-01-03",
            file="book_a.md",
            asin="A123456789",
        ),
    ]

    with (
        patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir,
        patch("app.routers.obsidian.collect_highlights") as mock_collect,
    ):
        mock_find_dir.return_value = "/mock/path"
        mock_collect.return_value = mock_highlights

        # 書籍Aのハイライトのみを取得
        response = client.get("/api/obsidian/highlights?book=書籍A")
        assert response.status_code == 200

        data = response.json()
        # 書籍Aのハイライト2件のみが返されることを確認
        assert len(data) == 2
        for highlight in data:
            assert highlight["book"] == "書籍A"

        # すべてのハイライトを取得（書籍指定なし）
        response_all = client.get("/api/obsidian/highlights")
        assert response_all.status_code == 200

        data_all = response_all.json()
        # 全ての書籍のハイライト3件が返されることを確認
        assert len(data_all) == 3


def test_kindle_widget_handles_empty_book_filter():
    """書籍名が空の場合、すべてのハイライトが返されることを確認"""
    app = create_app()
    client = TestClient(app)

    mock_highlights = [
        Mock(
            id="highlight_1",
            book="書籍A",
            author="著者A",
            text="ハイライト1",
            location="位置1",
            added_on="2024-01-01",
            file="test.md",
            asin="A123456789",
        ),
        Mock(
            id="highlight_2",
            book="書籍B",
            author="著者B",
            text="ハイライト2",
            location="位置2",
            added_on="2024-01-02",
            file="test.md",
            asin="B123456789",
        ),
    ]

    with (
        patch("app.routers.obsidian.find_obsidian_dir") as mock_find_dir,
        patch("app.routers.obsidian.collect_highlights") as mock_collect,
    ):
        mock_find_dir.return_value = "/mock/path"
        mock_collect.return_value = mock_highlights

        # 空の書籍名でリクエスト
        response = client.get("/api/obsidian/highlights?book=")
        assert response.status_code == 200

        data = response.json()
        # すべてのハイライトが返されることを確認
        assert len(data) == 2
