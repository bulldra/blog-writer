"""API テスト用ヘルパー関数"""

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient


class ApiTestHelper:
    """API テスト用ヘルパークラス"""

    def __init__(self, client: TestClient):
        self.client = client

    def post_article_template(
        self, template_type: str, data: Dict[str, Any]
    ) -> TestClient:
        """記事テンプレートを保存"""
        return self.client.post(f"/api/article-templates/{template_type}", json=data)

    def get_article_template(self, template_type: str) -> TestClient:
        """記事テンプレートを取得"""
        return self.client.get(f"/api/article-templates/{template_type}")

    def delete_article_template(self, template_type: str) -> TestClient:
        """記事テンプレートを削除"""
        return self.client.delete(f"/api/article-templates/{template_type}")

    def list_article_templates(self) -> TestClient:
        """記事テンプレート一覧を取得"""
        return self.client.get("/api/article-templates")

    def post_writing_style(self, style_name: str, data: Dict[str, Any]) -> TestClient:
        """文体を保存"""
        return self.client.post(f"/api/writing-styles/{style_name}", json=data)

    def get_writing_style(self, style_name: str) -> TestClient:
        """文体を取得"""
        return self.client.get(f"/api/writing-styles/{style_name}")

    def delete_writing_style(self, style_name: str) -> TestClient:
        """文体を削除"""
        return self.client.delete(f"/api/writing-styles/{style_name}")

    def list_writing_styles(self) -> TestClient:
        """文体一覧を取得"""
        return self.client.get("/api/writing-styles")

    def generate_ai_content(
        self, prompt: str, url_context: str = None, highlights: list = None
    ) -> TestClient:
        """AI コンテンツ生成"""
        data = {"prompt": prompt}
        if url_context:
            data["url_context"] = url_context
        if highlights:
            data["highlights"] = highlights
        return self.client.post("/api/ai/generate", json=data)


def validate_template_response(
    response_data: Dict[str, Any], expected_name: str = None
):
    """記事テンプレートレスポンスの検証"""
    assert "name" in response_data
    assert "fields" in response_data
    assert isinstance(response_data["fields"], list)

    if expected_name:
        assert response_data["name"] == expected_name

    # フィールドの構造検証
    for field in response_data["fields"]:
        assert "key" in field
        assert "label" in field
        assert "input_type" in field
        assert field["input_type"] in ["text", "textarea"]


def validate_writing_style_response(
    response_data: Dict[str, Any], expected_name: str = None
):
    """文体レスポンスの検証"""
    assert "name" in response_data
    assert "description" in response_data
    assert "properties" in response_data
    assert isinstance(response_data["properties"], dict)

    if expected_name:
        assert response_data["name"] == expected_name
