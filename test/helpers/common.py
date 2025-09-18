"""テスト用ヘルパー関数とユーティリティ"""

from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient


def create_test_client() -> TestClient:
    """テスト用FastAPIクライアントを作成"""
    from app.main import create_app

    app = create_app()
    return TestClient(app)


def assert_error_response(
    response, expected_status: int, expected_detail_contains: Optional[str] = None
):
    """エラーレスポンスの検証"""
    assert response.status_code == expected_status
    if expected_detail_contains:
        body = response.json()
        assert expected_detail_contains in body.get("detail", "")


def assert_success_response(response, expected_status: int = 200):
    """成功レスポンスの検証"""
    assert response.status_code == expected_status
    assert response.headers.get("content-type", "").startswith("application/json")


def create_test_article_template() -> Dict[str, Any]:
    """テスト用記事テンプレートデータを作成"""
    return {
        "name": "テストテンプレート",
        "fields": [
            {"key": "title", "label": "タイトル", "input_type": "text"},
            {"key": "content", "label": "内容", "input_type": "textarea"},
        ],
        "prompt_template": "{{base}}\n---\nタイトル: {{title}}\n内容: {{content}}",
        "widgets": ["url_context"],
    }


def create_test_writing_style() -> Dict[str, Any]:
    """テスト用文体データを作成"""
    return {
        "name": "テスト文体",
        "description": "テスト用の文体です",
        "properties": {"tone": "カジュアル", "length": "短め"},
    }


class TestDataFactory:
    """テストデータファクトリー"""

    @staticmethod
    def article_template(
        name: str = "テストテンプレート",
        fields: Optional[List[Dict[str, Any]]] = None,
        widgets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """記事テンプレートのテストデータを生成"""
        if fields is None:
            fields = [
                {"key": "title", "label": "タイトル", "input_type": "text"},
                {"key": "content", "label": "内容", "input_type": "textarea"},
            ]
        if widgets is None:
            widgets = ["url_context"]

        return {
            "name": name,
            "fields": fields,
            "prompt_template": "{{base}}\n---\nタイトル: {{title}}\n内容: {{content}}",
            "widgets": widgets,
        }

    @staticmethod
    def writing_style(
        name: str = "テスト文体", properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """文体のテストデータを生成"""
        if properties is None:
            properties = {"tone": "カジュアル", "length": "短め"}

        return {"name": name, "description": f"{name}の説明", "properties": properties}
