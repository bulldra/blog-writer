'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
	DragDropContext,
	Droppable,
	Draggable,
	type DropResult,
} from '@hello-pangea/dnd'
import TemplateList from './TemplateList'

export type Field = {
	key: string
	label: string
	input_type: 'text' | 'textarea'
}
export type Widget = { id: string; name: string; description: string }
export type ArticleTemplate = {
	type: 'url' | 'note' | 'review' | string
	name: string
	fields: Field[]
	prompt_template: string
	widgets?: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function TemplatesPage() {
	const [list, setList] = useState<ArticleTemplate[]>([])
	const [currentType, setCurrentType] = useState<string>('url')
	const current = useMemo(
		() => list.find((x) => x.type === currentType),
		[list, currentType]
	)

	const [name, setName] = useState('')
	const [widgets, setWidgets] = useState<string[]>([])
	const [fields, setFields] = useState<Field[]>([])
	const [promptText, setPromptText] = useState('')
	const [saving, setSaving] = useState(false)
	const [proposing, setProposing] = useState(false)
	const [error, setError] = useState<string>('')
	const [availableWidgets, setAvailableWidgets] = useState<Widget[]>([])

	const promptRef = useRef<HTMLTextAreaElement | null>(null)
	const [suggestOpen, setSuggestOpen] = useState(false)
	const [suggestQuery, setSuggestQuery] = useState('')
	const [suggestItems, setSuggestItems] = useState<string[]>([])
	const [suggestIndex, setSuggestIndex] = useState(0)

	useEffect(() => {
		;(async () => {
			try {
				const res = await fetch(`${API_BASE}/api/article-templates`)
				if (res.ok) setList((await res.json()) as ArticleTemplate[])
			} catch {}
		})()
	}, [])

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

	useEffect(() => {
		if (list.length > 0 && !list.find((x) => x.type === currentType)) {
			setCurrentType(list[0].type)
		}
	}, [list, currentType])

	useEffect(() => {
		if (!current) return
		setName(current.name)
		setFields(
			(current.fields || []).map((f) => ({
				key: f.key || '',
				label: f.label || f.key || '',
				input_type: (f.input_type as Field['input_type']) || 'text',
			}))
		)
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

	const variableCandidates = useMemo(() => {
		const base = ['title', 'style', 'length', 'bullets', 'base']
		const extra: string[] = []
		if (widgets.includes('url_context')) extra.push('url_context')
		if (widgets.includes('kindle')) extra.push('highlights')
		if (widgets.includes('past_posts')) extra.push('past_posts')
		const fieldKeys = widgets.includes('properties')
			? fields.map((f) => (f.key || '').trim()).filter(Boolean)
			: []
		return Array.from(new Set([...base, ...extra, ...fieldKeys]))
	}, [widgets, fields])

	const validate = (): string => {
		const keyRe = /^[a-z0-9_\-]+$/
		const keys = new Set<string>()
		for (const f of fields) {
			const k = (f.key || '').trim().toLowerCase()
			const label = (f.label || '').trim()
			if (!k || !label) return 'キーとラベルは必須です'
			if (!keyRe.test(k)) return 'キーは英数・_・- のみ使用できます'
			if (keys.has(k)) return `キーが重複しています: ${k}`
			keys.add(k)
		}
		if (fields.length > 30) return '項目は最大 30 個までです'
		return ''
	}

	const saveArticleTemplate = async () => {
		if (!current) return
		setSaving(true)
		setError('')
		try {
			const verr = validate()
			if (verr) {
				setError(verr)
				return
			}
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
				let msg = ''
				try {
					const j = await res.json()
					msg = j?.detail || ''
				} catch {}
				setError(msg || '保存に失敗しました')
			}
		} catch {
			setError('保存に失敗しました')
		} finally {
			setSaving(false)
		}
	}

	const aiPropose = async () => {
		try {
			setProposing(true)
			const enabled = widgets
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
				? fields.map((f) => (f.key || '').trim()).filter(Boolean)
				: []
			const placeholders = [...placeholdersBase, ...extra, ...fieldKeys]
			const fieldsSpec = fields.map((f) => ({
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
				setPromptText(String(json.text || ''))
			}
		} catch {
		} finally {
			setProposing(false)
		}
	}

	const varsForWidget = (widgetId: string): string[] => {
		if (widgetId === 'properties')
			return fields.map((f) => (f.key || '').trim()).filter(Boolean)
		if (widgetId === 'url_context') return ['url_context']
		if (widgetId === 'kindle') return ['highlights']
		if (widgetId === 'past_posts') return ['past_posts']
		return []
	}

	const updateSuggestFromCaret = () => {
		const ta = promptRef.current
		if (!ta) return
		const pos = ta.selectionStart ?? 0
		const text = promptText
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
		const ta = promptRef.current
		if (!ta) return
		const pos = ta.selectionStart ?? 0
		const text = promptText
		const left = text.slice(0, pos)
		const right = text.slice(pos)
		const atPos = left.lastIndexOf('@')
		if (atPos === -1) return
		const newLeft = left.slice(0, atPos) + `{{${name}}}`
		const next = newLeft + right
		setPromptText(next)
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

	const updateField = (idx: number, key: keyof Field, val: string) => {
		setFields((prev) => {
			const next = [...prev]
			next[idx] = { ...next[idx], [key]: val }
			return next
		})
		setError('')
	}
	const addField = () => {
		if (fields.length >= 30) {
			setError('項目は最大 30 個までです')
			return
		}
		setFields((prev) => [
			...prev,
			{ key: '', label: '', input_type: 'text' },
		])
	}
	const removeField = (idx: number) => {
		setFields((prev) => prev.filter((_, i) => i !== idx))
		setError('')
	}

	const onDragEnd = (result: DropResult) => {
		const { destination, source } = result
		if (!destination) return
		if (
			destination.droppableId === source.droppableId &&
			destination.index === source.index
		)
			return
		setWidgets((prev) => {
			const arr = [...prev]
			const [m] = arr.splice(source.index, 1)
			arr.splice(destination.index, 0, m)
			return arr
		})
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
				<div
					style={{
						border: '1px solid #ddd',
						background: '#fff',
						padding: 8,
					}}>
					<div
						style={{
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'space-between',
						}}>
						<strong>テンプレート一覧</strong>
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
							}}
							style={{ fontSize: 12, padding: '4px 8px' }}>
							+ 追加
						</button>
					</div>
					<TemplateList
						list={list}
						currentType={currentType}
						onSelect={(type) => setCurrentType(type)}
						onDelete={(type) => {
							if (!confirm(`${type} を削除しますか？`)) return
							fetch(
								`${API_BASE}/api/article-templates/${encodeURIComponent(
									type
								)}`,
								{ method: 'DELETE' }
							)
								.then((r) => r.ok && r.json())
								.then(() => {
									setList((prev) =>
										prev.filter((x) => x.type !== type)
									)
									if (currentType === type)
										setCurrentType('url')
								})
								.catch(() => {})
						}}
					/>
				</div>

				<div style={{ display: 'grid', gap: 12 }}>
					<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
						<input
							placeholder="テンプレート表示名"
							value={name}
							onChange={(e) => setName(e.target.value)}
							style={{ flex: 1 }}
						/>
						<button onClick={aiPropose} disabled={proposing}>
							{proposing ? '提案中…' : 'AIでプロンプト雛形を提案'}
						</button>
					</div>

					<div
						style={{
							opacity: proposing ? 0.6 : 1,
							pointerEvents: proposing
								? ('none' as const)
								: 'auto',
						}}>
						<strong>ウィジェット設定</strong>
						<span className="dnd-hint">
							ドラッグして順序を入れ替えられます
						</span>
						<div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
							<div>
								<strong style={{ fontSize: 14 }}>
									利用中のウィジェット
								</strong>
								{widgets.length === 0 ? (
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
										<div
											style={{
												opacity: proposing ? 0.6 : 1,
												pointerEvents: proposing
													? ('none' as const)
													: 'auto',
											}}>
											<DragDropContext
												onDragEnd={onDragEnd}>
												<Droppable droppableId="widgets">
													{(provided, snapshot) => (
														<div
															ref={
																provided.innerRef
															}
															{...provided.droppableProps}
															className={`dnd-list${
																snapshot.isDraggingOver
																	? ' drag-over'
																	: ''
															}`}>
															{widgets.map(
																(
																	widgetId,
																	index
																) => {
																	const widget =
																		availableWidgets.find(
																			(
																				w
																			) =>
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
																								display:
																									'flex',
																								gap: 8,
																								alignItems:
																									'center',
																							}}>
																							<strong
																								style={{
																									flex: 1,
																								}}>
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
																												<button
																													key={
																														v
																													}
																													onClick={() =>
																														insertVariableFromSuggest(
																															v
																														)
																													}
																													style={{
																														fontSize: 11,
																														background:
																															'#eef',
																														border: '1px solid #ccd',
																														padding:
																															'1px 6px',
																														borderRadius: 10,
																														cursor: 'pointer',
																													}}
																													title="変数を挿入">
																													@
																													{
																														v
																													}
																												</button>
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
																							{widgetId ===
																								'properties' && (
																								<div
																									style={{
																										marginTop: 8,
																										display:
																											'grid',
																										gap: 8,
																									}}>
																									{fields.map(
																										(
																											f,
																											i
																										) => (
																											<div
																												key={
																													i
																												}
																												style={{
																													display:
																														'flex',
																													gap: 6,
																												}}>
																												<input
																													placeholder="キー (英数字/スネーク推奨)"
																													value={
																														f.key
																													}
																													onChange={(
																														e
																													) =>
																														updateField(
																															i,
																															'key',
																															e
																																.target
																																.value
																														)
																													}
																													style={{
																														width: 200,
																													}}
																												/>
																												<input
																													placeholder="ラベル"
																													value={
																														f.label
																													}
																													onChange={(
																														e
																													) =>
																														updateField(
																															i,
																															'label',
																															e
																																.target
																																.value
																														)
																													}
																													style={{
																														flex: 1,
																													}}
																												/>
																												<select
																													value={
																														f.input_type
																													}
																													onChange={(
																														e
																													) =>
																														updateField(
																															i,
																															'input_type',
																															e
																																.target
																																.value as Field['input_type']
																														)
																													}>
																													<option value="text">
																														テキスト
																													</option>
																													<option value="textarea">
																														複数行
																													</option>
																												</select>
																												<button
																													onClick={() =>
																														removeField(
																															i
																														)
																													}
																													style={{
																														color: '#a00',
																													}}>
																													削除
																												</button>
																											</div>
																										)
																									)}
																									<div>
																										<button
																											onClick={
																												addField
																											}>
																											+
																											項目を追加
																										</button>
																										{fields.length ===
																											0 && (
																											<span
																												style={{
																													color: '#666',
																													fontSize: 12,
																													marginLeft: 8,
																												}}>
																												入力項目は任意です。
																											</span>
																										)}
																									</div>
																								</div>
																							)}
																						</div>
																						<div
																							style={{
																								display:
																									'flex',
																								gap: 4,
																							}}>
																							<button
																								onClick={() =>
																									setWidgets(
																										(
																											prev
																										) =>
																											prev.filter(
																												(
																													id
																												) =>
																													id !==
																													widgetId
																											)
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
															{
																provided.placeholder
															}
														</div>
													)}
												</Droppable>
											</DragDropContext>
										</div>
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
										.filter((w) => !widgets.includes(w.id))
										.map((w) => (
											<div
												key={w.id}
												style={{
													display: 'flex',
													alignItems: 'center',
													gap: 8,
													padding: 8,
													border: '1px solid #eee',
													background: '#fafafa',
												}}>
												<div style={{ flex: 1 }}>
													<strong>{w.name}</strong>
													<div
														style={{
															fontSize: 12,
															color: '#666',
														}}>
														{w.description}
													</div>
												</div>
												<button
													onClick={() =>
														setWidgets((prev) => [
															...prev,
															w.id,
														])
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
									(w) => !widgets.includes(w.id)
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
							<button onClick={aiPropose} disabled={proposing}>
								{proposing
									? '提案中…'
									: 'ウィジェットに基づき提案'}
							</button>
						</div>
						<textarea
							ref={promptRef}
							placeholder={
								'{{base}}\n---\n{{bullets}}\n---\n任意の変数: {{title}}, {{style}}, {{length}}, {{highlights}}, {{url_context}} など'
							}
							value={promptText}
							onChange={(e) => {
								setPromptText(e.target.value)
								updateSuggestFromCaret()
							}}
							onKeyDown={onPromptKeyDown}
							onClick={updateSuggestFromCaret}
							onKeyUp={updateSuggestFromCaret}
							onBlur={() => setSuggestOpen(false)}
							rows={12}
							style={{ width: '100%', marginTop: 6 }}
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
