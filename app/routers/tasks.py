"""タスク自動化 API エンドポイント"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.task_automation import TaskAutomationManager, Task, TaskStatus, TaskType

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    """タスク情報のレスポンス"""
    id: int
    text: str
    status: str
    task_type: str
    line_number: int
    auto_executable: bool
    priority: int
    estimated_effort: str


class TaskSummaryResponse(BaseModel):
    """タスク要約のレスポンス"""
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    auto_executable_tasks: int
    task_types_distribution: Dict[str, int]
    pending_task_details: List[Dict[str, Any]]


class TaskExecutionResponse(BaseModel):
    """タスク実行結果のレスポンス"""
    success: bool
    message: str
    executed_count: int
    success_count: int
    results: List[Dict[str, Any]]


# グローバルなタスクマネージャーインスタンス
task_manager = TaskAutomationManager()


def _task_to_response(task: Task) -> TaskResponse:
    """TaskオブジェクトをTaskResponseに変換"""
    return TaskResponse(
        id=task.id,
        text=task.text,
        status=task.status.value,
        task_type=task.task_type.value,
        line_number=task.line_number,
        auto_executable=task.auto_executable,
        priority=task.priority,
        estimated_effort=task.estimated_effort
    )


@router.get("/summary", response_model=TaskSummaryResponse)
async def get_task_summary():
    """タスクの要約情報を取得"""
    try:
        summary = task_manager.get_task_summary()
        return TaskSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タスク要約の取得に失敗しました: {str(e)}")


@router.get("/pending", response_model=List[TaskResponse])
async def get_pending_tasks():
    """未完了タスクの一覧を取得"""
    try:
        pending_tasks = task_manager.get_pending_tasks()
        return [_task_to_response(task) for task in pending_tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未完了タスクの取得に失敗しました: {str(e)}")


@router.get("/auto-executable", response_model=List[TaskResponse])
async def get_auto_executable_tasks():
    """自動実行可能タスクの一覧を取得"""
    try:
        auto_tasks = task_manager.get_auto_executable_tasks()
        return [_task_to_response(task) for task in auto_tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自動実行可能タスクの取得に失敗しました: {str(e)}")


@router.post("/execute", response_model=TaskExecutionResponse)
async def execute_auto_tasks(dry_run: bool = False):
    """自動実行可能タスクを実行"""
    try:
        if dry_run:
            # ドライランの場合は実行しないで結果をシミュレート
            auto_tasks = task_manager.get_auto_executable_tasks()
            return TaskExecutionResponse(
                success=True,
                message=f"ドライラン: {len(auto_tasks)} 個のタスクが実行対象です",
                executed_count=len(auto_tasks),
                success_count=len(auto_tasks),
                results=[
                    {
                        "success": True,
                        "message": f"ドライラン: {task.text}",
                        "task_id": task.id
                    }
                    for task in auto_tasks
                ]
            )
        else:
            result = task_manager.execute_all_auto_tasks()
            return TaskExecutionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タスク実行に失敗しました: {str(e)}")


@router.get("/refresh")
async def refresh_tasks():
    """タスクファイルを再読み込み"""
    try:
        # 新しいマネージャーインスタンスを作成してタスクを再読み込み
        global task_manager
        task_manager = TaskAutomationManager()
        return {"success": True, "message": "タスクファイルを再読み込みしました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"タスクファイルの再読み込みに失敗しました: {str(e)}")


@router.get("/status")
async def get_task_automation_status():
    """タスク自動化システムのステータス取得"""
    try:
        summary = task_manager.get_task_summary()
        return {
            "status": "active",
            "tasks_file": "docs/tasks.md",
            "total_tasks": summary["total_tasks"],
            "pending_tasks": summary["pending_tasks"],
            "auto_executable_tasks": summary["auto_executable_tasks"],
            "last_updated": "2024-01-01T00:00:00Z"  # 実際の実装では最終更新時刻を取得
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ステータス取得に失敗しました: {str(e)}")