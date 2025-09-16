# Blog Writer — FastAPI + Next.js (uv)

機能

-   AI: ブログ下書き生成（Gemini／API キーはサーバに保存可能）
-   辞書: 用語の簡易定義（スタブ）
-   いい回し登録: よく使う表現の保存/参照
-   下書き保存: 生成結果を保存・一覧・編集・削除（JSON ファイルに永続化）
-   Notion MCP: Notion連携による情報取得と記事記録

構成

-   backend: FastAPI (`/app`)
-   frontend: Next.js (`/web`)
-   ストレージ: `data/settings.json` / `data/drafts.json`（暗号化は APP_SECRET 指定時に有効）
-   パッケージ管理: uv + pyproject.toml

開発サーバ起動

1. Python 依存のインストール（プロジェクトルートで）
    - uv sync
2. FastAPI を起動
    - uv run fastapi dev app/main.py
3. Next.js を起動（web ディレクトリで）
    - npm install
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

フロント

-   トップ `/` で生成と保存
-   `/settings` で Gemini API キーの保存
-   `/drafts` で保存一覧と編集・削除

## Notion MCP 連携

### 概要
Model Context Protocol (MCP) を通じてNotionとの連携を提供します。

### 機能
- Notionページの情報取得
- ページ検索
- 記事作成時のNotionページコンテキスト利用
- 生成した記事のNotionへの投稿

### 設定方法
1. Notion API キーの取得
   - [Notion Developers](https://developers.notion.com/) で API キーを作成
   - 必要な権限（読み取り・書き込み）を設定

2. MCP サーバーの設定
   - NPM で Notion MCP サーバーをインストール：
     ```bash
     npm install -g @modelcontextprotocol/server-notion
     ```

3. API経由で設定を保存
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
記事生成時に Notion ウィジェットを使用して、Notionページの情報をコンテキストとして活用できます。

### API使用例
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
