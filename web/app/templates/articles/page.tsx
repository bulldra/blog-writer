'use client'
import { useEffect, useMemo, useState } from 'react'

type Field = { key: string; label: string; input_type: 'text' | 'textarea' }
type Widget = { id: string; name: string; description: string }
type ArticleTemplate = {
	type: 'url' | 'note' | 'review'
	name: string
	fields: Field[]
	prompt_template: string
	widgets: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function ArticleTemplatesPage() {
	const [types] = useState<Array<'url' | 'note' | 'review'>>([
		'url',
		'note',
		'review',
	])
	const [current, setCurrent] = useState<'url' | 'note' | 'review'>('url')
	const [tpl, setTpl] = useState<ArticleTemplate | null>(null)
	const [availableWidgets, setAvailableWidgets] = useState<Widget[]>([])
	const [loading, setLoading] = useState(false)
	const [savedMsg, setSavedMsg] = useState<string>('')
	const [errorMsg, setErrorMsg] = useState<string>('')

	const load = async (t: 'url' | 'note' | 'review') => {
		setLoading(true)
		setSavedMsg('')
		try {
			const res = await fetch(`${API_BASE}/api/article-templates/${t}`)
			if (res.ok) {
				const json = (await res.json()) as ArticleTemplate
				// widgets プロパティがない場合は空配列で初期化
				if (!json.widgets) {
					json.widgets = []
				}
				setTpl(json)
			}
		} finally {
			setLoading(false)
		}
	}

	const loadAvailableWidgets = async () => {
		try {
			const res = await fetch(`${API_BASE}/api/article-templates/widgets/available`)
			if (res.ok) {
				const data = await res.json()
				setAvailableWidgets(data.widgets || [])
			}
		} catch (error) {
			console.error('Failed to load available widgets:', error)
		}
	}

	useEffect(() => {
		load(current)
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [current])

	useEffect(() => {
		loadAvailableWidgets()
	}, [])

	const updateField = (idx: number, key: keyof Field, val: string) => {
		if (!tpl) return
		const next = { ...tpl, fields: [...tpl.fields] }
		const row = { ...next.fields[idx], [key]: val }
		next.fields[idx] = row
		setTpl(next)
		setErrorMsg('')
	}

	const addField = () => {
		if (!tpl) return
		if (tpl.fields.length >= 30) {
			setErrorMsg('項目は最大 30 個までです')
			return
		}
		const next = { ...tpl, fields: [...tpl.fields] }
		next.fields.push({ key: '', label: '', input_type: 'text' })
		setTpl(next)
	}

	const removeField = (idx: number) => {
		if (!tpl) return
		const next = { ...tpl, fields: [...tpl.fields] }
		next.fields.splice(idx, 1)
		setTpl(next)
		setErrorMsg('')
	}

	// ウィジェット管理機能
	const addWidget = (widgetId: string) => {
		if (!tpl || tpl.widgets.includes(widgetId)) return
		const next = { ...tpl, widgets: [...tpl.widgets, widgetId] }
		setTpl(next)
		setErrorMsg('')
	}

	const removeWidget = (widgetId: string) => {
		if (!tpl) return
		const next = { ...tpl, widgets: tpl.widgets.filter(id => id !== widgetId) }
		setTpl(next)
		setErrorMsg('')
	}

	const moveWidget = (fromIndex: number, toIndex: number) => {
		if (!tpl) return
		const widgets = [...tpl.widgets]
		const [moved] = widgets.splice(fromIndex, 1)
		widgets.splice(toIndex, 0, moved)
		const next = { ...tpl, widgets }
		setTpl(next)
		setErrorMsg('')
	}

	const validate = () => {
		if (!tpl) return '内部エラー'
		const keys = new Set<string>()
		const keyRe = /^[a-z0-9_\-]+$/
		for (const f of tpl.fields) {
			const k = (f.key || '').trim().toLowerCase()
			const label = (f.label || '').trim()
			if (!k || !label) return 'キーとラベルは必須です'
			if (!keyRe.test(k)) return 'キーは英数・_・- のみ使用できます'
			if (keys.has(k)) return `キーが重複しています: ${k}`
			keys.add(k)
		}
		if (tpl.fields.length > 30) return '項目は最大 30 個までです'
		return ''
	}

	const save = async () => {
		if (!tpl) return
		setSavedMsg('')
		const verr = validate()
		if (verr) {
			setErrorMsg(verr)
			return
		}
		const res = await fetch(
			`${API_BASE}/api/article-templates/${tpl.type}`,
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: tpl.name,
					fields: tpl.fields,
					prompt_template: tpl.prompt_template,
					widgets: tpl.widgets,
				}),
			}
		)
		if (res.ok) {
			setSavedMsg('保存しました')
			setErrorMsg('')
		} else {
			let detail = ''
			try {
				const j = await res.json()
				detail = j?.detail || ''
			} catch (_) {}
			setSavedMsg('保存に失敗しました')
			setErrorMsg(detail || '入力を確認してください')
		}
	}

	const del = async () => {
		if (!tpl) return
		setSavedMsg('')
		const res = await fetch(
			`${API_BASE}/api/article-templates/${tpl.type}`,
			{
				method: 'DELETE',
			}
		)
		if (res.ok) {
			setSavedMsg('初期状態に戻しました')
			setErrorMsg('')
			// 再ロード（デフォルトに戻る）
			load(tpl.type)
		} else setSavedMsg('削除に失敗しました')
	}

	const preview = useMemo(() => {
		if (!tpl) return ''
		const lines: string[] = []
		lines.push(`# ${tpl.name}`)
		lines.push('項目一覧:')
		for (const f of tpl.fields) lines.push(`- ${f.label} (${f.key})`)
		
		if (tpl.widgets && tpl.widgets.length > 0) {
			lines.push('\nウィジェット:')
			for (const widgetId of tpl.widgets) {
				const widget = availableWidgets.find(w => w.id === widgetId)
				lines.push(`- ${widget ? widget.name : widgetId}`)
			}
		}
		
		if (tpl.prompt_template?.trim()) {
			lines.push('\n--- プロンプトテンプレプレビュー ---')
			lines.push(tpl.prompt_template)
		}
		return lines.join('\n')
	}, [tpl, availableWidgets])

	return (
		<div style={{ maxWidth: 1000, margin: '2rem auto', padding: '0 1rem' }}>
			<h1>記事テンプレート編集</h1>
			{errorMsg && (
				<div style={{ color: '#a00', marginTop: 8 }}>{errorMsg}</div>
			)}
			<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
				{types.map((t) => (
					<button
						key={t}
						onClick={() => setCurrent(t)}
						style={{
							padding: '6px 10px',
							background: current === t ? '#333' : '#eee',
							color: current === t ? '#fff' : '#222',
							border: '1px solid #ccc',
						}}>
						{t === 'url'
							? 'URL コンテキスト'
							: t === 'note'
							? '雑記'
							: '書評'}
					</button>
				))}
			</div>

			{loading && <div style={{ marginTop: 12 }}>読み込み中...</div>}

			{tpl && (
				<div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
					<div style={{ display: 'flex', gap: 8 }}>
						<input
							value={tpl.name}
							onChange={(e) =>
								setTpl({ ...tpl, name: e.target.value })
							}
							placeholder="テンプレート名"
							style={{ flex: 1 }}
						/>
						<button onClick={save}>保存</button>
						<button onClick={del} style={{ color: '#a00' }}>
							初期状態へ戻す
						</button>
						{savedMsg && <span>{savedMsg}</span>}
					</div>

					<div>
						<strong>入力項目</strong>
						<div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
							{tpl.fields.map((f, i) => (
								<div
									key={i}
									style={{ display: 'flex', gap: 6 }}>
									<input
										placeholder="キー (英数字/スネーク推奨)"
										value={f.key}
										onChange={(e) =>
											updateField(
												i,
												'key',
												e.target.value
											)
										}
										style={{ width: 200 }}
									/>
									<input
										placeholder="ラベル"
										value={f.label}
										onChange={(e) =>
											updateField(
												i,
												'label',
												e.target.value
											)
										}
										style={{ flex: 1 }}
									/>
									<select
										value={f.input_type}
										onChange={(e) =>
											updateField(
												i,
												'input_type',
												e.target
													.value as Field['input_type']
											)
										}>
										<option value="text">テキスト</option>
										<option value="textarea">複数行</option>
									</select>
									<button
										onClick={() => removeField(i)}
										style={{ color: '#a00' }}>
										削除
									</button>
								</div>
							))}
							<button onClick={addField}>項目を追加</button>
						</div>
					</div>

					<div>
						<strong>プロンプトテンプレート</strong>
						<textarea
							value={tpl.prompt_template}
							onChange={(e) =>
								setTpl({
									...tpl,
									prompt_template: e.target.value,
								})
							}
							rows={10}
							style={{ width: '100%' }}
							placeholder="{{title}}, {{style}}, {{length}}, {{bullets}}, {{highlights}}, {{url_context}}, {{base}} などが使用可能"
						/>
					</div>

					<div>
						<strong>ウィジェット設定</strong>
						<div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
							<div>
								<strong style={{ fontSize: 14 }}>利用中のウィジェット</strong>
								{tpl.widgets.length === 0 ? (
									<div style={{ fontSize: 12, color: '#666', padding: 8 }}>
										利用中のウィジェットはありません
									</div>
								) : (
									<div style={{ border: '1px solid #ddd', padding: 8, marginTop: 4 }}>
										{tpl.widgets.map((widgetId, index) => {
											const widget = availableWidgets.find(w => w.id === widgetId)
											return (
												<div
													key={widgetId}
													style={{
														display: 'flex',
														alignItems: 'center',
														gap: 8,
														padding: '4px 0',
														borderBottom: index < tpl.widgets.length - 1 ? '1px solid #eee' : 'none'
													}}>
													<div style={{ flex: 1 }}>
														<strong>{widget ? widget.name : widgetId}</strong>
														{widget && (
															<div style={{ fontSize: 12, color: '#666' }}>
																{widget.description}
															</div>
														)}
													</div>
													<div style={{ display: 'flex', gap: 4 }}>
														{index > 0 && (
															<button
																onClick={() => moveWidget(index, index - 1)}
																style={{ fontSize: 12, padding: '2px 6px' }}
																title="上に移動">
																↑
															</button>
														)}
														{index < tpl.widgets.length - 1 && (
															<button
																onClick={() => moveWidget(index, index + 1)}
																style={{ fontSize: 12, padding: '2px 6px' }}
																title="下に移動">
																↓
															</button>
														)}
														<button
															onClick={() => removeWidget(widgetId)}
															style={{ fontSize: 12, padding: '2px 6px', color: '#a00' }}
															title="削除">
															削除
														</button>
													</div>
												</div>
											)
										})}
									</div>
								)}
							</div>
							
							<div>
								<strong style={{ fontSize: 14 }}>追加可能なウィジェット</strong>
								<div style={{ display: 'grid', gap: 4, marginTop: 4 }}>
									{availableWidgets
										.filter(widget => !tpl.widgets.includes(widget.id))
										.map(widget => (
											<div
												key={widget.id}
												style={{
													display: 'flex',
													alignItems: 'center',
													gap: 8,
													padding: 8,
													border: '1px solid #eee',
													background: '#fafafa'
												}}>
												<div style={{ flex: 1 }}>
													<strong>{widget.name}</strong>
													<div style={{ fontSize: 12, color: '#666' }}>
														{widget.description}
													</div>
												</div>
												<button
													onClick={() => addWidget(widget.id)}
													style={{ fontSize: 12, padding: '4px 8px' }}>
													追加
												</button>
											</div>
										))}
								</div>
								{availableWidgets.filter(w => !tpl.widgets.includes(w.id)).length === 0 && (
									<div style={{ fontSize: 12, color: '#666', padding: 8 }}>
										すべてのウィジェットが利用中です
									</div>
								)}
							</div>
						</div>
					</div>

					<div>
						<strong>プレビュー</strong>
						<pre
							style={{
								background: '#f7f7f7',
								padding: 12,
								whiteSpace: 'pre-wrap',
								border: '1px solid #ddd',
							}}>
							{preview}
						</pre>
					</div>
				</div>
			)}
		</div>
	)
}
