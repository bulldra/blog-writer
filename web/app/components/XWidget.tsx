'use client'

import React, { useState } from 'react'

export type XPreviewMode = 'thread' | 'user'

export type XWidgetState = {
	url?: string
	mode: XPreviewMode
	maxPosts: number
	rawText: string
}

type Props = {
	state: XWidgetState
	apiBase?: string
	onChange: (next: Partial<XWidgetState>) => void
}

export default function XWidget({ state, apiBase, onChange }: Props) {
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState('')
	const [text, setText] = useState('')

	const preview = async () => {
		const lines = (state.rawText || '')
			.split('\n')
			.map((t) => t.trim())
			.filter(Boolean)
		if (lines.length === 0) {
			setError('raw_posts を1行1ポストで入力してください')
			return
		}
		setLoading(true)
		setError('')
		setText('')
		try {
			const raw_posts = lines.map((text, i) => ({
				id: String(i + 1),
				text,
			}))
			const base = (apiBase || '').replace(/\/$/, '')
			const res = await fetch(`${base}/api/widgets/x/preview`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					mode: state.mode,
					max_posts: state.maxPosts,
					raw_posts,
				}),
			})
			if (!res.ok) throw new Error('preview_failed')
			const j = await res.json()
			if (j.ok) setText(String(j.text || ''))
			else setError(j.error || 'プレビューに失敗しました')
		} catch (e) {
			setError('プレビューに失敗しました')
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="component-container">
			<strong>X プレビュー</strong>
			<div className="mt-3 grid gap-3 text-sm">
				<div className="text-xs text-gray-600">
					現状は raw_posts による整形プレビューです。URL
					は将来対応予定です。
				</div>

				<label className="grid gap-1">
					<span className="text-xs text-gray-600">
						URL（任意・未使用）
					</span>
					<input
						className="p-2 border rounded"
						placeholder="https://x.com/...（将来対応）"
						value={state.url || ''}
						onChange={(e) => onChange({ url: e.target.value })}
					/>
				</label>

				<div className="grid grid-cols-2 gap-3">
					<label className="grid gap-1">
						<span className="text-xs text-gray-600">モード</span>
						<select
							className="p-2 border rounded"
							value={state.mode}
							onChange={(e) =>
								onChange({
									mode: e.target.value as XPreviewMode,
								})
							}>
							<option value="thread">thread</option>
							<option value="user">user</option>
						</select>
					</label>

					<label className="grid gap-1">
						<span className="text-xs text-gray-600">max_posts</span>
						<input
							type="number"
							className="p-2 border rounded"
							min={1}
							max={100}
							value={state.maxPosts}
							onChange={(e) =>
								onChange({
									maxPosts: Number(e.target.value) || 20,
								})
							}
						/>
					</label>
				</div>

				<label className="grid gap-1">
					<span className="text-xs text-gray-600">
						raw_posts（1行1ポスト）
					</span>
					<textarea
						className="p-2 border rounded"
						rows={4}
						placeholder={
							'新機能が最高だった！\n実装メモ: useEffectの依存関係…'
						}
						value={state.rawText}
						onChange={(e) => onChange({ rawText: e.target.value })}
					/>
				</label>

				<div className="flex items-center gap-2">
					<button
						onClick={preview}
						disabled={loading}
						className="px-3 py-1 text-xs bg-blue-600 text-white rounded disabled:opacity-50">
						{loading ? 'プレビュー中…' : 'プレビュー'}
					</button>
					<button
						className="px-3 py-1 text-xs border rounded"
						onClick={() =>
							onChange({
								rawText:
									'新機能が最高だった！ 即日アップデートした。\n実装メモ: useEffectの依存関係を最適化する。\n気づき: リリースノートの読みやすさがKPIに効く。',
							})
						}
						title="サンプルを挿入">
						サンプル
					</button>
					<button
						className="px-3 py-1 text-xs border rounded"
						onClick={() => {
							setText('')
							setError('')
							onChange({ rawText: '' })
						}}
						title="入力をクリア">
						クリア
					</button>
					{error && (
						<span className="text-xs text-red-600">{error}</span>
					)}
				</div>

				<div className="text-xs text-gray-600">
					raw_posts
					は1行1ポストで入力します。URL/認証/キャッシュは今後追加予定です。
				</div>

				{text && (
					<textarea
						readOnly
						className="p-2 border rounded text-xs mt-2"
						style={{ height: 120 }}
						value={text}
					/>
				)}
			</div>
		</div>
	)
}
