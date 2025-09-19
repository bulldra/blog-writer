#!/usr/bin/env python3
"""タスクファイル監視スクリプト

docs/tasks.md の変更を監視し、変更があった場合に自動でタスクを処理する
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime, UTC
from hashlib import md5

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
            logging.FileHandler(log_dir / "task_watcher.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def get_file_hash(file_path: Path) -> str:
    """ファイルのハッシュ値を取得"""
    if not file_path.exists():
        return ""
    
    try:
        with open(file_path, 'rb') as f:
            return md5(f.read()).hexdigest()
    except Exception:
        return ""


def process_tasks(manager: TaskAutomationManager, logger: logging.Logger):
    """タスクを処理"""
    try:
        # 自動実行可能なタスクを取得
        auto_tasks = manager.get_auto_executable_tasks()
        
        if not auto_tasks:
            logger.info("自動実行可能なタスクはありません")
            return
        
        logger.info(f"自動実行可能なタスクを {len(auto_tasks)} 個発見")
        
        # 実行確認（監視モードでは自動実行）
        result = manager.execute_all_auto_tasks()
        
        logger.info(f"実行結果: 処理数={result['executed_count']}, "
                   f"成功数={result['success_count']}")
        
        # 成功したタスクの詳細をログに出力
        for task_result in result['results']:
            if task_result['success']:
                logger.info(f"✅ {task_result['message']}")
            else:
                logger.warning(f"❌ {task_result['message']}")
                
    except Exception as e:
        logger.error(f"タスク処理中にエラー: {e}", exc_info=True)


def main():
    """監視のメイン処理"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    tasks_file = Path("docs/tasks.md")
    
    if not tasks_file.exists():
        logger.error(f"監視対象ファイルが見つかりません: {tasks_file}")
        sys.exit(1)
    
    logger.info(f"タスクファイル監視を開始: {tasks_file}")
    logger.info("Ctrl+C で停止")
    
    manager = TaskAutomationManager(str(tasks_file))
    last_hash = get_file_hash(tasks_file)
    
    # 起動時に一度処理
    logger.info("起動時のタスク処理を実行")
    process_tasks(manager, logger)
    
    try:
        while True:
            time.sleep(5)  # 5秒間隔でチェック
            
            current_hash = get_file_hash(tasks_file)
            
            if current_hash != last_hash:
                logger.info("タスクファイルの変更を検出")
                
                # マネージャーを再初期化してタスクを再読み込み
                manager = TaskAutomationManager(str(tasks_file))
                
                # タスクを処理
                process_tasks(manager, logger)
                
                last_hash = current_hash
                
    except KeyboardInterrupt:
        logger.info("監視を停止します")
    except Exception as e:
        logger.error(f"監視中にエラーが発生: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()