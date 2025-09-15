'use client'
import { useEffect, useMemo, useState } from 'react'

type Property = { key: string }
type ArticleTemplate = {
	type: 'url' | 'note' | 'review'
	name: string
	fields: { key: string; label: string; input_type: 'text' | 'textarea' }[]
	prompt_template: string
	widgets?: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function TemplatesPage() {
	// 記事テンプレ
	const [list, setList] = useState<ArticleTemplate[]>([])
	const [currentType, setCurrentType] = useState<'url' | 'note' | 'review'>(
		'url'
	)
	const current = useMemo(
		() => list.find((x) => x.type === currentType),
		[list, currentType]
	)
	const [name, setName] = useState('')
	const [widgets, setWidgets] = useState<string[]>([])
	// プロパティ（キーのみ）
	const [properties, setProperties] = useState<Property[]>([])
	const [promptText, setPromptText] = useState('')
	const [saving, setSaving] = useState(false)
	const [error, setError] = useState<string>('')

	// 初期ロード
	useEffect(() => {
		;(async () => {
			try {
				const res = await fetch(`${API_BASE}/api/article-templates`)
				if (res.ok) {
					const rows = (await res.json()) as ArticleTemplate[]
					setList(rows)
				}
			} catch {}
			// 旧プロンプトテンプレの取り込みは廃止
		})()
	}, [])

	// 現在テンプレのフォームへ反映
	useEffect(() => {
		if (!current) return
		setName(current.name)
		setProperties((current.fields || []).map((f) => ({ key: f.key })))
		setPromptText(current.prompt_template || '')
		setWidgets(
			Array.isArray(
				(current as unknown as { widgets?: string[] })?.widgets
			)
				? ((current as unknown as { widgets?: string[] })
						.widgets as string[])
				: []
		)
		setError('')
	}, [currentType, current])

	const saveArticleTemplate = async () => {
		if (!current) return
		setSaving(true)
		setError('')
		try {
			const fields = properties
				.map((p) => p.key.trim())
				.filter((k) => k.length > 0)
				.map((k) => ({ key: k, label: k, input_type: 'text' as const }))
			const res = await fetch(
				`${API_BASE}/api/article-templates/${current.type}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						name,
						fields,
						prompt_template: promptText,
						widgets,
					}),
				}
			)
			if (res.ok) {
				const row = (await res.json()) as ArticleTemplate
				setList((prev) =>
					prev.map((x) => (x.type === row.type ? row : x))
				)
			} else {
				const t = await res.text()
				setError(t || '保存に失敗しました')
			}
		} catch (e) {
			setError('保存に失敗しました')
		} finally {
			setSaving(false)
		}
	}

	const aiPropose = async () => {
		try {
			const res = await fetch('/api/ai/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					prompt: 'ブログ記事生成に使うプロンプトテンプレートの雛形を提案してください。利用可能なプレースホルダーは {{title}}, {{style}}, {{length}}, {{bullets}}, {{highlights}}, {{url_context}}, {{base}} です。テンプレとしてそのまま貼り付け可能な形式で出力してください。',
				}),
			})
			if (res.ok) {
				const json = await res.json()
				setPromptText(String(json.text || ''))
			}
		} catch {}
	}

	return (
		<div style={{ maxWidth: 980, margin: '2rem auto', padding: '0 1rem' }}>
			<h1>記事テンプレート管理</h1>
			<p style={{ color: '#555', marginTop: 4 }}>
				左の一覧からテンプレートを選び、右側で詳細を編集します。
			</p>

			<div
				style={{
					display: 'grid',
					gridTemplateColumns: '260px 1fr',
					gap: 16,
					alignItems: 'start',
					marginTop: 16,
				}}>
				{/* 一覧 */}
				<div
					style={{
						border: '1px solid #ddd',
						background: '#fff',
						padding: 8,
					}}>
					<strong>テンプレート一覧</strong>
					<ul style={{ listStyle: 'none', padding: 0, margin: 8 }}>
						{list.map((tpl) => (
							<li key={tpl.type} style={{ marginBottom: 6 }}>
								<button
									onClick={() => setCurrentType(tpl.type)}
									style={{
										width: '100%',
										textAlign: 'left',
										padding: '6px 8px',
										background:
											currentType === tpl.type
												? '#eef5ff'
												: '#f9f9f9',
										border: '1px solid #ddd',
										cursor: 'pointer',
									}}>
									<div style={{ fontWeight: 600 }}>
										{tpl.name || tpl.type}
									</div>
									<div
										style={{ fontSize: 12, color: '#666' }}>
										{tpl.type}
									</div>
								</button>
							</li>
						))}
						{list.length === 0 ? (
							<li style={{ fontSize: 12, color: '#666' }}>
								テンプレートが見つかりません
							</li>
						) : null}
					</ul>
				</div>

				{/* 詳細 */}
				<div style={{ display: 'grid', gap: 12 }}>
					<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
						<input
							placeholder="テンプレート表示名"
							value={name}
							onChange={(e) => setName(e.target.value)}
							style={{ flex: 1 }}
						/>
						<button onClick={aiPropose}>
							AIでプロンプト雛形を提案
						</button>
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
										headers: {
											'Content-Type': 'application/json',
										},
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
										setCurrentType(row.type)
									})
									.catch(() => {})
							}}>
							+ テンプレート追加
						</button>
						{current &&
							(current as unknown as { type: string }).type &&
							!['url', 'note', 'review'].includes(
								(current as unknown as { type: string }).type
							) && (
								<button
									onClick={() => {
										const id = (
											current as unknown as {
												type: string
											}
										).type
										if (!confirm(`${id} を削除しますか？`))
											return
										fetch(
											`${API_BASE}/api/article-templates/${encodeURIComponent(
												id
											)}`,
											{ method: 'DELETE' }
										)
											.then((r) => r.ok && r.json())
											.then(() => {
												setList((prev) =>
													prev.filter(
														(x) => x.type !== id
													)
												)
												setCurrentType('url')
											})
											.catch(() => {})
									}}
									style={{ color: '#a00' }}>
									削除
								</button>
							)}
					</div>

					<div>
						<div
							style={{
								display: 'flex',
								alignItems: 'center',
								gap: 8,
							}}>
							<strong>プロパティ</strong>
							<button
								onClick={() =>
									setProperties((prev) => [
										...prev,
										{ key: '' },
									])
								}>
								+ プロパティを追加
							</button>
						</div>
						<div style={{ marginTop: 8, display: 'grid', gap: 8 }}>
							{properties.map((p, i) => (
								<div
									key={i}
									style={{
										display: 'grid',
										gridTemplateColumns: '1fr auto',
										gap: 8,
										alignItems: 'center',
									}}>
									<input
										placeholder="property 名 (英数・_・-)"
										value={p.key}
										onChange={(e) =>
											setProperties((prev) =>
												prev.map((x, idx) =>
													idx === i
														? {
																...x,
																key: e.target
																	.value,
														  }
														: x
												)
											)
										}
									/>
									<button
										onClick={() =>
											setProperties((prev) =>
												prev.filter(
													(_, idx) => idx !== i
												)
											)
										}
										style={{ color: '#a00' }}>
										削除
									</button>
								</div>
							))}
							{properties.length === 0 ? (
								<div style={{ color: '#666', fontSize: 12 }}>
									プロパティは任意です。
								</div>
							) : null}
						</div>
					</div>

					<div>
						<strong>プロンプトテンプレート</strong>
						<textarea
							placeholder={
								'{{base}}\n---\n{{bullets}}\n---\n任意の変数: {{title}}, {{style}}, {{length}}, {{highlights}}, {{url_context}} など'
							}
							value={promptText}
							onChange={(e) => setPromptText(e.target.value)}
							rows={12}
							style={{ width: '100%', marginTop: 6 }}
						/>
					</div>

					<div>
						<strong>ウィジェット</strong>
						<div
							style={{
								display: 'flex',
								gap: 12,
								flexWrap: 'wrap',
								marginTop: 6,
							}}>
							{['url_context', 'kindle', 'past_posts'].map(
								(w) => (
									<label
										key={w}
										style={{
											display: 'flex',
											alignItems: 'center',
											gap: 6,
										}}>
										<input
											type="checkbox"
											checked={widgets.includes(w)}
											onChange={(e) => {
												const on = e.target.checked
												setWidgets((prev) => {
													const s = new Set(prev)
													if (on) s.add(w)
													else s.delete(w)
													return Array.from(s)
												})
											}}
										/>
										<span style={{ fontSize: 12 }}>
											{w}
										</span>
									</label>
								)
							)}
						</div>
						<div
							style={{
								fontSize: 12,
								color: '#666',
								marginTop: 4,
							}}>
							表示用のウィジェットを選べます。URLコンテキスト、Kindleハイライト、過去記事の参照を切替可能。
						</div>
					</div>

					<div
						style={{
							display: 'flex',
							gap: 8,
							alignItems: 'center',
							flexWrap: 'wrap',
						}}>
						<button onClick={saveArticleTemplate} disabled={saving}>
							{saving ? '保存中…' : '保存'}
						</button>
						{error ? (
							<span style={{ color: '#a00', fontSize: 12 }}>
								{error}
							</span>
						) : null}
					</div>
				</div>
			</div>
		</div>
	)
}
