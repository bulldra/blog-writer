# Blog Writer — FastAPI + Next.js (uv)

機能

-   AI: ブログ下書き生成（Gemini／API キーはサーバに保存可能）
-   辞書: 用語の簡易定義（スタブ）
-   いい回し登録: よく使う表現の保存/参照
-   下書き保存: 生成結果を保存・一覧・編集・削除（JSON ファイルに永続化）

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

フロント

-   トップ `/` で生成と保存
-   `/settings` で Gemini API キーの保存
-   `/drafts` で保存一覧と編集・削除
