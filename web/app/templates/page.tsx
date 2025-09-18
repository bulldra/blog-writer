'use client'
import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

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
			// tie-breaker
			if (a.type < b.type) return -1
			if (a.type > b.type) return 1
			return 0
		})
		return arr
	}, [list, q, sortKey, sortOrder])

	return (
		<div style={{ maxWidth: 980, margin: '2rem auto', padding: '0 1rem' }}>
			<h1>記事テンプレート一覧</h1>
			<div
				style={{
					display: 'flex',
					justifyContent: 'space-between',
					alignItems: 'center',
					gap: 12,
					marginTop: 12,
					flexWrap: 'wrap',
				}}>
				<button
					onClick={() => {
						const id = window.prompt(
							'新しいテンプレートID（英数・_・-）',
							''
						)
						if (!id) return
						fetch(
							`${API_BASE}/api/article-templates/${encodeURIComponent(
								id
							)}`,
							{
								method: 'POST',
								headers: { 'Content-Type': 'application/json' },
								body: JSON.stringify({
									name: id,
									fields: [],
									prompt_template: '',
									widgets: [],
								}),
							}
						)
							.then((r) => r.ok && r.json())
							.then((row) => {
								if (!row) return
								setList((prev) => {
									const found = prev.find(
										(x) => x.type === row.type
									)
									return found ? prev : [...prev, row]
								})
								router.push(
									`/templates/${encodeURIComponent(row.type)}`
								)
							})
							.catch(() => {})
					}}>
					+ 新規作成
				</button>
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
							<tr key={tpl.type}>
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
									}}>
									{tpl.description ? (
										<details>
											<summary
												style={{ cursor: 'pointer' }}>
												{tpl.description.length > 40
													? tpl.description.slice(
															0,
															40
													  ) + '…'
													: tpl.description}
											</summary>
											<div
												style={{
													whiteSpace: 'pre-wrap',
													color: '#555',
													marginTop: 4,
												}}>
												{tpl.description}
											</div>
										</details>
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
									<Link
										href={`/templates/${encodeURIComponent(
											tpl.type
										)}`}>
										編集
									</Link>
									<button
										onClick={() => {
											const newType = window.prompt(
												'複製先のテンプレートID（英数・_・-）',
												`${tpl.type}-copy`
											)
											if (!newType) return
											fetch(
												`${API_BASE}/api/article-templates/${encodeURIComponent(
													tpl.type
												)}/duplicate`,
												{
													method: 'POST',
													headers: {
														'Content-Type':
															'application/json',
													},
													body: JSON.stringify({
														new_type: newType,
													}),
												}
											)
												.then((r) =>
													r.ok ? r.json() : null
												)
												.then((row) => {
													if (!row) return
													setList((prev) => {
														const exists =
															prev.some(
																(x) =>
																	x.type ===
																	row.type
															)
														return exists
															? prev
															: [...prev, row]
													})
													router.push(
														`/templates/${encodeURIComponent(
															row.type
														)}`
													)
												})
												.catch(() => {})
										}}
										style={{ marginLeft: 12 }}>
										複製
									</button>
									{['url', 'note', 'review'].includes(
										tpl.type
									) ? null : (
										<button
											onClick={() => {
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
						{list.length === 0 && (
							<tr>
								<td
									colSpan={4}
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
