#!/usr/bin/env python3
"""タスク自動実行 CLI

Usage:
    python scripts/task_automation_cli.py [command] [options]

Commands:
    list       - 未完了タスクの一覧表示
    summary    - タスクの要約情報表示
    execute    - 自動実行可能タスクの実行
    monitor    - タスクファイルの監視（開発中）
"""

import sys
import json
import argparse
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.task_automation import TaskAutomationManager, TaskStatus


def setup_logging():
    """ログ設定"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def list_tasks(manager: TaskAutomationManager, show_completed: bool = False):
    """タスク一覧表示"""
    all_tasks = manager.parser.parse_tasks()
    
    if show_completed:
        tasks_to_show = all_tasks
        print("=== 全タスク一覧 ===")
    else:
        tasks_to_show = [t for t in all_tasks if t.status == TaskStatus.PENDING]
        print("=== 未完了タスク一覧 ===")
    
    if not tasks_to_show:
        print("該当するタスクはありません。")
        return
    
    for task in tasks_to_show:
        status_icon = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
        auto_icon = "🤖" if task.auto_executable else "👤"
        priority_stars = "⭐" * task.priority
        
        print(f"{status_icon} {auto_icon} [Line {task.line_number:3d}] {task.text}")
        print(f"    タイプ: {task.task_type.value}, 優先度: {priority_stars}, 作業量: {task.estimated_effort}")
        print()


def show_summary(manager: TaskAutomationManager):
    """タスク要約表示"""
    summary = manager.get_task_summary()
    
    print("=== タスク要約 ===")
    print(f"総タスク数: {summary['total_tasks']}")
    print(f"完了タスク: {summary['completed_tasks']}")
    print(f"未完了タスク: {summary['pending_tasks']}")
    print(f"自動実行可能タスク: {summary['auto_executable_tasks']}")
    print()
    
    if summary['task_types_distribution']:
        print("タスクタイプ別分布:")
        for task_type, count in summary['task_types_distribution'].items():
            print(f"  {task_type}: {count} 個")
        print()
    
    if summary['auto_executable_tasks'] > 0:
        print("🤖 自動実行可能タスク:")
        for task in summary['pending_task_details']:
            if task['auto_executable']:
                priority_stars = "⭐" * task['priority']
                print(f"  - {task['text']} (優先度: {priority_stars})")
        print()


def execute_tasks(manager: TaskAutomationManager, dry_run: bool = False):
    """タスク実行"""
    auto_tasks = manager.get_auto_executable_tasks()
    
    if not auto_tasks:
        print("自動実行可能なタスクはありません。")
        return
    
    print(f"自動実行可能なタスクが {len(auto_tasks)} 個見つかりました:")
    for task in auto_tasks:
        print(f"  - {task.text}")
    print()
    
    if dry_run:
        print("ドライランモードのため実行しません。")
        return
    
    # 実行確認
    response = input("これらのタスクを実行しますか？ (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("実行をキャンセルしました。")
        return
    
    print("タスク実行中...")
    result = manager.execute_all_auto_tasks()
    
    print()
    print("=== 実行結果 ===")
    print(f"処理タスク数: {result['executed_count']}")
    print(f"成功数: {result['success_count']}")
    print(f"失敗数: {result['executed_count'] - result['success_count']}")
    
    if result['results']:
        print("\n詳細結果:")
        for i, task_result in enumerate(result['results'], 1):
            status = "✅ 成功" if task_result['success'] else "❌ 失敗"
            print(f"  {i}. {status}: {task_result['message']}")


def monitor_tasks(manager: TaskAutomationManager):
    """タスクファイル監視（簡易版）"""
    print("タスクファイル監視機能は開発中です。")
    print("将来的には tasks.md の変更を監視してリアルタイムでタスクを処理する予定です。")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="タスク自動実行システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'command', 
        choices=['list', 'summary', 'execute', 'monitor'],
        help='実行するコマンド'
    )
    
    parser.add_argument(
        '--tasks-file',
        default='docs/tasks.md',
        help='タスクファイルのパス (デフォルト: docs/tasks.md)'
    )
    
    parser.add_argument(
        '--show-completed',
        action='store_true',
        help='完了タスクも表示 (listコマンド用)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際には実行せずに実行予定を表示 (executeコマンド用)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='JSON形式で出力'
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    # タスクファイルの存在確認
    tasks_file = Path(args.tasks_file)
    if not tasks_file.exists():
        print(f"エラー: タスクファイルが見つかりません: {tasks_file}", file=sys.stderr)
        sys.exit(1)
    
    manager = TaskAutomationManager(str(tasks_file))
    
    try:
        if args.command == 'list':
            if args.json:
                all_tasks = manager.parser.parse_tasks()
                tasks_to_show = all_tasks if args.show_completed else [
                    t for t in all_tasks if t.status == TaskStatus.PENDING
                ]
                task_data = [
                    {
                        "id": t.id,
                        "text": t.text,
                        "status": t.status.value,
                        "type": t.task_type.value,
                        "line_number": t.line_number,
                        "auto_executable": t.auto_executable,
                        "priority": t.priority,
                        "estimated_effort": t.estimated_effort
                    }
                    for t in tasks_to_show
                ]
                print(json.dumps(task_data, ensure_ascii=False, indent=2))
            else:
                list_tasks(manager, args.show_completed)
                
        elif args.command == 'summary':
            if args.json:
                summary = manager.get_task_summary()
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                show_summary(manager)
                
        elif args.command == 'execute':
            execute_tasks(manager, args.dry_run)
            
        elif args.command == 'monitor':
            monitor_tasks(manager)
            
    except KeyboardInterrupt:
        print("\n処理を中断しました。")
        sys.exit(0)
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()