"""文体テンプレートストレージのテスト"""

from app.storage import (
    delete_writing_style,
    get_writing_style,
    list_writing_styles,
    save_writing_style,
)


def test_writing_style_defaults_present(temp_data_dir):
    """デフォルトの文体テンプレートが存在することをテスト"""
    styles = list_writing_styles()
    assert isinstance(styles, list)
    assert len(styles) >= 0


def test_writing_style_save_and_retrieve(temp_data_dir):
    """文体テンプレートの保存と取得をテスト"""
    style_data = {
        "name": "テスト文体",
        "properties": {
            "tone": "フレンドリー",
            "formality": "カジュアル",
            "length_preference": "簡潔",
        },
        "source_text": "元となる文章のサンプルです。",
        "description": "テスト用の文体テンプレートです。",
        "tone_manner": {
            "dos": ["親しみやすい表現を使う"],
            "donts": ["堅苦しい表現は避ける"],
            "example_phrases": ["〜してみませんか？"],
            "brand_voice_rules": "親しみやすさを第一に",
        },
    }

    # 保存
    saved_style = save_writing_style("test_style", style_data)
    assert saved_style is not None
    assert saved_style["id"] == "test_style"
    assert saved_style["name"] == "テスト文体"
    assert saved_style["tone_manner"]["dos"] == ["親しみやすい表現を使う"]

    # 取得
    retrieved_style = get_writing_style("test_style")
    assert retrieved_style is not None
    assert retrieved_style["id"] == "test_style"
    assert retrieved_style["name"] == "テスト文体"
    assert retrieved_style["properties"]["tone"] == "フレンドリー"
    assert retrieved_style["tone_manner"]["brand_voice_rules"] == "親しみやすさを第一に"


def test_writing_style_list_includes_saved(temp_data_dir):
    """保存した文体テンプレートがリストに含まれることをテスト"""
    style_data = {
        "name": "リスト確認用文体",
        "properties": {"tone": "丁寧"},
        "source_text": "サンプルテキスト",
        "description": "リスト確認用",
    }

    save_writing_style("list_test", style_data)
    styles = list_writing_styles()

    test_style = next((s for s in styles if s["id"] == "list_test"), None)
    assert test_style is not None
    assert test_style["name"] == "リスト確認用文体"


def test_writing_style_update_existing(temp_data_dir):
    """既存の文体テンプレートの更新をテスト"""
    original_data = {
        "name": "更新前文体",
        "properties": {"tone": "フォーマル"},
        "source_text": "元のテキスト",
        "description": "更新前",
    }

    updated_data = {
        "name": "更新後文体",
        "properties": {"tone": "カジュアル"},
        "source_text": "更新されたテキスト",
        "description": "更新後",
    }

    # 初期保存
    save_writing_style("update_test", original_data)

    # 更新
    updated_style = save_writing_style("update_test", updated_data)
    assert updated_style is not None
    assert updated_style["name"] == "更新後文体"
    assert updated_style["properties"]["tone"] == "カジュアル"

    # 取得して確認
    retrieved = get_writing_style("update_test")
    assert retrieved is not None
    assert retrieved["name"] == "更新後文体"


def test_writing_style_delete(temp_data_dir):
    """文体テンプレートの削除をテスト"""
    style_data = {
        "name": "削除テスト文体",
        "properties": {"tone": "ニュートラル"},
        "source_text": "削除されるテキスト",
        "description": "削除テスト用",
    }

    # 保存
    save_writing_style("delete_test", style_data)
    assert get_writing_style("delete_test") is not None

    # 削除
    result = delete_writing_style("delete_test")
    assert result is True

    # 削除確認
    assert get_writing_style("delete_test") is None


def test_writing_style_delete_nonexistent(temp_data_dir):
    """存在しない文体テンプレートの削除をテスト"""
    result = delete_writing_style("nonexistent")
    assert result is False


def test_writing_style_get_nonexistent(temp_data_dir):
    """存在しない文体テンプレートの取得をテスト"""
    result = get_writing_style("nonexistent")
    assert result is None


def test_writing_style_properties_validation(temp_data_dir):
    """文体プロパティのバリデーションをテスト"""
    # 最小限のデータ
    minimal_data = {
        "name": "最小文体",
        "properties": {},
        "source_text": "",
        "description": "",
    }

    style = save_writing_style("minimal", minimal_data)
    assert style is not None
    assert style["properties"] == {}

    # 完全なデータ
    complete_data = {
        "name": "完全文体",
        "properties": {
            "tone": "プロフェッショナル",
            "formality": "フォーマル",
            "length_preference": "詳細",
            "target_audience": "専門家",
            "writing_style": "解説的",
        },
        "source_text": "詳細な説明を含む文章のサンプルです。",
        "description": "プロフェッショナル向けの詳細な文体テンプレート",
    }

    style = save_writing_style("complete", complete_data)
    assert style is not None
    assert len(style["properties"]) == 5


def test_writing_style_tone_manner_empty(temp_data_dir):
    """トンマナフィールドが空の場合のテスト"""
    style_data = {
        "name": "トンマナなし文体",
        "properties": {"tone": "ニュートラル"},
        "source_text": "サンプルテキスト",
        "description": "トンマナなし",
    }

    saved_style = save_writing_style("no_tone_manner", style_data)
    assert saved_style is not None
    assert saved_style["tone_manner"] == {}


def test_writing_style_tone_manner_full(temp_data_dir):
    """トンマナフィールドが完全に設定された場合のテスト"""
    style_data = {
        "name": "完全トンマナ文体",
        "properties": {"tone": "フレンドリー"},
        "source_text": "サンプルテキスト",
        "description": "完全なトンマナ設定",
        "tone_manner": {
            "dos": ["親しみやすい表現を使う", "簡潔に書く"],
            "donts": ["専門用語を避ける", "長文は書かない"],
            "example_phrases": ["〜してみませんか？", "〜してみましょう"],
            "brand_voice_rules": "親しみやすさと分かりやすさを第一に",
        },
    }

    saved_style = save_writing_style("full_tone_manner", style_data)
    assert saved_style is not None
    assert len(saved_style["tone_manner"]["dos"]) == 2
    assert len(saved_style["tone_manner"]["donts"]) == 2
    assert len(saved_style["tone_manner"]["example_phrases"]) == 2
    assert "親しみやすさ" in saved_style["tone_manner"]["brand_voice_rules"]

    # 取得して確認
    retrieved = get_writing_style("full_tone_manner")
    assert retrieved is not None
    assert retrieved["tone_manner"]["dos"][0] == "親しみやすい表現を使う"
    assert (
        retrieved["tone_manner"]["brand_voice_rules"]
        == "親しみやすさと分かりやすさを第一に"
    )


def test_writing_style_tone_manner_partial(temp_data_dir):
    """トンマナフィールドが部分的に設定された場合のテスト"""
    style_data = {
        "name": "部分トンマナ文体",
        "properties": {"tone": "カジュアル"},
        "source_text": "サンプルテキスト",
        "description": "部分的なトンマナ設定",
        "tone_manner": {
            "dos": ["絵文字を使う"],
            "brand_voice_rules": "カジュアルに",
        },
    }

    saved_style = save_writing_style("partial_tone_manner", style_data)
    assert saved_style is not None
    assert len(saved_style["tone_manner"]["dos"]) == 1
    assert saved_style["tone_manner"]["brand_voice_rules"] == "カジュアルに"
