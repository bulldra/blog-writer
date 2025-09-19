#!/usr/bin/env python3
"""定期実行スクリプト

定期的にタスクを実行するためのスクリプト
cron や systemd timer で使用することを想定
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, UTC

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.task_automation import TaskAutomationManager


def setup_logging():
    """ログ設定"""
    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "task_automation.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """定期実行のメイン処理"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("タスク自動実行を開始")
    
    try:
        manager = TaskAutomationManager()
        
        # 要約情報をログに出力
        summary = manager.get_task_summary()
        logger.info(f"タスク要約: 総数={summary['total_tasks']}, "
                   f"完了={summary['completed_tasks']}, "
                   f"未完了={summary['pending_tasks']}, "
                   f"自動実行可能={summary['auto_executable_tasks']}")
        
        # 自動実行可能なタスクがあるかチェック
        auto_tasks = manager.get_auto_executable_tasks()
        if not auto_tasks:
            logger.info("自動実行可能なタスクはありません")
            return
        
        logger.info(f"自動実行可能なタスクを {len(auto_tasks)} 個発見:")
        for task in auto_tasks:
            logger.info(f"  - [Line {task.line_number}] {task.text}")
        
        # タスクを実行
        result = manager.execute_all_auto_tasks()
        
        logger.info(f"実行結果: 処理数={result['executed_count']}, "
                   f"成功数={result['success_count']}, "
                   f"失敗数={result['executed_count'] - result['success_count']}")
        
        # 詳細結果をログに出力
        for i, task_result in enumerate(result['results'], 1):
            status = "成功" if task_result['success'] else "失敗"
            logger.info(f"  {i}. {status}: {task_result['message']}")
        
        logger.info("タスク自動実行を完了")
        
    except Exception as e:
        logger.error(f"タスク自動実行中にエラーが発生: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()