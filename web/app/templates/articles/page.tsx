'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
	DragDropContext,
	Droppable,
	Draggable,
	type DropResult,
} from '@hello-pangea/dnd'

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

	// @補完用の状態
	const promptRef = useRef<HTMLTextAreaElement | null>(null)
	const [suggestOpen, setSuggestOpen] = useState(false)
	const [suggestQuery, setSuggestQuery] = useState('')
	const [suggestItems, setSuggestItems] = useState<string[]>([])
	const [suggestIndex, setSuggestIndex] = useState(0)

	useEffect(() => {
		load(current)
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [current])

	useEffect(() => {
		;(async () => {
			try {
				const r = await fetch(
					`${API_BASE}/api/article-templates/widgets/available`
				)
				if (r.ok) {
					const data = await r.json()
					setAvailableWidgets(data.widgets || [])
				}
			} catch {}
		})()
	}, [])

	const load = async (t: 'url' | 'note' | 'review') => {
		setLoading(true)
		setSavedMsg('')
		try {
			const res = await fetch(`${API_BASE}/api/article-templates/${t}`)
			if (res.ok) {
				const json = (await res.json()) as ArticleTemplate
				if (!json.widgets) {
					json.widgets = []
				}
				setTpl(json)
				setErrorMsg('')
			}
		} catch (_) {
			// noop
		} finally {
			setLoading(false)
		}
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
		const next = {
			...tpl,
			widgets: tpl.widgets.filter((id) => id !== widgetId),
		}
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

	const onDragEnd = (result: DropResult) => {
		if (!tpl) return
		const { destination, source } = result
		if (!destination) return
		if (
			destination.droppableId === source.droppableId &&
			destination.index === source.index
		)
			return
		moveWidget(source.index, destination.index)
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

	// 変数候補（@補完）
	const variableCandidates = useMemo(() => {
		const base = ['title', 'style', 'length', 'bullets', 'base']
		const extra: string[] = []
		const ws = tpl?.widgets || []
		if (ws.includes('url_context')) extra.push('url_context')
		if (ws.includes('kindle')) extra.push('highlights')
		if (ws.includes('past_posts')) extra.push('past_posts')
		const fieldKeys = (tpl?.fields || [])
			.map((f) => (f.key || '').trim())
			.filter(Boolean)
		return Array.from(new Set([...base, ...extra, ...fieldKeys]))
	}, [tpl?.widgets, tpl?.fields])

	// ウィジェット→提供変数
	const varsForWidget = (widgetId: string): string[] => {
		if (widgetId === 'properties')
			return (tpl?.fields || [])
				.map((f) => (f.key || '').trim())
				.filter(Boolean)
		if (widgetId === 'url_context') return ['url_context']
		if (widgetId === 'kindle') return ['highlights']
		if (widgetId === 'past_posts') return ['past_posts']
		return []
	}

	// @補完: カーソル位置から候補更新
	const updateSuggestFromCaret = () => {
		if (!tpl) return
		const ta = promptRef.current
		if (!ta) return
		const pos = ta.selectionStart ?? 0
		const text = tpl.prompt_template || ''
		const left = text.slice(0, pos)
		const atPos = left.lastIndexOf('@')
		if (atPos === -1) {
			setSuggestOpen(false)
			return
		}
		const between = left.slice(atPos + 1)
		if (/[^a-zA-Z0-9_\-]/.test(between) && between.length > 0) {
			setSuggestOpen(false)
			return
		}
		const prefix = between
		const items = variableCandidates
			.filter((v) => v.startsWith(prefix))
			.slice(0, 8)
		if (items.length === 0) {
			setSuggestOpen(false)
			return
		}
		setSuggestItems(items)
		setSuggestIndex(0)
		setSuggestQuery(prefix)
		setSuggestOpen(true)
	}

	const insertVariableFromSuggest = (name: string) => {
		if (!tpl) return
		const ta = promptRef.current
		if (!ta) return
		const pos = ta.selectionStart ?? 0
		const text = tpl.prompt_template || ''
		const left = text.slice(0, pos)
		const right = text.slice(pos)
		const atPos = left.lastIndexOf('@')
		if (atPos === -1) return
		const newLeft = left.slice(0, atPos) + `{{${name}}}`
		const next = newLeft + right
		setTpl({ ...tpl, prompt_template: next })
		requestAnimationFrame(() => {
			const el = promptRef.current
			if (!el) return
			const newPos = newLeft.length
			el.selectionStart = newPos
			el.selectionEnd = newPos
			el.focus()
		})
		setSuggestOpen(false)
	}

	const onPromptKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (
		e
	) => {
		if (!suggestOpen) return
		if (e.key === 'ArrowDown') {
			e.preventDefault()
			setSuggestIndex((i) => (i + 1) % suggestItems.length)
			return
		}
		if (e.key === 'ArrowUp') {
			e.preventDefault()
			setSuggestIndex(
				(i) => (i - 1 + suggestItems.length) % suggestItems.length
			)
			return
		}
		if (e.key === 'Enter' || e.key === 'Tab') {
			e.preventDefault()
			insertVariableFromSuggest(suggestItems[suggestIndex])
			return
		}
		if (e.key === 'Escape') {
			e.preventDefault()
			setSuggestOpen(false)
		}
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

	const aiPropose = async () => {
		if (!tpl) return
		try {
			const enabled = tpl.widgets || []
			const widgetMeta = availableWidgets
				.filter((w) => enabled.includes(w.id))
				.map((w) => `${w.id}: ${w.name} — ${w.description}`)
				.join('\n')

			const placeholdersBase = [
				'title',
				'style',
				'length',
				'bullets',
				'base',
			]
			const extra: string[] = []
			if (enabled.includes('url_context')) extra.push('url_context')
			if (enabled.includes('kindle')) extra.push('highlights')
			if (enabled.includes('past_posts')) extra.push('past_posts')
			const fieldKeys = enabled.includes('properties')
				? (tpl.fields || [])
						.map((f) => (f.key || '').trim())
						.filter(Boolean)
				: []
			const placeholders = [...placeholdersBase, ...extra, ...fieldKeys]

			const fieldsSpec = (tpl.fields || []).map((f) => ({
				key: f.key,
				label: f.label,
				input_type: f.input_type,
			}))

			const prompt = [
				'あなたはブログ記事生成プロンプトの設計アシスタントです。',
				'現在のテンプレートで有効なウィジェット一覧:',
				widgetMeta || '(なし)',
				'',
				'利用可能なプレースホルダー（{{var}} 形式で使用）:',
				placeholders.map((p) => `- {{${p}}}`).join('\n'),
				'',
				'ユーザが入力可能なプロパティ一覧（任意）:',
				JSON.stringify(fieldsSpec, null, 2),
				'',
				'上記を踏まえ、記事生成に適したプロンプトテンプレートを日本語で提案してください。',
				'要件:',
				'- そのまま貼り付けて使えるテンプレート本文のみを出力（説明文やコードフェンスは不要）',
				'- {{base}} セクションを中核に、利用可能なプレースホルダーを活用する',
				'- ウィジェットが無い要素には依存しない（例: Kindleが無ければ {{highlights}} を使わない）',
			].join('\n')

			const res = await fetch('/api/ai/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt }),
			})
			if (res.ok) {
				const json = await res.json()
				setTpl({ ...tpl, prompt_template: String(json.text || '') })
			}
		} catch (_) {
			// no-op
		}
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
				const widget = availableWidgets.find((w) => w.id === widgetId)
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

					{/* 入力項目セクションはプロパティセットウィジェットへ統合のため削除 */}

					<div>
						<strong>ウィジェット設定</strong>
						<span className="dnd-hint">
							ドラッグして順序を入れ替えられます
						</span>
						<div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
							<div>
								<strong style={{ fontSize: 14 }}>
									利用中のウィジェット
								</strong>
								{tpl.widgets.length === 0 ? (
									<div
										style={{
											fontSize: 12,
											color: '#666',
											padding: 8,
										}}>
										利用中のウィジェットはありません
									</div>
								) : (
									<div
										style={{
											border: '1px solid #ddd',
											padding: 8,
											marginTop: 4,
										}}>
										<DragDropContext onDragEnd={onDragEnd}>
											<Droppable droppableId="widgets">
												{(
													provided,
													droppableSnapshot
												) => (
													<div
														ref={provided.innerRef}
														{...provided.droppableProps}
														className={`dnd-list${
															droppableSnapshot.isDraggingOver
																? ' drag-over'
																: ''
														}`}>
														{tpl.widgets.map(
															(
																widgetId,
																index
															) => {
																const widget =
																	availableWidgets.find(
																		(w) =>
																			w.id ===
																			widgetId
																	)
																return (
																	<Draggable
																		key={
																			widgetId
																		}
																		draggableId={
																			widgetId
																		}
																		index={
																			index
																		}>
																		{(
																			dragProvided,
																			dragSnapshot
																		) => (
																			<div
																				ref={
																					dragProvided.innerRef
																				}
																				{...dragProvided.draggableProps}
																				className={`dnd-item${
																					dragSnapshot.isDragging
																						? ' dragging'
																						: ''
																				}`}>
																				<span
																					{...dragProvided.dragHandleProps}
																					className="dnd-handle"
																					title="ドラッグして移動"
																					aria-label="ドラッグハンドル">
																					≡
																				</span>
																				<div className="dnd-item-main">
																					<div
																						style={{
																							flex: 1,
																						}}>
																						<strong>
																							{widget
																								? widget.name
																								: widgetId}
																						</strong>
																						{(() => {
																							const vs =
																								varsForWidget(
																									widgetId
																								)
																							if (
																								vs.length ===
																								0
																							)
																								return null
																							return (
																								<div
																									style={{
																										marginTop: 4,
																										display:
																											'flex',
																										gap: 6,
																										flexWrap:
																											'wrap',
																									}}>
																									{vs.map(
																										(
																											v
																										) => (
																											<span
																												key={
																													v
																												}
																												style={{
																													fontSize: 11,
																													background:
																														'#eef',
																													border: '1px solid #ccd',
																													padding:
																														'1px 6px',
																													borderRadius: 10,
																												}}>
																												@
																												{
																													v
																												}
																											</span>
																										)
																									)}
																								</div>
																							)
																						})()}
																						{widget && (
																							<div
																								style={{
																									fontSize: 12,
																									color: '#666',
																								}}>
																								{
																									widget.description
																								}
																							</div>
																						)}
																					</div>
																					<div
																						style={{
																							display:
																								'flex',
																							gap: 4,
																						}}>
																						{index >
																							0 && (
																							<button
																								onClick={() =>
																									moveWidget(
																										index,
																										index -
																											1
																									)
																								}
																								style={{
																									fontSize: 12,
																									padding:
																										'2px 6px',
																								}}
																								title="上に移動">
																								↑
																							</button>
																						)}
																						{index <
																							tpl
																								.widgets
																								.length -
																								1 && (
																							<button
																								onClick={() =>
																									moveWidget(
																										index,
																										index +
																											1
																									)
																								}
																								style={{
																									fontSize: 12,
																									padding:
																										'2px 6px',
																								}}
																								title="下に移動">
																								↓
																							</button>
																						)}
																						<button
																							onClick={() =>
																								removeWidget(
																									widgetId
																								)
																							}
																							style={{
																								fontSize: 12,
																								padding:
																									'2px 6px',
																								color: '#a00',
																							}}
																							title="削除">
																							削除
																						</button>
																					</div>
																				</div>
																			</div>
																		)}
																	</Draggable>
																)
															}
														)}
														{provided.placeholder}
													</div>
												)}
											</Droppable>
										</DragDropContext>
									</div>
								)}
							</div>

							<div>
								<strong style={{ fontSize: 14 }}>
									追加可能なウィジェット
								</strong>
								<div
									style={{
										display: 'grid',
										gap: 4,
										marginTop: 4,
									}}>
									{availableWidgets
										.filter(
											(widget) =>
												!tpl.widgets.includes(widget.id)
										)
										.map((widget) => (
											<div
												key={widget.id}
												style={{
													display: 'flex',
													alignItems: 'center',
													gap: 8,
													padding: 8,
													border: '1px solid #eee',
													background: '#fafafa',
												}}>
												<div style={{ flex: 1 }}>
													<strong>
														{widget.name}
													</strong>
													<div
														style={{
															fontSize: 12,
															color: '#666',
														}}>
														{widget.description}
													</div>
												</div>
												<button
													onClick={() =>
														addWidget(widget.id)
													}
													style={{
														fontSize: 12,
														padding: '4px 8px',
													}}>
													追加
												</button>
											</div>
										))}
								</div>
								{availableWidgets.filter(
									(w) => !tpl.widgets.includes(w.id)
								).length === 0 && (
									<div
										style={{
											fontSize: 12,
											color: '#666',
											padding: 8,
										}}>
										すべてのウィジェットが利用中です
									</div>
								)}
							</div>
						</div>
					</div>

					<div>
						<strong>プロンプトテンプレート</strong>
						<div
							style={{
								display: 'flex',
								gap: 8,
								alignItems: 'center',
								marginTop: 6,
								flexWrap: 'wrap',
							}}>
							<button onClick={aiPropose}>
								ウィジェットに基づき提案
							</button>
						</div>
						<textarea
							ref={promptRef}
							value={tpl.prompt_template}
							onChange={(e) => {
								setTpl({
									...tpl,
									prompt_template: e.target.value,
								})
								updateSuggestFromCaret()
							}}
							onKeyDown={onPromptKeyDown}
							onClick={updateSuggestFromCaret}
							onKeyUp={updateSuggestFromCaret}
							onBlur={() => setSuggestOpen(false)}
							rows={10}
							style={{ width: '100%' }}
							placeholder="{{title}}, {{style}}, {{length}}, {{bullets}}, {{highlights}}, {{url_context}}, {{base}} などが使用可能"
						/>
						{suggestOpen && (
							<div style={{ position: 'relative' }}>
								<div
									role="listbox"
									style={{
										position: 'absolute',
										right: 0,
										bottom: 4,
										zIndex: 10,
										background: '#fff',
										border: '1px solid #ddd',
										boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
										minWidth: 220,
									}}>
									<div
										style={{
											padding: '6px 8px',
											borderBottom: '1px solid #eee',
											fontSize: 12,
											color: '#555',
										}}>
										@{suggestQuery}
									</div>
									{suggestItems.map((item, i) => (
										<button
											key={item}
											onMouseDown={(e) => {
												e.preventDefault()
												insertVariableFromSuggest(item)
											}}
											style={{
												display: 'block',
												width: '100%',
												textAlign: 'left',
												padding: '6px 8px',
												background:
													i === suggestIndex
														? '#eef5ff'
														: '#fff',
												borderBottom:
													'1px solid #f0f0f0',
												cursor: 'pointer',
												fontFamily: 'inherit',
												fontSize: 13,
											}}>
											{'{{'}
											{item}
											{'}}'}
										</button>
									))}
								</div>
							</div>
						)}
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
