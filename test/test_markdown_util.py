"""Markdownユーティリティのテスト"""
from app.markdown_util import generate_writing_style_markdown, generate_style_comparison_markdown


def test_generate_writing_style_markdown_basic():
    """基本的なMarkdown生成のテスト"""
    style_data = {
        "name": "テスト文体",
        "description": "テスト用の文体です",
        "source_text": "これはサンプルテキストです。",
        "properties": {
            "tone": "フレンドリー",
            "formality": "カジュアル",
        },
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
    }
    
    result = generate_writing_style_markdown(style_data)
    
    assert "# テスト文体" in result
    assert "## 説明" in result
    assert "テスト用の文体です" in result
    assert "## 文体プロパティ" in result
    assert "### tone" in result
    assert "フレンドリー" in result
    assert "## 元となる文章" in result
    assert "これはサンプルテキストです。" in result


def test_generate_writing_style_markdown_minimal():
    """最小限のデータでのMarkdown生成のテスト"""
    style_data = {
        "name": "最小文体",
        "description": "",
        "source_text": "",
        "properties": {},
    }
    
    result = generate_writing_style_markdown(style_data)
    
    assert "# 最小文体" in result
    assert "## 使用方法" in result
    # 空のセクションは含まれない
    assert "## 説明" not in result
    assert "## 文体プロパティ" not in result
    assert "## 元となる文章" not in result


def test_generate_style_comparison_markdown_empty():
    """空のリストでの比較表生成のテスト"""
    result = generate_style_comparison_markdown([])
    
    assert "# 文体テンプレート比較" in result
    assert "文体テンプレートがありません" in result


def test_generate_style_comparison_markdown_multiple():
    """複数の文体での比較表生成のテスト"""
    styles = [
        {
            "name": "カジュアル文体",
            "description": "親しみやすい文体です",
            "properties": {
                "tone": "フレンドリー",
                "formality": "カジュアル",
            },
            "source_text": "こんにちは！",
        },
        {
            "name": "フォーマル文体",
            "description": "正式な文体です",
            "properties": {
                "tone": "丁寧",
                "formality": "フォーマル",
                "length": "詳細",
            },
            "source_text": "拝啓、時下ますます...",
        },
    ]
    
    result = generate_style_comparison_markdown(styles)
    
    assert "# 文体テンプレート比較" in result
    assert "| 文体名 | 説明 |" in result
    assert "カジュアル文体" in result
    assert "フォーマル文体" in result
    assert "## 詳細" in result
    assert "### カジュアル文体" in result
    assert "### フォーマル文体" in result


def test_generate_style_comparison_markdown_long_text():
    """長いテキストでの比較表生成のテスト"""
    styles = [
        {
            "name": "長い説明の文体",
            "description": "これはとても長い説明文です。" * 10,  # 長い説明
            "properties": {
                "very_long_property_name": "とても長いプロパティ値です" * 5,  # 長いプロパティ
            },
            "source_text": "長いソーステキストです。" * 50,  # 長いソーステキスト
        },
    ]
    
    result = generate_style_comparison_markdown(styles)
    
    # 長いテキストが省略されていることを確認
    assert "..." in result
    # テーブル形式が保たれていることを確認
    assert "|" in result