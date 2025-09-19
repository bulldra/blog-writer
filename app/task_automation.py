"""タスク自動実行システム

docs/tasks.md のタスクを解析し、自動実行可能なタスクを処理するモジュール
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """タスクのステータス"""
    COMPLETED = "completed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"


class TaskType(Enum):
    """タスクの種類"""
    UI_ENHANCEMENT = "ui_enhancement"
    FEATURE_ADDITION = "feature_addition"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    UNKNOWN = "unknown"


@dataclass
class Task:
    """個別タスクの情報"""
    id: int
    text: str
    status: TaskStatus
    task_type: TaskType
    line_number: int
    auto_executable: bool = False
    priority: int = 0
    estimated_effort: str = "medium"


class TaskParser:
    """tasks.md ファイルのパーサー"""
    
    def __init__(self, tasks_file_path: str = "docs/tasks.md"):
        self.tasks_file_path = Path(tasks_file_path)
        
    def parse_tasks(self) -> List[Task]:
        """tasks.md からタスクリストを解析"""
        if not self.tasks_file_path.exists():
            logger.error(f"タスクファイルが見つかりません: {self.tasks_file_path}")
            return []
            
        tasks = []
        
        try:
            with open(self.tasks_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                task = self._parse_task_line(line, line_num)
                if task:
                    tasks.append(task)
                    
        except Exception as e:
            logger.error(f"タスクファイルの読み込みエラー: {e}")
            
        return tasks
    
    def _parse_task_line(self, line: str, line_number: int) -> Optional[Task]:
        """個別行からタスクを解析"""
        # タスクのパターンマッチング: -   [x] または -   [ ] で始まる行
        pattern = r'^-\s+\[([x\s])\]\s+(.+)$'
        match = re.match(pattern, line.strip())
        
        if not match:
            return None
            
        status_char, text = match.groups()
        status = TaskStatus.COMPLETED if status_char.lower() == 'x' else TaskStatus.PENDING
        
        task = Task(
            id=line_number,
            text=text.strip(),
            status=status,
            task_type=self._classify_task_type(text),
            line_number=line_number,
            auto_executable=self._is_auto_executable(text),
            priority=self._estimate_priority(text),
            estimated_effort=self._estimate_effort(text)
        )
        
        return task
    
    def _classify_task_type(self, text: str) -> TaskType:
        """タスクの種類を分類"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['ui', 'プレビュー', '画面', '表示', 'ボタン', 'リンク']):
            return TaskType.UI_ENHANCEMENT
        elif any(keyword in text_lower for keyword in ['追加', '機能', 'ウィジェット', '提案']):
            return TaskType.FEATURE_ADDITION
        elif any(keyword in text_lower for keyword in ['修正', 'バグ', 'エラー', '問題']):
            return TaskType.BUG_FIX
        elif any(keyword in text_lower for keyword in ['ドキュメント', '説明', 'readme']):
            return TaskType.DOCUMENTATION
        elif any(keyword in text_lower for keyword in ['テスト', 'test', 'pytest']):
            return TaskType.TESTING
        elif any(keyword in text_lower for keyword in ['リファクタ', '整理', '共通化', '分割']):
            return TaskType.REFACTORING
        else:
            return TaskType.UNKNOWN
    
    def _is_auto_executable(self, text: str) -> bool:
        """自動実行可能かどうかを判定"""
        # 現時点では簡単なルールベースで判定
        # 将来的にはより高度な判定ロジックを実装
        auto_keywords = [
            'ai 提案',
            '自動入力',
            'テスト実行',
            'コード整理',
            'ドキュメント更新'
        ]
        
        return any(keyword in text.lower() for keyword in auto_keywords)
    
    def _estimate_priority(self, text: str) -> int:
        """タスクの優先度を推定 (1-5, 5が最高優先度)"""
        high_priority_keywords = ['緊急', 'バグ', 'エラー', '必須']
        medium_priority_keywords = ['改善', '追加', '機能']
        
        if any(keyword in text for keyword in high_priority_keywords):
            return 5
        elif any(keyword in text for keyword in medium_priority_keywords):
            return 3
        else:
            return 2
    
    def _estimate_effort(self, text: str) -> str:
        """作業量を推定"""
        if any(keyword in text for keyword in ['大幅', '全面', '大規模']):
            return "large"
        elif any(keyword in text for keyword in ['追加', '新規', '実装']):
            return "medium"
        else:
            return "small"


