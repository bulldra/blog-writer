'use client'

import React, { useState, useEffect } from 'react'

type GenerationHistoryItem = {
	id: number
	title: string
	template_type: string
	widgets_used: string[]
	properties: Record<string, string>
	created_at: string
	content_length: number
}

type GenerationHistoryDetail = GenerationHistoryItem & {
	generated_content: string
	reasoning: string
}

type GenerationHistoryWidgetProps = {
	onLoadHistory?: (history: GenerationHistoryDetail) => void
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function GenerationHistoryWidget({
	onLoadHistory,
}: GenerationHistoryWidgetProps) {
	const [history, setHistory] = useState<GenerationHistoryItem[]>([])
	const [selectedHistory, setSelectedHistory] = useState<GenerationHistoryDetail | null>(null)
	const [loading, setLoading] = useState(false)
	const [showDetail, setShowDetail] = useState(false)

	useEffect(() => {
		loadHistory()
	}, [])

	const loadHistory = async () => {
		try {
			setLoading(true)
			const response = await fetch(`${API_BASE}/api/generation-history`)
			if (response.ok) {
				const data = await response.json()
				setHistory(data.history || [])
			}
		} catch (error) {
			console.error('Failed to load generation history:', error)
		} finally {
			setLoading(false)
		}
	}

	const loadHistoryDetail = async (historyId: number) => {
		try {
			setLoading(true)
			const response = await fetch(`${API_BASE}/api/generation-history/${historyId}`)
			if (response.ok) {
				const detail = await response.json()
				setSelectedHistory(detail)
				setShowDetail(true)
			}
		} catch (error) {
			console.error('Failed to load history detail:', error)
		} finally {
			setLoading(false)
		}
	}

	const deleteHistory = async (historyId: number) => {
		if (!window.confirm('この履歴を削除しますか？')) return

		try {
			const response = await fetch(`${API_BASE}/api/generation-history/${historyId}`, {
				method: 'DELETE',
			})
			if (response.ok) {
				setHistory(prev => prev.filter(item => item.id !== historyId))
				if (selectedHistory?.id === historyId) {
					setSelectedHistory(null)
					setShowDetail(false)
				}
			}
		} catch (error) {
			console.error('Failed to delete history:', error)
		}
	}

	const formatDate = (dateString: string) => {
		try {
			return new Date(dateString).toLocaleString('ja-JP')
		} catch {
			return dateString
		}
	}

	const handleLoadHistory = () => {
		if (selectedHistory && onLoadHistory) {
			onLoadHistory(selectedHistory)
			setShowDetail(false)
		}
	}

	if (showDetail && selectedHistory) {
		return (
			<div className="component-container">
				<div className="flex justify-between items-center mb-4">
					<strong>生成履歴詳細</strong>
					<button
						onClick={() => setShowDetail(false)}
						className="text-sm text-gray-500"
					>
						← 一覧に戻る
					</button>
				</div>

				<div className="grid gap-4">
					<div>
						<div className="text-sm font-medium">タイトル</div>
						<div className="text-sm">{selectedHistory.title}</div>
					</div>

					<div>
						<div className="text-sm font-medium">テンプレート</div>
						<div className="text-sm">{selectedHistory.template_type}</div>
					</div>

					<div>
						<div className="text-sm font-medium">使用ウィジェット</div>
						<div className="text-sm">
							{selectedHistory.widgets_used.length > 0 
								? selectedHistory.widgets_used.join(', ')
								: 'なし'
							}
						</div>
					</div>

					<div>
						<div className="text-sm font-medium">プロパティ</div>
						<div className="text-sm">
							{Object.entries(selectedHistory.properties).length > 0 ? (
								<div className="grid gap-1">
									{Object.entries(selectedHistory.properties).map(([key, value]) => (
										<div key={key} className="text-xs">
											<span className="font-medium">{key}:</span> {value}
										</div>
									))}
								</div>
							) : (
								'なし'
							)}
						</div>
					</div>

					<div>
						<div className="text-sm font-medium">生成日時</div>
						<div className="text-sm">{formatDate(selectedHistory.created_at)}</div>
					</div>

					{selectedHistory.reasoning && (
						<div>
							<div className="text-sm font-medium">思考過程</div>
							<div className="text-xs bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
								{selectedHistory.reasoning}
							</div>
						</div>
					)}

					<div>
						<div className="text-sm font-medium">生成内容</div>
						<div className="text-xs bg-gray-50 p-2 rounded max-h-48 overflow-y-auto">
							{selectedHistory.generated_content}
						</div>
					</div>

					<div className="flex gap-2">
						{onLoadHistory && (
							<button
								onClick={handleLoadHistory}
								className="px-3 py-1 bg-blue-500 text-white text-sm rounded"
							>
								この履歴を読み込む
							</button>
						)}
						<button
							onClick={() => deleteHistory(selectedHistory.id)}
							className="px-3 py-1 bg-red-500 text-white text-sm rounded"
						>
							削除
						</button>
					</div>
				</div>
			</div>
		)
	}

	return (
		<div className="component-container">
			<div className="flex justify-between items-center">
				<strong>生成履歴</strong>
				<button
					onClick={loadHistory}
					disabled={loading}
					className="text-sm text-blue-500"
				>
					{loading ? '読み込み中...' : '更新'}
				</button>
			</div>

			<div className="mt-4">
				{history.length === 0 ? (
					<div className="text-sm text-gray-500">履歴がありません</div>
				) : (
					<div className="grid gap-2">
						{history.map(item => (
							<div key={item.id} className="border rounded p-2">
								<div className="flex justify-between items-start">
									<div className="flex-1">
										<div className="text-sm font-medium">{item.title}</div>
										<div className="text-xs text-gray-600">
											{item.template_type} | {formatDate(item.created_at)}
										</div>
										<div className="text-xs text-gray-500">
											{item.content_length}文字
											{item.widgets_used.length > 0 && 
												` | ウィジェット: ${item.widgets_used.join(', ')}`
											}
										</div>
									</div>
									<div className="flex gap-1">
										<button
											onClick={() => loadHistoryDetail(item.id)}
											className="px-2 py-1 text-xs bg-blue-500 text-white rounded"
											disabled={loading}
										>
											詳細
										</button>
										<button
											onClick={() => deleteHistory(item.id)}
											className="px-2 py-1 text-xs bg-red-500 text-white rounded"
										>
											削除
										</button>
									</div>
								</div>
							</div>
						))}
					</div>
				)}
			</div>
		</div>
	)
}