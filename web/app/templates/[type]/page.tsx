'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import {
	DragDropContext,
	Droppable,
	Draggable,
	type DropResult,
} from '@hello-pangea/dnd'
import { useRouter } from 'next/navigation'

type Field = {
	key: string
	label: string
	input_type: 'text' | 'textarea'
}
type Widget = { id: string; name: string; description: string }
type ArticleTemplate = {
	type: string
	name: string
	description?: string
	fields: Field[]
	prompt_template: string
	widgets?: string[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function TemplateDetailPage({
	params,
}: {
	params: { type: string }
}) {
	const router = useRouter()
	const { type } = params
	const [row, setRow] = useState<ArticleTemplate | null>(null)
	const [availableWidgets, setAvailableWidgets] = useState<Widget[]>([])
	const [saving, setSaving] = useState(false)
	const [proposing, setProposing] = useState(false)
	const [executing, setExecuting] = useState(false)
	const [error, setError] = useState('')
	const [executeResult, setExecuteResult] = useState('')

	const [name, setName] = useState('')
	const [fields, setFields] = useState<Field[]>([])
	const [description, setDescription] = useState('')
	const [widgets, setWidgets] = useState<string[]>([])
	const [promptText, setPromptText] = useState('')
	const promptRef = useRef<HTMLTextAreaElement | null>(null)
	const [suggestOpen, setSuggestOpen] = useState(false)
	const [suggestQuery, setSuggestQuery] = useState('')
	const [suggestItems, setSuggestItems] = useState<string[]>([])
	const [suggestIndex, setSuggestIndex] = useState(0)

	useEffect(() => {
		;(async () => {
			try {
				const r = await fetch(
					`${API_BASE}/api/article-templates/${encodeURIComponent(
						type
					)}`
				)
				if (r.ok) {
					const j = (await r.json()) as ArticleTemplate
					setRow(j)
				}
			} catch {}
		})()
	}, [type])

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
		if (!row) return
		setName(row.name || row.type)
		setFields(
			(row.fields || []).map((f) => ({
				key: f.key || '',
				label: f.label || f.key || '',
				input_type: (f.input_type as Field['input_type']) || 'text',
			}))
		)
		setPromptText(row.prompt_template || '')
		setWidgets(Array.isArray(row.widgets) ? row.widgets! : [])
		setDescription(row.description || '')
		setError('')
	}, [row])

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

	const save = async () => {
		if (!row) return
		setSaving(true)
		setError('')
		try {
			const verr = validate()
			if (verr) {
				setError(verr)
				return
			}
			const res = await fetch(
				`${API_BASE}/api/article-templates/${encodeURIComponent(
					row.type
				)}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						name,
						description,
						fields,
						prompt_template: promptText,
						widgets,
					}),
				}
			)
			if (!res.ok) {
				let msg = ''
				try {
					const j = await res.json()
					msg = j?.detail || ''
				} catch {}
				setError(msg || '保存に失敗しました')
				return
			}
			const saved = (await res.json()) as ArticleTemplate
			setRow(saved)
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

	const executeTemplate = async () => {
		if (!promptText.trim()) {
			setError('実行するプロンプトテンプレートがありません')
			return
		}
		try {
			setExecuting(true)
			setError('')
			setExecuteResult('')
			
			// デモ用のサンプルデータ
			const sampleTitle = '新しい記事のタイトル'
			const sampleBullets = [
				'ポイント1: 重要な内容について説明',
				'ポイント2: 具体例を挙げて解説',
				'ポイント3: まとめと今後の展望'
			]
			
			// プロンプトテンプレートを実行
			const res = await fetch(`${API_BASE}/api/ai/from-bullets`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					bullets: sampleBullets,
					title: sampleTitle,
					style: '丁寧で分かりやすい文体',
					length: '中程度（1000-1500文字）',
					prompt_template: promptText,
					url_context: widgets.includes('url_context') ? 'https://example.com' : undefined,
					highlights: widgets.includes('kindle') ? ['サンプルハイライト'] : undefined,
					extra_context: {},
				}),
			})
			
			if (res.ok) {
				const json = await res.json()
				setExecuteResult(String(json.text || ''))
			} else {
				setError('テンプレートの実行に失敗しました')
			}
		} catch (err) {
			setError('テンプレートの実行中にエラーが発生しました')
		} finally {
			setExecuting(false)
		}
	}

	// const updateField = (idx: number, key: keyof Field, val: string) => {
	// 	setFields((prev) => {
	// 		const next = [...prev]
	// 		next[idx] = { ...next[idx], [key]: val }
	// 		return next
	// 	})
	// 	setError('')
	// }
	// const addField = () => {
	// 	if (fields.length >= 30) {
	// 		setError('項目は最大 30 個までです')
	// 		return
	// 	}
	// 	setFields((prev) => [
	// 		...prev,
	// 		{ key: '', label: '', input_type: 'text' },
	// 	])
	// }
	// const removeField = (idx: number) => {
	// 	setFields((prev) => prev.filter((_, i) => i !== idx))
	// 	setError('')
	// }

	const varsForWidget = (widgetId: string): string[] => {
		if (widgetId === 'properties')
			return fields.map((f) => (f.key || '').trim()).filter(Boolean)
		if (widgetId === 'url_context') return ['url_context']
		if (widgetId === 'kindle') return ['highlights']
		if (widgetId === 'past_posts') return ['past_posts']
		return []
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
			<button
				onClick={() => router.push('/templates')}
				style={{ marginBottom: 8 }}>
				← 一覧へ
			</button>
			<h1>テンプレート編集: {type}</h1>
			<div
				style={{
					display: 'flex',
					gap: 8,
					flexWrap: 'wrap',
					marginTop: 8,
				}}>
				<input
					placeholder="テンプレート表示名"
					value={name}
					onChange={(e) => setName(e.target.value)}
					style={{ flex: 1 }}
				/>
				<input
					placeholder="一覧で表示する説明文（任意）"
					value={description}
					onChange={(e) => setDescription(e.target.value)}
					style={{ flex: 2 }}
				/>
				<button onClick={aiPropose} disabled={proposing}>
					{proposing ? '提案中…' : 'AIでプロンプト雛形を提案'}
				</button>
			</div>

			<div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
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
									<DragDropContext onDragEnd={onDragEnd}>
										<Droppable droppableId="widgets">
											{(provided, snapshot) => (
												<div
													ref={provided.innerRef}
													{...provided.droppableProps}
													className={`dnd-list${
														snapshot.isDraggingOver
															? ' drag-over'
															: ''
													}`}>
													{widgets.map(
														(widgetId, index) => {
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
									display: 'flex',
									gap: 8,
									marginTop: 4,
									alignItems: 'center',
									flexWrap: 'wrap',
								}}>
								<select
									value={''}
									onChange={(e) => {
										const id = e.target.value
										if (!id) return
										if (widgets.includes(id)) return
										setWidgets((prev) => [...prev, id])
									}}
									style={{ minWidth: 260 }}>
									<option value="">
										追加するウィジェットを選択
									</option>
									{availableWidgets
										.filter((w) => !widgets.includes(w.id))
										.map((w) => (
											<option key={w.id} value={w.id}>
												{w.name} — {w.description}
											</option>
										))}
								</select>
								{availableWidgets.filter(
									(w) => !widgets.includes(w.id)
								).length === 0 && (
									<span
										style={{ fontSize: 12, color: '#666' }}>
										追加可能なウィジェットはありません
									</span>
								)}
							</div>
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
							{proposing ? '提案中…' : 'ウィジェットに基づき提案'}
						</button>
						<button 
							onClick={executeTemplate} 
							disabled={executing || !promptText.trim()}
							style={{
								backgroundColor: executing ? '#ccc' : '#4CAF50',
								color: 'white',
								border: 'none',
								padding: '8px 16px',
								borderRadius: '4px',
								cursor: executing || !promptText.trim() ? 'not-allowed' : 'pointer'
							}}
						>
							{executing ? 'テンプレート実行中…' : 'テンプレートを実行'}
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
											borderBottom: '1px solid #f0f0f0',
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

				{/* テンプレート実行結果 */}
				{executeResult && (
					<div style={{ marginTop: 20 }}>
						<strong>テンプレート実行結果</strong>
						<div 
							style={{
								marginTop: 8,
								padding: 12,
								border: '1px solid #ddd',
								borderRadius: 4,
								backgroundColor: '#f9f9f9',
								whiteSpace: 'pre-wrap',
								fontSize: 14,
								maxHeight: 400,
								overflow: 'auto'
							}}
						>
							{executeResult}
						</div>
					</div>
				)}

				<div
					style={{
						display: 'flex',
						gap: 8,
						alignItems: 'center',
						flexWrap: 'wrap',
						marginTop: 20,
					}}>
					<button onClick={save} disabled={saving}>
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
	)
}
