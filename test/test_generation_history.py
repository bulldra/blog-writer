from typing import Dict, List

from app.storage import (
    delete_generation_history,
    get_generation_history,
    list_generation_history,
    save_generation_history,
)


def test_save_and_retrieve_generation_history():
    """生成履歴の保存と取得をテスト"""
    # 生成履歴を保存
    history = save_generation_history(
        title="テスト記事",
        template_type="test_template",
        widgets_used=["properties", "url_context"],
        properties={"title": "テストタイトル", "author": "テスト著者"},
        generated_content="これはテスト用の生成コンテンツです。",
        reasoning="テスト用の思考過程です。"
    )
    
    assert history["title"] == "テスト記事"
    assert history["template_type"] == "test_template"
    assert history["widgets_used"] == ["properties", "url_context"]
    assert history["properties"] == {"title": "テストタイトル", "author": "テスト著者"}
    assert history["generated_content"] == "これはテスト用の生成コンテンツです。"
    assert history["reasoning"] == "テスト用の思考過程です。"
    assert "id" in history
    assert "created_at" in history
    
    # 保存した履歴を取得
    retrieved = get_generation_history(history["id"])
    assert retrieved is not None
    assert retrieved["title"] == "テスト記事"
    assert retrieved["template_type"] == "test_template"
    assert retrieved["widgets_used"] == ["properties", "url_context"]
    assert retrieved["properties"] == {"title": "テストタイトル", "author": "テスト著者"}


def test_list_generation_history():
    """生成履歴一覧の取得をテスト"""
    # 複数の履歴を保存
    history1 = save_generation_history(
        title="記事1",
        template_type="template1",
        widgets_used=["properties"],
        properties={"theme": "テーマ1"},
        generated_content="コンテンツ1",
    )
    
    history2 = save_generation_history(
        title="記事2",
        template_type="template2",
        widgets_used=["kindle", "past_posts"],
        properties={"theme": "テーマ2"},
        generated_content="コンテンツ2",
    )
    
    # 履歴一覧を取得
    histories = list_generation_history(limit=10)
    assert isinstance(histories, list)
    assert len(histories) >= 2
    
    # 最新順でソートされている
    found_history1 = None
    found_history2 = None
    for h in histories:
        if h["id"] == history1["id"]:
            found_history1 = h
        elif h["id"] == history2["id"]:
            found_history2 = h
    
    assert found_history1 is not None
    assert found_history2 is not None
    assert found_history1["title"] == "記事1"
    assert found_history2["title"] == "記事2"
    assert "content_length" in found_history1
    assert found_history1["content_length"] == len("コンテンツ1")


def test_delete_generation_history():
    """生成履歴の削除をテスト"""
    # 履歴を保存
    history = save_generation_history(
        title="削除テスト",
        template_type="test",
        widgets_used=[],
        properties={},
        generated_content="削除対象のコンテンツ",
    )
    
    history_id = history["id"]
    
    # 履歴が存在することを確認
    retrieved = get_generation_history(history_id)
    assert retrieved is not None
    
    # 履歴を削除
    success = delete_generation_history(history_id)
    assert success is True
    
    # 削除後は取得できない
    retrieved_after_delete = get_generation_history(history_id)
    assert retrieved_after_delete is None
    
    # 存在しない履歴の削除はFalseを返す
    success_nonexistent = delete_generation_history(999999)
    assert success_nonexistent is False


def test_generation_history_without_optional_fields():
    """オプションフィールドなしの生成履歴をテスト"""
    history = save_generation_history(
        title="最小限の履歴",
        template_type="minimal",
        widgets_used=[],
        properties={},
        generated_content="最小限のコンテンツ",
        # reasoning は省略
    )
    
    assert history["title"] == "最小限の履歴"
    assert history["reasoning"] == ""
    assert history["widgets_used"] == []
    assert history["properties"] == {}
    
    # 取得時も同様
    retrieved = get_generation_history(history["id"])
    assert retrieved is not None
    assert retrieved["reasoning"] == ""
    assert retrieved["widgets_used"] == []
    assert retrieved["properties"] == {}


def test_generation_history_limit():
    """履歴の件数制限をテスト"""
    # 複数の履歴を保存
    for i in range(5):
        save_generation_history(
            title=f"履歴{i}",
            template_type="test",
            widgets_used=[],
            properties={},
            generated_content=f"コンテンツ{i}",
        )
    
    # 制限付きで取得
    histories_limited = list_generation_history(limit=3)
    assert len(histories_limited) == 3
    
    # より多い制限で取得
    histories_all = list_generation_history(limit=10)
    assert len(histories_all) >= 5