class TaskExecutor:
    """タスク実行エンジン"""
    
    def __init__(self):
        self.execution_handlers = {
            TaskType.UI_ENHANCEMENT: self._handle_ui_enhancement,
            TaskType.FEATURE_ADDITION: self._handle_feature_addition,
            TaskType.DOCUMENTATION: self._handle_documentation,
            TaskType.TESTING: self._handle_testing,
        }
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """個別タスクを実行"""
        logger.info(f"タスク実行開始: {task.text}")
        
        if not task.auto_executable:
            return {
                "success": False,
                "message": "このタスクは自動実行対象外です",
                "task_id": task.id
            }
        
        handler = self.execution_handlers.get(task.task_type)
        if not handler:
            return {
                "success": False,
                "message": f"タスクタイプ {task.task_type} のハンドラーが見つかりません",
                "task_id": task.id
            }
        
        try:
            result = handler(task)
            logger.info(f"タスク実行完了: {task.text}")
            return result
        except Exception as e:
            logger.error(f"タスク実行エラー: {task.text}, Error: {e}")
            return {
                "success": False,
                "message": f"実行中にエラーが発生しました: {e}",
                "task_id": task.id
            }
    
    def _handle_ui_enhancement(self, task: Task) -> Dict[str, Any]:
        """UI改善タスクの処理"""
        # UI改善タスクの自動処理ロジック
        return {
            "success": True,
            "message": "UI改善タスクが処理されました（プレースホルダー）",
            "task_id": task.id,
            "actions_taken": []
        }
    
    def _handle_feature_addition(self, task: Task) -> Dict[str, Any]:
        """機能追加タスクの処理"""
        # 機能追加タスクの自動処理ロジック
        return {
            "success": True,
            "message": "機能追加タスクが処理されました（プレースホルダー）",
            "task_id": task.id,
            "actions_taken": []
        }
    
    def _handle_documentation(self, task: Task) -> Dict[str, Any]:
        """ドキュメント関連タスクの処理"""
        # ドキュメント更新の自動処理ロジック
        return {
            "success": True,
            "message": "ドキュメントタスクが処理されました（プレースホルダー）",
            "task_id": task.id,
            "actions_taken": []
        }
    
    def _handle_testing(self, task: Task) -> Dict[str, Any]:
        """テスト関連タスクの処理"""
        # テスト実行の自動処理ロジック
        return {
            "success": True,
            "message": "テストタスクが処理されました（プレースホルダー）",
            "task_id": task.id,
            "actions_taken": []
        }


class TaskAutomationManager:
    """タスク自動化の管理クラス"""
    
    def __init__(self, tasks_file_path: str = "docs/tasks.md"):
        self.parser = TaskParser(tasks_file_path)
        self.executor = TaskExecutor()
        
    def get_pending_tasks(self) -> List[Task]:
        """未完了タスクを取得"""
        all_tasks = self.parser.parse_tasks()
        return [task for task in all_tasks if task.status == TaskStatus.PENDING]
    
    def get_auto_executable_tasks(self) -> List[Task]:
        """自動実行可能な未完了タスクを取得"""
        pending_tasks = self.get_pending_tasks()
        return [task for task in pending_tasks if task.auto_executable]
    
    def execute_all_auto_tasks(self) -> Dict[str, Any]:
        """自動実行可能なすべてのタスクを実行"""
        auto_tasks = self.get_auto_executable_tasks()
        
        if not auto_tasks:
            return {
                "success": True,
                "message": "自動実行可能なタスクはありません",
                "executed_count": 0,
                "results": []
            }
        
        results = []
        success_count = 0
        
        for task in auto_tasks:
            result = self.executor.execute_task(task)
            results.append(result)
            if result["success"]:
                success_count += 1
        
        return {
            "success": True,
            "message": f"{len(auto_tasks)} 個のタスクを処理しました（成功: {success_count}）",
            "executed_count": len(auto_tasks),
            "success_count": success_count,
            "results": results
        }
    
    def get_task_summary(self) -> Dict[str, Any]:
        """タスクの要約情報を取得"""
        all_tasks = self.parser.parse_tasks()
        pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
        auto_tasks = [t for t in pending_tasks if t.auto_executable]
        
        task_types_count = {}
        for task in pending_tasks:
            task_type = task.task_type.value
            task_types_count[task_type] = task_types_count.get(task_type, 0) + 1
        
        return {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            "pending_tasks": len(pending_tasks),
            "auto_executable_tasks": len(auto_tasks),
            "task_types_distribution": task_types_count,
            "pending_task_details": [
                {
                    "id": task.id,
                    "text": task.text,
                    "type": task.task_type.value,
                    "auto_executable": task.auto_executable,
                    "priority": task.priority,
                    "effort": task.estimated_effort
                }
                for task in pending_tasks
            ]
        }