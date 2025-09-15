'use client'

import { useEffect, useMemo, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type PostItem = {
	filename: string
	title: string
	mtime: number
	size: number
}

export default function DraftsPage() {
	const [items, setItems] = useState<PostItem[]>([])
	const [filter, setFilter] = useState('')
	const [selected, setSelected] = useState<PostItem | null>(null)
	const [content, setContent] = useState('')
	const [loading, setLoading] = useState(false)
	const [toast, setToast] = useState('')

	const showToast = (msg: string) => {
		setToast(msg)
		setTimeout(() => setToast(''), 1800)
	}
	const load = async () => {
		try {
			const res = await fetch(`${API_BASE}/api/drafts/posts`, {
				cache: 'no-store',
			})
			if (!res.ok) {
				showToast('削除に失敗しました')
				return
			}
			const json = (await res.json()) as PostItem[]
			setItems(json)
			if (json.length > 0 && !selected) {
				openItem(json[0])
			}
		} catch {}
	}

	useEffect(() => {
		load()
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [])

	const openItem = async (item: PostItem) => {
		setSelected(item)
		setContent('')
		setLoading(true)
		try {
			const res = await fetch(
				`${API_BASE}/api/drafts/posts/${encodeURIComponent(
					item.filename
				)}`
			)
			if (!res.ok) return
			const json = (await res.json()) as {
				filename: string
				content: string
			}
			setContent(json.content || '')
		} finally {
			setLoading(false)
		}
	}

	const filtered = useMemo(() => {
		const q = filter.trim().toLowerCase()
		if (!q) return items
		return items.filter(
			(it) =>
				it.title.toLowerCase().includes(q) ||
				it.filename.toLowerCase().includes(q)
		)
	}, [items, filter])

	const remove = async (item: PostItem) => {
		if (!confirm(`本当に削除しますか？\n${item.filename}`)) return
		try {
			const res = await fetch(
				`${API_BASE}/api/drafts/posts/${encodeURIComponent(
					item.filename
				)}`,
				{ method: 'DELETE' }
			)
			if (!res.ok) {
				showToast('削除に失敗しました')
				return
			}
			// 再読込
			await load()
			// 選択解除
			setSelected((cur) => (cur?.filename === item.filename ? null : cur))
			setContent('')
			showToast('削除しました')
		} catch {}
	}

	const loadIntoWriter = () => {
		if (!content) return
		try {
			localStorage.setItem('prefillDraft', content)
		} catch {}
		window.location.href = '/'
	}

	const copy = async () => {
		try {
			await navigator.clipboard.writeText(content)
		} catch {}
	}

	return (
		<main
			style={{
				display: 'grid',
				gridTemplateColumns: '340px 1fr',
				gap: 16,
			}}>
			<section>
				<h1>保存済み Markdown</h1>
				<div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
					<input
						placeholder="検索（タイトル/ファイル名）"
						value={filter}
						onChange={(e) => setFilter(e.target.value)}
						style={{ flex: 1 }}
					/>
					<button onClick={load}>再読込</button>
				</div>
				<ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
					{filtered.map((it) => (
						<li key={it.filename} style={{ marginBottom: 6 }}>
							<div style={{ display: 'flex', gap: 6 }}>
								<button
									onClick={() => openItem(it)}
									style={{
										flex: 1,
										textAlign: 'left',
										padding: '8px 10px',
										border: '1px solid #eee',
										background:
											selected?.filename === it.filename
												? '#eef6ff'
												: '#fff',
									}}>
									<div style={{ fontWeight: 600 }}>
										{it.title}
									</div>
									<div
										style={{ fontSize: 12, color: '#666' }}>
										{it.filename} ·{' '}
										{new Date(
											it.mtime * 1000
										).toLocaleString()}{' '}
										· {Math.round(it.size / 1024)}KB
									</div>
								</button>
								<button
									onClick={() => remove(it)}
									style={{
										border: '1px solid #f3d6d6',
										background: '#fff5f5',
									}}>
									削除
								</button>
							</div>
						</li>
					))}
					{filtered.length === 0 && (
						<li style={{ color: '#666', fontSize: 12 }}>
							該当なし
						</li>
					)}
				</ul>
			</section>
			<section>
				{selected ? (
					<div>
						<div
							style={{
								display: 'flex',
								alignItems: 'center',
								gap: 8,
							}}>
							<h2 style={{ margin: 0, fontSize: 18 }}>
								{selected.title}
							</h2>
							<span style={{ fontSize: 12, color: '#666' }}>
								{selected.filename}
							</span>
						</div>
						<div
							style={{
								display: 'flex',
								gap: 8,
								margin: '8px 0',
							}}>
							<button
								onClick={loadIntoWriter}
								disabled={!content}>
								Writerで読み込む
							</button>
							<button onClick={copy} disabled={!content}>
								コピー
							</button>
						</div>
						<textarea
							value={loading ? '読み込み中…' : content}
							onChange={(e) => setContent(e.target.value)}
							readOnly={loading}
							rows={24}
							style={{
								width: '100%',
								fontFamily:
									'ui-monospace, SFMono-Regular, Menlo, monospace',
							}}
						/>
					</div>
				) : (
					<p>左の一覧から選択してください。</p>
				)}
			</section>
			{toast && (
				<div
					style={{
						position: 'fixed',
						bottom: 16,
						right: 16,
						background: '#333',
						color: '#fff',
						padding: '8px 10px',
						borderRadius: 4,
						fontSize: 12,
						boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
					}}>
					{toast}
				</div>
			)}
		</main>
	)
}
