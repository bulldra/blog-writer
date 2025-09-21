# Blog Writer — FastAPI + Next.js (uv)

機能

-   AI: ブログ下書き生成（Gemini／API キーはサーバに保存可能）
-   辞書: 用語の簡易定義（スタブ）
-   いい回し登録: よく使う表現の保存/参照
-   下書き保存: 生成結果を保存・一覧・編集・削除（JSON ファイルに永続化）
-   Notion MCP: Notion 連携による情報取得と記事記録

構成

-   backend: FastAPI (`/app`)
-   frontend: Next.js (`/web`)
-   ストレージ: `data/settings.json` / `data/drafts.json`（暗号化は APP_SECRET 指定時に有効）
-   パッケージ管理: uv + pyproject.toml

開発サーバ起動

前提: Node は 20 LTS を推奨（Node 22 では Next.js 14 の dev 実行で
webpack ランタイムの欠損モジュールに遭遇する既知事象があります）。
プロジェクト直下の `.nvmrc` は `20` を指定しています。

1. Python 依存のインストール（プロジェクトルートで）
    - uv sync（`uv.lock` があるため基本は凍結インストール）
2. 開発用統合スクリプトで起動（推奨）
    - scripts/dev.sh
        - API: http://127.0.0.1:8000
        - Web: http://localhost:3000
    - dev.sh は FastAPI のリロード対象を `app/**/*.py` に限定し、
      `web/**` の変更では API を再起動しないようにしています。
    - Node バージョンが 21 以上の場合は警告を出します。
3. フロント/バックを個別に起動する場合
    - FastAPI（プロジェクトルート）
        - uv run fastapi dev app/main.py
    - Next.js（web ディレクトリ）
        - npm ci
        - npm run dev

API エンドポイント（抜粋）

-   GET /api/health
-   GET /api/ai/settings / POST /api/ai/settings
-   POST /api/ai/generate
-   GET /api/dict?term=...
-   GET/POST/DELETE /api/phrases
-   GET/POST /api/drafts
-   GET/PUT/DELETE /api/drafts/{id}
-   GET/POST /api/notion/settings
-   POST /api/notion/test-connection
-   GET /api/notion/pages
-   POST /api/notion/search
-   POST /api/notion/create-page
-   POST /api/notion/publish-article

テンプレート管理/ウィジェット（抜粋）

-   GET /api/article-templates
-   GET/POST/DELETE /api/article-templates/{t}
-   POST /api/article-templates/{t}/duplicate
-   GET /api/article-templates/{t}/versions
-   GET /api/article-templates/{t}/versions/{version}
-   GET /api/article-templates/{t}/diff?from_version=...&to_version=...
-   GET /api/article-templates/widgets/available
-   POST /api/widgets/scrape/preview

フロント

-   トップ `/` で生成と保存
-   `/settings` で AI 設定（Gemini/LM Studio）、Obsidian/EPUB ディレクトリ設定
-   Obsidian/EPUB は「選択…」ボタンからディレクトリピッカーで設定可能
-   `/drafts` で保存一覧と編集・削除

## 記事テンプレート管理（/templates）

テンプレートの一覧・編集 UI を提供します。詳細ページでは以下が可能です。

-   モード設定: 計画/発想/実行/整理/学習（plan/ideate/execute/organize/learn）
-   文体選択: プロンプト内で `{{style}}` を使用すると選択した文体名が反映されます
-   ウィジェット管理: 複数追加・ドラッグ&ドロップで並べ替え・変数ボタンで挿入
-   JSON インポート/エクスポート: 設定の保存/復元に対応
-   静的検証: 未使用のフィールド/ウィジェット変数、未知変数、文体未使用を警告
-   バージョン履歴/差分: 保存時にスナップショットを記録し直近の変更点を表示
-   スクレイプウィジェットのサンドボックスプレビュー:
    -   URL・CSS セレクタ・取得モード（text/screenshot/both）を指定して単体プレビュー
    -   バックエンド `/api/widgets/scrape/preview` を使用（ヘッドレス/タイムアウトあり）

注意:

-   文体を選んでもプロンプトに `{{style}}` が無いと反映されません（UI が警告します）
-   スクリーンショットは `<img>` でプレビューしています（最適化警告が出る場合あり）
-   バージョン履歴は内容が変化した保存時のみ増えます（重複スナップショットを抑制）

## Notion MCP 連携

### 概要

Model Context Protocol (MCP) を通じて Notion との連携を提供します。
Python クライアントは fast-mcp を使用します（フォールバックなし）。

### 機能

-   Notion ページの情報取得
-   ページ検索
-   記事作成時の Notion ページコンテキスト利用
-   生成した記事の Notion への投稿

### 設定方法

1. Notion API キーの取得

    - [Notion Developers](https://developers.notion.com/) で API キーを作成
    - 必要な権限（読み取り・書き込み）を設定

2. MCP サーバーの設定

    - NPM で Notion MCP サーバーをインストール：
        ```bash
        npm install -g @modelcontextprotocol/server-notion
        ```

    Python クライアント側（本リポジトリ）では fast-mcp を利用します（依存定義済）。

3. API 経由で設定を保存
    ```json
    {
    	"command": "npx",
    	"args": ["@modelcontextprotocol/server-notion"],
    	"env": {
    		"NOTION_API_KEY": "your_notion_api_key"
    	},
    	"enabled": true,
    	"default_parent_id": "optional_default_parent_page_id"
    }
    ```

### ウィジェット利用

記事生成時に Notion ウィジェットを使用して、Notion ページの情報をコンテキストとして活用できます。

### API 使用例

```bash
# 接続テスト
curl -X POST http://localhost:8000/api/notion/test-connection

# ページ一覧取得
curl http://localhost:8000/api/notion/pages

# 記事投稿
curl -X POST http://localhost:8000/api/notion/publish-article \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新しい記事",
    "content": "# 新しい記事\\n\\nコンテンツ..."
  }'
```

## トラブルシューティング

-   Next.js dev で `Cannot find module './xxx.js'`（webpack-runtime.js 由来）
    -   `web/.next` と `web/node_modules` を削除し、`npm ci` をやり直してから
        `scripts/dev.sh` で再起動
    -   Node が 22 系だと再発する場合があります。Node 20 LTS に切替（`.nvmrc` 利用）
