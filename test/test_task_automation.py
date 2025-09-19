"""タスク自動化システムのテスト"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from app.task_automation import (
    TaskParser, TaskAutomationManager, TaskExecutor,
    Task, TaskStatus, TaskType
)


@pytest.fixture
def sample_tasks_content():
    """テスト用のタスクファイル内容"""
    return """# 開発タスク

## 完了済み
-   [x] UI コンポーネントの分割
-   [x] API エンドポイントの追加

## 未完了
-   [ ] スクリーンショット画像の UI プレビューを追加（writer/AI の入出力）
-   [ ] 詳細画面で説明文の AI 提案（自動入力）を追加
-   [ ] テンプレート一覧の編集リンクは不要で、行クリックで詳細画面に遷移
-   [ ] pytest の実行
-   [ ] ドキュメント更新
"""


@pytest.fixture
def temp_tasks_file(sample_tasks_content):
    """一時的なタスクファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(sample_tasks_content)
        temp_file = f.name
    
    yield temp_file
    
    # クリーンアップ
    os.unlink(temp_file)


class TestTaskParser:
    """TaskParserのテスト"""
    
    def test_parse_tasks_with_valid_file(self, temp_tasks_file):
        """正常なタスクファイルの解析"""
        parser = TaskParser(temp_tasks_file)
        tasks = parser.parse_tasks()
        
        assert len(tasks) == 7
        
        # 完了タスクのテスト
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        assert len(completed_tasks) == 2
        assert "UI コンポーネントの分割" in completed_tasks[0].text
        
        # 未完了タスクのテスト
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        assert len(pending_tasks) == 5
        
        # 自動実行可能タスクのテスト
        auto_tasks = [t for t in tasks if t.auto_executable]
        assert len(auto_tasks) >= 1
        
        # 特定のタスクをチェック
        ai_suggestion_task = next(
            (t for t in tasks if "AI 提案" in t.text), None
        )
        assert ai_suggestion_task is not None
        assert ai_suggestion_task.auto_executable
        assert ai_suggestion_task.status == TaskStatus.PENDING
    
    def test_parse_tasks_with_nonexistent_file(self):
        """存在しないファイルの処理"""
        parser = TaskParser("nonexistent.md")
        tasks = parser.parse_tasks()
        assert tasks == []
    
    def test_classify_task_type(self, temp_tasks_file):
        """タスクタイプの分類テスト"""
        parser = TaskParser(temp_tasks_file)
        
        # UI関連
        assert parser._classify_task_type("UI プレビューを追加") == TaskType.UI_ENHANCEMENT
        assert parser._classify_task_type("画面表示の改善") == TaskType.UI_ENHANCEMENT
        
        # 機能追加
        assert parser._classify_task_type("新機能を追加する") == TaskType.FEATURE_ADDITION
        assert parser._classify_task_type("ウィジェット追加") == TaskType.FEATURE_ADDITION
        
        # テスト
        assert parser._classify_task_type("pytest の実行") == TaskType.TESTING
        assert parser._classify_task_type("テスト追加") == TaskType.TESTING
        
        # ドキュメント
        assert parser._classify_task_type("ドキュメント更新") == TaskType.DOCUMENTATION
        assert parser._classify_task_type("README修正") == TaskType.DOCUMENTATION
    
    def test_auto_executable_detection(self, temp_tasks_file):
        """自動実行可能判定のテスト"""
        parser = TaskParser(temp_tasks_file)
        
        # 自動実行可能
        assert parser._is_auto_executable("AI 提案（自動入力）")
        assert parser._is_auto_executable("テスト実行")
        assert parser._is_auto_executable("ドキュメント更新")
        
        # 自動実行不可
        assert not parser._is_auto_executable("手動でUIを修正")
        assert not parser._is_auto_executable("レビューを実施")


