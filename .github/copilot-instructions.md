# Copilot Instructions for Blog Writer

このファイルは GitHub Copilot Coding Agent がこのリポジトリで作業する際の指針となります。

## プロジェクト概要

Blog Writer は FastAPI（バックエンド）と Next.js（フロントエンド）を組み合わせた AI ブログ記事生成アプリケーションです。
Gemini API を使用してブログ下書きを生成し、Notion MCP 連携や記事テンプレート管理機能を提供します。

## セットアップと実行

### 必須要件
- Python 3.12以上
- Node.js 20 LTS（推奨。`.nvmrc` で指定）
- uv（Python パッケージマネージャー）

### 初期セットアップ
```bash
# Python 依存関係のインストール
uv sync

# フロントエンド依存関係のインストール
cd web && npm ci && cd ..
```

### 開発サーバー起動
```bash
# 推奨: 統合開発スクリプト（FastAPI + Next.js を同時起動）
./scripts/dev.sh
# API: http://127.0.0.1:8000
# Web: http://localhost:3000

# または個別に起動
# FastAPI のみ
uv run fastapi dev app/main.py

# Next.js のみ（別ターミナル）
cd web && npm run dev
```

## ビルド、テスト、リント

### Python (バックエンド)
```bash
# テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=app --cov-report=html

# リント（Ruff）
uv run ruff check app test

# フォーマット（Black）
uv run black app test

# 型チェック（mypy）
uv run mypy app test
```

### Next.js (フロントエンド)
```bash
cd web

# リント
npm run lint

# ビルド
npm run build

# プロダクション起動
npm run start
```

### コード品質チェックの順序
コード変更後は以下の順序で実行し、全てのエラー・警告を解消すること：
1. `uv run ruff check app test` - リント
2. `uv run mypy app test` - 型チェック
3. `uv run black app test` - フォーマット
4. `uv run pytest` - テスト

## 主要な開発原則

-   Python 3.12 と Next.js 13（App Router）を使用
-   uv を利用して開発、実行、テスト
-   型ヒント必須
-   日本語で回答
-   ソースコードは `src/` ディレクトリに配置
-   テストコードは `test/` ディレクトリに配置
-   一時的なスクリプト生成やデバッグ用のコードは `scripts/` ディレクトリに配置
-   ドキュメントは `docs/` ディレクトリに配置
-   `docs/todo.md` に TODO を記載
-   余計なファイルを増やさないようにように注意
-   88 文字行長制限
-   テストは pytest 使用し、t-wada 流 TDD（Test-Driven Development）を採用
-   import-outside-toplevel になる修正を禁止し、toplevel に import 文を配置する
-   pylint: disable を使用しない
-   コメントは不要
-   テストに失敗するなら直して
-   可能な限り自律的に問題解決して
-   可能な限り、コードの可読性と保守性を向上させることを優先し無駄なコードは削除すること
-   コード修正後は以下を実行して全てのエラー、警告、インフォメーション、修正を解消するまで繰り返すこと
    -   ruff
    -   mypy
    -   black
-   修正する際にエラーを握りつぶすのではなく本質的な解決をプランニングする
-   修正後にはテストを実行し、全てのテストが通ることを確認すること
    -   pytest は uv から実行すること
-   ステップバイステップのデバックログを出力して、ログを参照しながら改善を実施
-   UI は基本的にコンポーネント化する
-   コードを修正したらサーバーの再起動を実施
-   jsx ファイルは Prettier でフォーマットすること
-   スタイルは css に分離すること
-   API エンドポイントは RESTful に設計すること
-   API エンドポイントは `/api/` で始めること
-   API エンドポイントは可能な限り CRUD 操作に対応すること
-   コンポーネント化を推進し、共通化できる部分は共通化すること
-   デザインシステムを意識して、UI コンポーネントの再利用性を高めること

## プロジェクト構造

### ディレクトリ構成
-   `app/`: FastAPI バックエンドアプリケーション
    -   `routers/`: API エンドポイント定義
    -   `models/`: データモデル（Pydantic）
    -   `ai_utils.py`: AI 関連ユーティリティ
    -   `storage.py`: データ永続化層
-   `test/`: テストファイル（pytest）
-   `web/`: Next.js フロントエンド
    -   `app/`: App Router ページとレイアウト
    -   `components/`: 再利用可能な React コンポーネント
-   `data/`: ランタイムデータ（設定、下書きなど）
-   `cache/`: キャッシュファイル
-   `scripts/`: 開発用スクリプト
-   `docs/`: プロジェクトドキュメント
-   `config/`: YAML 設定ファイル

### 主要な技術スタック
-   **バックエンド**: FastAPI, Pydantic, Google Gemini API
-   **フロントエンド**: Next.js 14 (App Router), React 18, TypeScript
-   **AI/ML**: sentence-transformers, scikit-learn (RAG/埋め込み)
-   **テスト**: pytest, pytest-asyncio, pytest-cov
-   **リント/フォーマット**: Ruff, Black, mypy, ESLint
-   **パッケージ管理**: uv (Python), npm (Node.js)

## 重要なモジュール

