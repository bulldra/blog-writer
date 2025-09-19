'use client'

import { useState, useEffect } from 'react'

interface TaskSummary {
	total_tasks: number
	completed_tasks: number
	pending_tasks: number
	auto_executable_tasks: number
	task_types_distribution: Record<string, number>
}

interface TaskAutomationStatusProps {
	apiBase?: string
}

export default function TaskAutomationStatus({ 
	apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000' 
}: TaskAutomationStatusProps) {
	const [summary, setSummary] = useState<TaskSummary | null>(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

	const fetchSummary = async () => {
		setLoading(true)
		setError(null)
		
		try {
			const response = await fetch(`${apiBase}/api/tasks/summary`)
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`)
			}
			
			const data = await response.json()
			setSummary(data)
			setLastUpdated(new Date())
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unknown error')
		} finally {
			setLoading(false)
		}
	}

	const executeAutoTasks = async (dryRun: boolean = false) => {
		setLoading(true)
		setError(null)
		
		try {
			const response = await fetch(
				`${apiBase}/api/tasks/execute?dry_run=${dryRun}`,
				{ method: 'POST' }
			)
			
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`)
			}
			
			const result = await response.json()
			
			// 実行後にサマリーを再取得
			await fetchSummary()
			
			// 結果を表示（簡易版）
			alert(`タスク実行${dryRun ? '（ドライラン）' : ''}完了:\n処理数: ${result.executed_count}\n成功数: ${result.success_count}`)
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Unknown error')
		} finally {
			setLoading(false)
		}
	}

	useEffect(() => {
		fetchSummary()
	}, [])

	if (error) {
		return (
			<div className="component-container">
				<strong>タスク自動化</strong>
				<div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
					<p className="text-red-600">エラー: {error}</p>
					<button 
						onClick={fetchSummary}
						className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
					>
						再試行
					</button>
				</div>
			</div>
		)
	}

	return (
		<div className="component-container">
			<div className="flex-row">
				<strong>タスク自動化</strong>
				<button 
					onClick={fetchSummary}
					disabled={loading}
					className="text-xs"
				>
					{loading ? '更新中...' : '更新'}
				</button>
			</div>

			{summary && (
				<div className="mt-4 space-y-3">
					{/* 要約統計 */}
					<div className="grid grid-cols-2 gap-3 text-sm">
						<div className="bg-gray-50 p-3 rounded">
							<div className="font-medium">総タスク数</div>
							<div className="text-lg font-bold text-blue-600">
								{summary.total_tasks}
							</div>
						</div>
						<div className="bg-gray-50 p-3 rounded">
							<div className="font-medium">完了率</div>
							<div className="text-lg font-bold text-green-600">
								{summary.total_tasks > 0 
									? Math.round((summary.completed_tasks / summary.total_tasks) * 100)
									: 0}%
							</div>
						</div>
						<div className="bg-gray-50 p-3 rounded">
							<div className="font-medium">未完了</div>
							<div className="text-lg font-bold text-orange-600">
								{summary.pending_tasks}
							</div>
						</div>
						<div className="bg-gray-50 p-3 rounded">
							<div className="font-medium">自動実行可能</div>
							<div className="text-lg font-bold text-purple-600">
								{summary.auto_executable_tasks}
							</div>
						</div>
					</div>

					{/* タスクタイプ分布 */}
					{Object.keys(summary.task_types_distribution).length > 0 && (
						<div>
							<div className="text-sm font-medium mb-2">タスクタイプ分布</div>
							<div className="space-y-1">
								{Object.entries(summary.task_types_distribution).map(([type, count]) => (
									<div key={type} className="flex justify-between text-xs">
										<span className="capitalize">{type.replace('_', ' ')}</span>
										<span className="font-medium">{count}</span>
									</div>
								))}
							</div>
						</div>
					)}

					{/* 実行ボタン */}
					{summary.auto_executable_tasks > 0 && (
						<div className="flex gap-2">
							<button
								onClick={() => executeAutoTasks(true)}
								disabled={loading}
								className="flex-1 px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 disabled:opacity-50"
							>
								ドライラン
							</button>
							<button
								onClick={() => executeAutoTasks(false)}
								disabled={loading}
								className="flex-1 px-3 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:opacity-50"
							>
								実行
							</button>
						</div>
					)}

					{/* 最終更新時刻 */}
					{lastUpdated && (
						<div className="text-xs text-gray-500">
							最終更新: {lastUpdated.toLocaleTimeString()}
						</div>
					)}
				</div>
			)}

			{loading && !summary && (
				<div className="mt-4 text-center text-gray-500">
					読み込み中...
				</div>
			)}
		</div>
	)
}