class TestTaskExecutor:
    """TaskExecutorのテスト"""
    
    def test_execute_auto_executable_task(self):
        """自動実行可能タスクの実行"""
        executor = TaskExecutor()
        
        task = Task(
            id=1,
            text="AI 提案（自動入力）を追加",
            status=TaskStatus.PENDING,
            task_type=TaskType.FEATURE_ADDITION,
            line_number=10,
            auto_executable=True
        )
        
        result = executor.execute_task(task)
        
        assert result["success"] is True
        assert result["task_id"] == 1
        assert "処理されました" in result["message"]
    
    def test_execute_non_auto_executable_task(self):
        """自動実行不可タスクの実行"""
        executor = TaskExecutor()
        
        task = Task(
            id=2,
            text="手動でレビューを実施",
            status=TaskStatus.PENDING,
            task_type=TaskType.UNKNOWN,
            line_number=11,
            auto_executable=False
        )
        
        result = executor.execute_task(task)
        
        assert result["success"] is False
        assert result["task_id"] == 2
        assert "自動実行対象外" in result["message"]
    
    def test_execute_task_with_unknown_type(self):
        """未知のタスクタイプの実行"""
        executor = TaskExecutor()
        
        task = Task(
            id=3,
            text="未知のタスク",
            status=TaskStatus.PENDING,
            task_type=TaskType.UNKNOWN,
            line_number=12,
            auto_executable=True
        )
        
        result = executor.execute_task(task)
        
        assert result["success"] is False
        assert result["task_id"] == 3
        assert "ハンドラーが見つかりません" in result["message"]


class TestTaskAutomationManager:
    """TaskAutomationManagerのテスト"""
    
    def test_get_pending_tasks(self, temp_tasks_file):
        """未完了タスク取得のテスト"""
        manager = TaskAutomationManager(temp_tasks_file)
        pending_tasks = manager.get_pending_tasks()
        
        assert len(pending_tasks) == 5
        assert all(task.status == TaskStatus.PENDING for task in pending_tasks)
    
    def test_get_auto_executable_tasks(self, temp_tasks_file):
        """自動実行可能タスク取得のテスト"""
        manager = TaskAutomationManager(temp_tasks_file)
        auto_tasks = manager.get_auto_executable_tasks()
        
        assert len(auto_tasks) >= 1
        assert all(task.auto_executable for task in auto_tasks)
        assert all(task.status == TaskStatus.PENDING for task in auto_tasks)
    
    def test_get_task_summary(self, temp_tasks_file):
        """タスク要約取得のテスト"""
        manager = TaskAutomationManager(temp_tasks_file)
        summary = manager.get_task_summary()
        
        assert "total_tasks" in summary
        assert "completed_tasks" in summary
        assert "pending_tasks" in summary
        assert "auto_executable_tasks" in summary
        assert "task_types_distribution" in summary
        assert "pending_task_details" in summary
        
        assert summary["total_tasks"] == 7
        assert summary["completed_tasks"] == 2
        assert summary["pending_tasks"] == 5
        assert summary["auto_executable_tasks"] >= 1
    
    @patch('app.task_automation.TaskExecutor.execute_task')
    def test_execute_all_auto_tasks(self, mock_execute, temp_tasks_file):
        """すべての自動実行可能タスクの実行テスト"""
        # モックの設定
        mock_execute.return_value = {
            "success": True,
            "message": "テスト実行成功",
            "task_id": 1
        }
        
        manager = TaskAutomationManager(temp_tasks_file)
        result = manager.execute_all_auto_tasks()
        
        assert result["success"] is True
        assert result["executed_count"] >= 1
        assert result["success_count"] >= 1
        assert len(result["results"]) >= 1
    
    def test_execute_all_auto_tasks_no_tasks(self):
        """自動実行可能タスクがない場合のテスト"""
        # 自動実行可能タスクがないファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# タスク\n-   [x] 完了タスク\n-   [ ] 手動タスク")
            temp_file = f.name
        
        try:
            manager = TaskAutomationManager(temp_file)
            result = manager.execute_all_auto_tasks()
            
            assert result["success"] is True
            assert result["executed_count"] == 0
            assert "自動実行可能なタスクはありません" in result["message"]
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])