-   `epub_util.py`: EPUB 処理ユーティリティ
-   `embedding_util.py`: 埋め込み処理
-   `rag_util.py`: RAG 機能
-   `history_util.py`: 履歴管理
-   `server.py`: Web サーバー
-   `config_manager.py`: 設定管理（AppConfig, SmartRAGConfig）

## 設定管理

### アプリケーション設定 (`config/app_config.yaml`)

-   LLM モデル設定（開発モード、モデル名、埋め込みモデル名）
-   サーバー設定（ホスト、ポート）
-   ディレクトリ設定（epub, cache, log, config）
-   ログ設定（レベル、フォーマット、ファイル名）
-   環境変数オーバーライド設定

### Smart RAG 設定 (`config/smart_rag_config.yaml`)

-   ハイブリッド検索設定
-   BM25 設定
-   チャンク設定
-   リランキング設定

## t-wada 流 TDD 実装方針

1. テストファーストの原則を厳守
2. Red-Green-Refactor サイクルを遵守
3. まず失敗するテストを書き、次に最小限のコードで通し、最後にリファクタリング
4. テストは可読性と保守性を重視
5. テストケースは具体的で明確な名前を付ける
6. モックやスタブは必要最小限に留める
7. 統合テストよりも単体テストを優先
8. テストの実行速度を重視
9. テストコードも本番コードと同じ品質基準を適用

## テスト方針メモ（LLM 抑止）

-   pytest は外部 LLM/ネットワークに到達しないことを厳守 - `test/conftest.py` の autouse フィクスチャで以下を実施 - `app.ai_utils.call_ai` / `call_ai_stream` をスタブ - `app.routers.ai.call_ai` / `call_ai_stream` をスタブ（早期経路） - `app.storage.get_ai_settings` をスタブ（常に API キー空） - ソケットレベルで外部通信を遮断（`socket.socket.connect/connect_ex`） - `google.genai.Client` をスタブ（`models.generate_content` は固定文字列） - `httpx.AsyncClient` をスタブ（get/post/stream で即例外） - これによりテスト中にネットワークへ出る経路は強制的に失敗 → 回帰検出可能

## PR とコミットのガイドライン

### コミットメッセージ
-   簡潔で明確な単一行の説明を使用
-   日本語または英語で記述可能
-   例: "AI設定APIのバリデーションを追加", "Fix template widget rendering"

### プルリクエスト
-   タイトル: 変更内容を明確に要約
-   説明: 変更の理由と主要な変更点を記載
-   テストが通ることを確認してから PR を作成
-   全ての lint エラーと型エラーを解消
-   関連する Issue があれば参照を含める

### コードレビュー前のチェックリスト
- [ ] `uv run pytest` が全て成功
- [ ] `uv run ruff check` がエラーなし
- [ ] `uv run mypy` がエラーなし
- [ ] `uv run black` でフォーマット済み
- [ ] 変更に関連するドキュメントを更新（必要に応じて）

## よくあるタスク

### 新しい API エンドポイントの追加
1. `app/routers/` に新しいルーターを作成または既存のルーターに追加
2. `app/models/` に必要な Pydantic モデルを定義
3. `test/api/` に対応するテストを作成（t-wada 流 TDD）
4. エンドポイントは `/api/` プレフィックスを使用
5. RESTful な設計を心がける（GET, POST, PUT, DELETE）

### 新しい UI コンポーネントの追加
1. `web/app/components/` に React コンポーネントを作成
2. TypeScript で型定義を含める
3. CSS は別ファイルに分離（コンポーネントと同じディレクトリ）
4. 再利用可能な設計を意識
5. 必要に応じて SWR でデータフェッチ

### データモデルの変更
1. `app/models/` の Pydantic モデルを更新
2. 影響を受ける API エンドポイントを確認・更新
3. `app/storage.py` のシリアライゼーション/デシリアライゼーション処理を確認
4. テストを更新または追加
5. マイグレーションが必要な場合は適切に処理

## トラブルシューティング

### Next.js で `Cannot find module` エラー
```bash
# web/.next と node_modules を削除して再インストール
cd web
rm -rf .next node_modules
npm ci
cd ..
./scripts/dev.sh
```
**注意**: Node.js 22 系では webpack ランタイムの既知の問題があります。Node.js 20 LTS を使用してください（`.nvmrc` 参照）。

### pytest でネットワークエラー
テストは外部ネットワークに接続しないように設計されています。`test/conftest.py` で自動的にスタブ化されます。
ネットワークエラーが発生する場合は、モックが正しく設定されているか確認してください。

### ポート競合エラー
```bash
# 開発スクリプトは自動的にポートをクリーンアップしますが、手動で停止する場合:
./scripts/stop.sh
```

### uv sync が失敗する
```bash
# uv のキャッシュをクリア
rm -rf .venv
uv sync
```

### 型チェックエラー
-   外部ライブラリの型エラーは `pyproject.toml` の `[[tool.mypy.overrides]]` に追加
-   `ignore_missing_imports = true` を使用（プロジェクト固有のコードでは使用しない）

## 参考リソース

-   [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
-   [Next.js ドキュメント](https://nextjs.org/docs)
-   [GitHub Copilot Best Practices](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
-   プロジェクト固有のドキュメント: `docs/` ディレクトリ
