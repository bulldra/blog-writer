"""AI UtilsのRAG機能テスト"""

from app.ai_utils import generate_rag_query, inject_rag_context


def test_generate_rag_query_basic():
    """基本的なRAGクエリ生成テスト"""
    prompt = (
        "機械学習について教えてください。深層学習の基本的な概念を説明してください。"
    )
    title = "AIの基礎"

    query = generate_rag_query(prompt, title)

    assert "AIの基礎" in query
    assert len(query) <= 100
    assert query.strip()


def test_generate_rag_query_no_title():
    """タイトルなしのRAGクエリ生成テスト"""
    prompt = "プログラミング言語のPythonについて学習したい"

    query = generate_rag_query(prompt)

    assert query.strip()
    assert len(query) <= 100


def test_generate_rag_query_long_prompt():
    """長いプロンプトのRAGクエリ生成テスト"""
    prompt = "非常に長いプロンプトテキスト" * 20

    query = generate_rag_query(prompt)

    assert len(query) <= 100


def test_generate_rag_query_empty():
    """空のプロンプトのRAGクエリ生成テスト"""
    query = generate_rag_query("")

    assert query == ""


def test_inject_rag_context_with_content():
    """RAGコンテキスト注入テスト（コンテンツあり）"""
    prompt = "機械学習について説明してください。"
    rag_context = "関連情報:\n1. [AI基礎] 機械学習は..."

    result = inject_rag_context(prompt, rag_context)

    assert rag_context in result
    assert "参考情報" in result
    assert prompt in result


def test_inject_rag_context_empty():
    """RAGコンテキスト注入テスト（空のコンテキスト）"""
    prompt = "機械学習について説明してください。"
    rag_context = ""

    result = inject_rag_context(prompt, rag_context)

    assert result == prompt


def test_inject_rag_context_no_results():
    """RAGコンテキスト注入テスト（結果なし）"""
    prompt = "機械学習について説明してください。"
    rag_context = "関連する情報が見つかりませんでした。"

    result = inject_rag_context(prompt, rag_context)

    assert result == prompt


def test_inject_rag_context_complex_prompt():
    """複雑なプロンプトへのRAGコンテキスト注入テスト"""
    prompt = """以下の要件に従って記事を作成してください。
    - タイトル: AI技術の活用
    - 文字数: 1000文字程度
    詳細な説明をお願いします。"""

    rag_context = "関連情報:\n1. [AI技術書] AIの活用事例..."

    result = inject_rag_context(prompt, rag_context)

    assert rag_context in result
    assert "参考情報" in result
    assert "詳細な説明をお願いします。" in result
