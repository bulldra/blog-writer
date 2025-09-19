# Blog Writer 仕様書

## 1. 概要

Blog Writerは、AI（Gemini）を活用したブログ記事生成システムです。
FastAPI + Next.jsを使用し、記事の下書き生成から編集、保存、公開まで一連の機能を提供します。

### 主要機能

- **AI記事生成**: Gemini API を使用した高品質な記事生成
- **記事テンプレート**: 多様なテンプレートによる記事生成の型化
- **ウィジェット機能**: Notion、URL、Selenium等を活用した情報収集
- **文体管理**: 文体テンプレートの作成・管理・適用
- **下書き管理**: 生成した記事の保存・編集・履歴管理
- **EPUB連携**: EPUBファイルからのハイライト抽出・活用
- **認証機能**: Google OAuth による安全なアクセス制御
- **Obsidian連携**: Obsidianワークスペースとの統合

## 2. アーキテクチャ

### システム構成

```
Frontend (Next.js) ← → Backend (FastAPI) ← → External APIs
     │                        │              │
     │                        │              ├─ Gemini API
     │                        │              ├─ Notion API (MCP)
     │                        │              ├─ Google OAuth
     │                        │              └─ External URLs
     │                        │
     │                        └─ Storage Layer
     │                               │
     └─ Static Files               ├─ SQLite (highlights)
                                   ├─ JSON Files (settings, drafts)
                                   └─ File System (epub, images)
```

### 技術スタック

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Next.js 14 (TypeScript, React 18)
- **AI**: Google Gemini API (2.5-pro, 2.5-flash)
- **Database**: SQLite (ハイライト管理)
- **Storage**: JSON ファイル (設定、下書き)
- **認証**: Google OAuth 2.0
- **パッケージ管理**: uv (Python), npm (Node.js)

## 3. 機能仕様

### 3.1 記事生成

#### テンプレートベース生成
- **記事テンプレート**: URL分析、書評、ノート等の定型フォーマット
- **フィールド設定**: テンプレートごとのカスタムフィールド
- **プロンプト管理**: テンプレート毎の最適化されたプロンプト

#### ウィジェット機能
- **Notion**: MCP経由でのページ取得・検索
- **URL分析**: Webページの内容抽出・要約
- **Selenium**: スクリーンショット撮影・動的コンテンツ取得
- **EPUB**: ハイライト箇所の抽出・コンテキスト活用

#### AI生成プロセス
1. **情報収集**: ウィジェットによる関連情報の取得
2. **プランニング**: AI による記事構成の計画
3. **TODO管理**: 生成項目の段階的実行
4. **記事生成**: 文体適用済みの最終記事作成
5. **レビュー**: 生成内容の確認・修正

### 3.2 文体管理

#### 文体テンプレート
- **プロパティ設定**: トーン、形式、スタイル等の文体特性
- **サンプルテキスト**: 文体の参考例
- **適用機能**: 記事生成時の文体自動適用

#### 文体比較
- **一覧表示**: 複数文体の特性比較
- **Markdown生成**: 文体仕様書の自動生成

### 3.3 下書き管理

#### CRUD操作
- **作成**: AI生成記事の自動保存
- **一覧**: 下書きリストの表示・検索
- **編集**: リアルタイム編集・プレビュー
- **削除**: 不要な下書きの削除

#### 履歴管理
- **生成履歴**: プロンプト、パラメータ、結果の記録
- **バージョン管理**: 編集履歴の追跡

### 3.4 EPUB機能

#### ハイライト管理
- **抽出**: EPUBファイルからのハイライト自動抽出
- **データベース**: SQLiteによる構造化保存
- **検索**: 書籍・章・内容による検索機能
- **コンテキスト活用**: 記事生成時の参考資料として活用

## 4. API仕様

### 4.1 認証API

- `GET /api/auth/login` - Google OAuth ログイン開始
- `GET /api/auth/callback` - OAuth コールバック処理
- `GET /api/auth/user` - ユーザー情報取得
- `POST /api/auth/logout` - ログアウト処理

### 4.2 AI生成API

- `GET/POST /api/ai/settings` - AI設定の取得・保存
- `POST /api/ai/generate` - 記事生成実行
- `POST /api/ai/stream` - ストリーミング生成

### 4.3 記事管理API

- `GET /api/article-templates` - テンプレート一覧
- `GET /api/article-templates/{type}` - 特定テンプレート取得
- `POST /api/article-templates/{type}` - テンプレート保存
- `DELETE /api/article-templates/{type}` - テンプレート削除

### 4.4 下書きAPI

- `GET /api/drafts` - 下書き一覧取得
- `POST /api/drafts` - 下書き作成
- `GET /api/drafts/{id}` - 特定下書き取得
- `PUT /api/drafts/{id}` - 下書き更新
- `DELETE /api/drafts/{id}` - 下書き削除

### 4.5 文体API

- `GET /api/writing-styles` - 文体一覧取得
- `POST /api/writing-styles` - 文体作成
- `GET /api/writing-styles/{id}` - 文体取得
- `PUT /api/writing-styles/{id}` - 文体更新
- `DELETE /api/writing-styles/{id}` - 文体削除

### 4.6 履歴管理API

- `GET /api/generation-history` - 生成履歴一覧取得
- `POST /api/generation-history` - 生成履歴保存
- `GET /api/generation-history/{id}` - 特定履歴取得
- `DELETE /api/generation-history/{id}` - 履歴削除

### 4.7 EPUB API

