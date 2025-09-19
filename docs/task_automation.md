# タスク自動実行システム

`docs/tasks.md` のタスクを自動的に処理・実行するシステムです。

## 概要

このシステムは以下の機能を提供します：

- `docs/tasks.md` のタスク解析
- 自動実行可能なタスクの特定
- タスクの自動実行
- タスクファイルの監視
- Web API による制御

## システム構成

```
app/
├── task_automation.py     # コアロジック
└── routers/
    └── tasks.py          # Web API エンドポイント

scripts/
├── task_automation_cli.py # CLI インターフェース
├── task_scheduler.py      # 定期実行スクリプト
└── task_watcher.py        # ファイル監視スクリプト

docs/
└── tasks.md              # タスクファイル
```

## 使用方法

### 1. CLI による操作

#### タスク一覧表示
```bash
python scripts/task_automation_cli.py list
python scripts/task_automation_cli.py list --show-completed  # 完了タスクも表示
```

#### タスク要約表示
```bash
python scripts/task_automation_cli.py summary
python scripts/task_automation_cli.py summary --json  # JSON形式
```

#### タスク実行
```bash
python scripts/task_automation_cli.py execute
python scripts/task_automation_cli.py execute --dry-run  # ドライラン
```

### 2. 定期実行

cron や systemd timer で定期実行する場合：

```bash
# 毎時実行
python scripts/task_scheduler.py

# crontab の例
0 * * * * cd /path/to/blog-writer && python scripts/task_scheduler.py
```

### 3. ファイル監視

タスクファイルの変更を監視して自動実行：

```bash
python scripts/task_watcher.py
```

### 4. Web API

#### タスク要約取得
```
GET /api/tasks/summary
```

#### 未完了タスク一覧
```
GET /api/tasks/pending
```

#### 自動実行可能タスク一覧
```
GET /api/tasks/auto-executable
```

#### タスク実行
```
POST /api/tasks/execute?dry_run=false
```

#### タスクファイル再読み込み
```
GET /api/tasks/refresh
```

## タスクの分類

システムは以下の基準でタスクを分類します：

### タスクタイプ
- `ui_enhancement`: UI改善
- `feature_addition`: 機能追加
- `bug_fix`: バグ修正
- `documentation`: ドキュメント
- `testing`: テスト
- `refactoring`: リファクタリング

### 自動実行可能性

以下のキーワードを含むタスクは自動実行可能と判定されます：
- `ai 提案`
- `自動入力`
- `テスト実行`
- `コード整理`
- `ドキュメント更新`

## タスクファイル形式

`docs/tasks.md` は以下の形式で記述してください：

```markdown
# タスクリスト

-   [x] 完了したタスク
-   [ ] 未完了のタスク
-   [ ] AI 提案（自動入力）を追加  # 自動実行可能
```

## ログ

実行ログは以下に出力されます：
- `log/task_automation.log` - 定期実行ログ
- `log/task_watcher.log` - ファイル監視ログ
- `log/app.log` - API実行ログ

## 設定

### 環境変数
- `TASKS_FILE`: タスクファイルのパス（デフォルト: `docs/tasks.md`）
- `LOG_LEVEL`: ログレベル（デフォルト: `INFO`）

### カスタマイズ

`app/task_automation.py` の以下のメソッドをカスタマイズして、
自動実行の条件や処理ロジックを変更できます：

- `_classify_task_type()`: タスクタイプの分類ロジック
- `_is_auto_executable()`: 自動実行可能性の判定ロジック
- `_handle_*()`: 各タスクタイプの実行ロジック

## テスト

```bash
python -m pytest test/test_task_automation.py -v
```

## 注意事項

- 自動実行は慎重に設計されており、危険な操作は手動実行が必要です
- 現在は基本的なタスクハンドラーのみ実装されています
- 本格的な自動実行には追加の開発が必要です

## 今後の拡張予定

- [ ] より高度なタスク依存関係の処理
- [ ] タスクの優先度に基づいた実行順序制御
- [ ] 外部システムとの連携（GitHub Issues、Notion等）
- [ ] タスクテンプレートの自動生成
- [ ] 実行結果のレポート機能