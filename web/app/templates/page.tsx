'use client'
import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

export type Widget = { id: string; name: string; description: string }
export type ArticleTemplate = {
	type: 'url' | 'note' | 'review' | string
	name: string
	fields: { key: string; label: string; input_type: 'text' | 'textarea' }[]
	prompt_template: string
	widgets?: string[]
	description?: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

export default function TemplatesPage() {
	const [list, setList] = useState<ArticleTemplate[]>([])
	const [error, setError] = useState<string>('')
	const [q, setQ] = useState('')
	const [sortKey, setSortKey] = useState<'type' | 'name' | 'widgets'>('type')
	const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
	const router = useRouter()

	useEffect(() => {
		;(async () => {
			try {
				const res = await fetch(`${API_BASE}/api/article-templates`)
				if (res.ok) setList((await res.json()) as ArticleTemplate[])
				else setError('テンプレートの取得に失敗しました')
			} catch {
				setError('テンプレートの取得に失敗しました')
			}
		})()
	}, [])

	const view = useMemo(() => {
		let arr = [...list]
		const keyword = q.trim().toLowerCase()
		if (keyword) {
			arr = arr.filter((t) => {
				const hay = [
					t.type,
					t.name,
					t.description || '',
					(t.widgets || []).join(','),
				]
					.join('\n')
					.toLowerCase()
				return hay.includes(keyword)
			})
		}
		const dir = sortOrder === 'asc' ? 1 : -1
		arr.sort((a, b) => {
			if (sortKey === 'widgets') {
				const va = (a.widgets || []).length
				const vb = (b.widgets || []).length
				return (va - vb) * dir
			}
			const va = String(a[sortKey] || '').toLowerCase()
			const vb = String(b[sortKey] || '').toLowerCase()
			if (va < vb) return -1 * dir
			if (va > vb) return 1 * dir
			return 0
		})
		return arr
	}, [list, q, sortKey, sortOrder])

	const createNew = async () => {
		try {
			const id = window
				.prompt('新規テンプレートID（英数・_・-）', '')
				?.trim()
			if (!id) return
			const re = /^[a-z0-9_\-]+$/
			if (!re.test(id)) {
				alert('IDは英数・_・- のみ使用できます')
				return
			}
			if (list.some((x) => x.type === id)) {
				alert('同じIDのテンプレートが既に存在します')
				return
			}
			const name =
				window
					.prompt('表示名（任意。未入力ならIDを使用）', '')
					?.trim() || id
			const res = await fetch(
				`${API_BASE}/api/article-templates/${encodeURIComponent(id)}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						name,
						description: '',
						fields: [],
						prompt_template: '',
						widgets: [],
					}),
				}
			)
			if (!res.ok) {
				let msg = ''
				try {
					const j = await res.json()
					msg = j?.detail || ''
				} catch {}
				alert(msg || '新規作成に失敗しました')
				return
			}
			const created = (await res.json()) as ArticleTemplate
			setList((prev) =>
				prev.some((x) => x.type === created.type)
					? prev
					: [...prev, created]
			)
			router.push(`/templates/${encodeURIComponent(created.type)}`)
		} catch {}
	}

	return (
		<div style={{ maxWidth: 1000, margin: '2rem auto', padding: '0 1rem' }}>
			<div
				style={{
					display: 'flex',
					gap: 8,
					alignItems: 'center',
					justifyContent: 'space-between',
				}}>
				<h1 style={{ margin: 0 }}>テンプレート一覧</h1>
				<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
					<input
						placeholder="検索 (type/name/description/widgets)"
						value={q}
						onChange={(e) => setQ(e.target.value)}
						style={{ minWidth: 240 }}
					/>
					<select
						value={sortKey}
						onChange={(e) =>
							setSortKey(
								e.target.value as 'type' | 'name' | 'widgets'
							)
						}>
						<option value="type">Type</option>
						<option value="name">Name</option>
						<option value="widgets">Widgets数</option>
					</select>
					<button
						onClick={() =>
							setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
						}
						title="昇順/降順切替">
						{sortOrder === 'asc' ? '昇順' : '降順'}
					</button>
					<button onClick={createNew}>+ 新規作成</button>
				</div>
			</div>
			<div style={{ marginTop: 12 }}>
				<table style={{ width: '100%', borderCollapse: 'collapse' }}>
					<thead>
						<tr style={{ background: '#f7f7f7' }}>
							<th
								style={{
									textAlign: 'left',
									padding: 8,
									borderBottom: '1px solid #ddd',
								}}>
								Type
							</th>
							<th
								style={{
									textAlign: 'left',
									padding: 8,
									borderBottom: '1px solid #ddd',
								}}>
								Name
							</th>
							<th
								style={{
									textAlign: 'left',
									padding: 8,
									borderBottom: '1px solid #ddd',
								}}>
								Description
							</th>
							<th
								style={{
									textAlign: 'left',
									padding: 8,
									borderBottom: '1px solid #ddd',
								}}>
								Widgets
							</th>
							<th
								style={{
									textAlign: 'left',
									padding: 8,
									borderBottom: '1px solid #ddd',
								}}>
								Actions
							</th>
						</tr>
					</thead>
					<tbody>
						{view.map((tpl) => (
							<tr
								key={tpl.type}
								onClick={() =>
									router.push(
										`/templates/${encodeURIComponent(
											tpl.type
										)}`
									)
								}
								className="table-row"
								style={{ cursor: 'pointer' }}>
								<td
									style={{
										padding: 8,
										borderBottom: '1px solid #eee',
									}}>
									{tpl.type}
								</td>
								<td
									style={{
										padding: 8,
										borderBottom: '1px solid #eee',
									}}>
									{tpl.name}
								</td>
								<td
									style={{
										padding: 8,
										borderBottom: '1px solid #eee',
										overflow: 'hidden',
										textOverflow: 'ellipsis',
										whiteSpace: 'nowrap',
										maxWidth: 0,
									}}>
									{tpl.description ? (
										<span title={tpl.description}>
											{tpl.description}
										</span>
									) : (
										<span style={{ color: '#999' }}>—</span>
									)}
								</td>
								<td
									style={{
										padding: 8,
										borderBottom: '1px solid #eee',
									}}>
									{(tpl.widgets || []).length === 0 ? (
										<span style={{ color: '#999' }}>—</span>
									) : (
										<div
											style={{
												display: 'flex',
												gap: 6,
												flexWrap: 'wrap',
											}}>
											{(tpl.widgets || []).map((w) => (
												<span
													key={w}
													style={{
														fontSize: 12,
														background: '#eef',
														border: '1px solid #ccd',
														padding: '1px 8px',
														borderRadius: 12,
													}}>
													{w}
												</span>
											))}
										</div>
									)}
								</td>
								<td
									style={{
										padding: 8,
										borderBottom: '1px solid #eee',
									}}>
									{['url', 'note', 'review'].includes(
										tpl.type
									) ? null : (
										<button
											onClick={(e) => {
												e.stopPropagation()
												if (
													!confirm(
														`${tpl.type} を削除しますか？`
													)
												)
													return
												fetch(
													`${API_BASE}/api/article-templates/${encodeURIComponent(
														tpl.type
													)}`,
													{ method: 'DELETE' }
												)
													.then(
														(r) => r.ok && r.json()
													)
													.then(() =>
														setList((prev) =>
															prev.filter(
																(x) =>
																	x.type !==
																	tpl.type
															)
														)
													)
													.catch(() => {})
											}}
											style={{
												marginLeft: 12,
												color: '#a00',
											}}>
											削除
										</button>
									)}
								</td>
							</tr>
						))}
						{view.length === 0 && (
							<tr>
								<td
									colSpan={5}
									style={{ padding: 8, color: '#666' }}>
									テンプレートが見つかりません
								</td>
							</tr>
						)}
					</tbody>
				</table>
				{error ? (
					<div style={{ color: '#a00', marginTop: 8 }}>{error}</div>
				) : null}
			</div>
		</div>
	)
}
