"""MDファイル生成ユーティリティ"""

from datetime import UTC, datetime
from typing import Dict, Any


def generate_writing_style_markdown(style_data: Dict[str, Any]) -> str:
    """
    文体テンプレートからMarkdownファイルを生成

    Args:
        style_data: 文体テンプレートデータ

    Returns:
        生成されたMarkdownファイルの内容
    """
    name = style_data.get("name", "無題文体")
    description = style_data.get("description", "")
    source_text = style_data.get("source_text", "")
    properties = style_data.get("properties", {})
    created_at = style_data.get("created_at", "")
    updated_at = style_data.get("updated_at", "")

    # メタデータセクション
    metadata_lines = [
        "---",
        f"title: {name}",
        f"created: {created_at}",
        f"updated: {updated_at}",
        "type: writing-style-template",
        "---",
        "",
    ]

    # タイトルと説明
    content_lines = [
        f"# {name}",
        "",
    ]

    if description:
        content_lines.extend(
            [
                "## 説明",
                "",
                description,
                "",
            ]
        )

    # 文体プロパティ
    if properties:
        content_lines.extend(
            [
                "## 文体プロパティ",
                "",
            ]
        )

        for key, value in properties.items():
            content_lines.extend(
                [
                    f"### {key}",
                    "",
                    str(value),
                    "",
                ]
            )

    # 元となる文章
    if source_text:
        content_lines.extend(
            [
                "## 元となる文章",
                "",
                "```",
                source_text,
                "```",
                "",
            ]
        )

    # 使用例
    content_lines.extend(
        [
            "## 使用方法",
            "",
            "この文体テンプレートは記事生成時に選択することで、以下の特徴を持つ文章を生成できます：",
            "",
        ]
    )

    if properties:
        for key, value in properties.items():
            content_lines.append(f"- **{key}**: {value}")
        content_lines.append("")

    # フッター
    content_lines.extend(
        [
            "---",
            "",
            f"*Generated on {datetime.now(UTC).isoformat()}*",
        ]
    )

    return "\n".join(metadata_lines + content_lines)


def generate_style_comparison_markdown(styles: list[Dict[str, Any]]) -> str:
    """
    複数の文体テンプレートの比較表をMarkdownで生成

    Args:
        styles: 文体テンプレートのリスト

    Returns:
        比較表のMarkdown
    """
    if not styles:
        return "# 文体テンプレート比較\n\n文体テンプレートがありません。"

    lines = [
        "# 文体テンプレート比較",
        "",
        f"更新日時: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # すべてのプロパティキーを収集
    all_property_keys = set()
    for style in styles:
        properties = style.get("properties", {})
        all_property_keys.update(properties.keys())

    property_keys = sorted(all_property_keys)

    # テーブルヘッダー
    header = ["文体名", "説明"] + property_keys
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    # テーブル行
    for style in styles:
        name = style.get("name", "無題")
        description = style.get("description", "")[:50]  # 50文字まで
        if len(style.get("description", "")) > 50:
            description += "..."

        properties = style.get("properties", {})

        row = [name, description]
        for key in property_keys:
            value = properties.get(key, "")
            row.append(str(value)[:30])  # 30文字まで

        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## 詳細",
            "",
        ]
    )

    # 各文体の詳細
    for style in styles:
        name = style.get("name", "無題")
        description = style.get("description", "")
        source_text = style.get("source_text", "")
        properties = style.get("properties", {})

        lines.extend(
            [
                f"### {name}",
                "",
            ]
        )

        if description:
            lines.extend(
                [
                    f"**説明**: {description}",
                    "",
                ]
            )

        if properties:
            lines.append("**プロパティ**:")
            for key, value in properties.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        if source_text:
            lines.extend(
                [
                    "**サンプルテキスト**:",
                    "```",
                    source_text[:200] + ("..." if len(source_text) > 200 else ""),
                    "```",
                    "",
                ]
            )

    return "\n".join(lines)