- `POST /api/epub/upload` - EPUBファイルアップロード
- `GET /api/epub/books` - 書籍一覧取得
### 4.7 EPUB API

- `POST /api/epub/upload` - EPUBファイルアップロード
- `GET /api/epub/books` - 書籍一覧取得
- `GET /api/epub/highlights` - ハイライト一覧取得
- `POST /api/epub/highlights/toggle` - ハイライト選択切替

### 4.8 テンプレートAPI

- `GET /api/templates` - プロンプトテンプレート一覧取得
- `POST /api/templates` - プロンプトテンプレート作成・更新
- `DELETE /api/templates` - プロンプトテンプレート削除

### 4.9 画像API

- `POST /api/images/eyecatch` - アイキャッチ画像生成

### 4.11 マイグレーションAPI

- `POST /api/migrate/article-templates/{type}/migrate-from-prompt` - プロンプトテンプレートから記事テンプレートへの移行

### 4.12 外部連携API

#### Notion連携
- `GET/POST /api/notion/settings` - Notion設定
- `POST /api/notion/test-connection` - 接続テスト
- `GET /api/notion/pages` - ページ一覧取得
- `POST /api/notion/search` - ページ検索
- `POST /api/notion/create-page` - ページ作成

#### Obsidian連携
- `GET/POST /api/obsidian/settings` - Obsidian設定
- `POST /api/obsidian/test-connection` - 接続テスト
- `GET /api/obsidian/files` - ファイル一覧取得
- `GET /api/obsidian/file/{filename}` - ファイル内容取得

## 5. データ仕様

### 5.1 設定データ (JSON)

```json
{
  "provider": "gemini|lmstudio",
  "model": "gemini-2.5-pro|gemini-2.5-flash",
  "api_key": "暗号化されたAPIキー",
  "max_prompt_len": 32768
}
```

### 5.2 下書きデータ (JSON)

```json
{
  "id": "uuid",
  "title": "記事タイトル",
  "content": "Markdown本文",
  "created_at": "ISO8601日時",
  "updated_at": "ISO8601日時",
  "template_type": "テンプレートタイプ",
  "metadata": {
    "prompt": "使用プロンプト",
    "settings": "生成時設定"
  }
}
```

### 5.3 文体データ (JSON)

```json
{
  "id": "uuid",
  "name": "文体名",
  "description": "説明",
  "properties": {
    "tone": "フレンドリー",
    "formality": "カジュアル"
  },
  "source_text": "参考テキスト",
  "created_at": "ISO8601日時",
  "updated_at": "ISO8601日時"
}
```

### 5.4 履歴データ (JSON)

```json
{
  "id": "uuid",
  "title": "記事タイトル",
  "template_type": "テンプレートタイプ",
  "widgets_used": ["widget1", "widget2"],
  "properties": {
    "key1": "value1",
    "key2": "value2"
  },
  "generated_content": "生成された内容",
  "reasoning": "生成理由・思考過程",
  "created_at": "ISO8601日時"
}
```

### 5.5 ハイライトデータ (SQLite)

```sql
CREATE TABLE epub_highlights (
    id INTEGER PRIMARY KEY,
    book_title VARCHAR(500) NOT NULL,
    chapter_title VARCHAR(500) NOT NULL,
    highlighted_text TEXT NOT NULL,
    context_before TEXT,
    context_after TEXT,
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    selected_for_context BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 6. セキュリティ仕様

### 6.1 認証・認可

- **Google OAuth 2.0**: ユーザー認証
- **セッション管理**: サーバーサイドセッション
- **CORS設定**: フロントエンド限定アクセス

### 6.2 データ保護

- **暗号化**: APIキー等の機密情報暗号化
- **URL検証**: 外部URL アクセス時の安全性確認
- **入力検証**: すべてのユーザー入力の検証

## 7. 運用仕様

### 7.1 ログ管理

- **ファイル出力**: `log/app.log` への統一ログ出力
- **ローテーション**: 5MB毎、3世代保持
- **レベル**: INFO以上をログ出力

### 7.2 ディレクトリ構成

```
blog-writer/
├── app/                    # FastAPI アプリケーション
│   ├── routers/           # API ルーター
│   ├── models.py          # データベースモデル
│   ├── storage.py         # ストレージ操作
│   └── main.py            # アプリケーションエントリポイント
├── web/                   # Next.js フロントエンド
│   ├── app/               # App Router
│   └── components/        # React コンポーネント
├── data/                  # アプリケーションデータ
│   ├── settings.json      # AI設定
│   ├── drafts.json        # 下書きデータ
│   └── writing_styles.json # 文体データ
├── cache/                 # キャッシュファイル
├── log/                   # ログファイル
├── test/                  # テストコード
└── docs/                  # ドキュメント
```

### 7.3 パフォーマンス

- **AI生成**: ストリーミング対応による応答性向上
- **キャッシュ**: EPUB処理結果のキャッシュ化
- **非同期処理**: ウィジェット処理の並列実行

## 8. テスト仕様

### 8.1 テスト方針

- **TDD**: t-wada流 Test-Driven Development
- **カバレッジ**: 90%以上の目標設定
- **モック**: 外部API呼び出しのモック化

### 8.2 テスト分類

- **単体テスト**: 各モジュールの個別機能テスト
- **統合テスト**: API エンドポイントのテスト
- **E2Eテスト**: フロントエンド連携テスト

### 8.3 実行環境

- **フレームワーク**: pytest
- **実行コマンド**: `uv run pytest`
- **継続的実行**: `uv run pytest --watch`