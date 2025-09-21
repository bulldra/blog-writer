'use client'

import { useEffect, useMemo, useState } from 'react'
import {
	DragDropContext,
	Droppable,
	Draggable,
	type DropResult,
} from '@hello-pangea/dnd'
import { useRouter } from 'next/navigation'
import ScrapeWidget from '../../components/ScrapeWidget'
import XWidget, {
	type XWidgetState,
	type XPreviewMode,
} from '../../components/XWidget'

// 型定義
type Field = {
	key: string
	label: string
	input_type: 'text' | 'textarea' | 'date' | 'select'
	options?: string[]
}

type WidgetMeta = { id: string; name: string; description: string }

type ServerArticleTemplate = {
	type: string
	name: string
	description?: string
	fields: Field[]
	prompt_template: string
	widgets?: string[]
}

type UIWidget = { id: string; uid: string }

type ScrapeState = {
	url: string
	selector: string
	mode: 'text' | 'screenshot' | 'both'
	timeoutMs: number
	headless: boolean
	width: number
	height: number
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000'

function newUid(): string {
	return `w_${Date.now().toString(36)}_${Math.random()
		.toString(36)
		.slice(2, 8)}`
}

function getMaxPosts(state?: Partial<XWidgetState>): number {
	const legacy: number | undefined = (
		state as { max_posts?: number } | undefined
	)?.max_posts
	return state?.maxPosts ?? legacy ?? 20
}

export default function TemplateDetailPage({
	params,
}: {
	params: { type: string }
}) {
	const router = useRouter()
	const { type } = params

	const [loading, setLoading] = useState(true)
	const [saving, setSaving] = useState(false)
	const [error, setError] = useState('')
	const [proposing, setProposing] = useState(false)

	const [name, setName] = useState('')
	const [description, setDescription] = useState('')
	const [fields, setFields] = useState<Field[]>([])
	const [promptText, setPromptText] = useState('')
	const [widgets, setWidgets] = useState<UIWidget[]>([])
	const [availableWidgets, setAvailableWidgets] = useState<WidgetMeta[]>([])

	const [scrapeMap, setScrapeMap] = useState<
		Record<string, Partial<ScrapeState>>
	>({})
	const [xMap, setXMap] = useState<Record<string, Partial<XWidgetState>>>({})

	// 入力項目（フィールド）の編集ユーティリティ
	const sanitizeKey = (s: string): string => {
		const t = s
			.toLowerCase()
			.replace(/[^a-z0-9_\-]/g, '-')
			.replace(/\-+/g, '-')
			.trim()
		return t || 'field'
	}

	const ensureUniqueKey = (base: string, idx?: number): string => {
		const b = sanitizeKey(base)
		const keys = fields.map((f, i) => (i === idx ? '__me__' : f.key))
		if (!keys.includes(b)) return b
		let i = 2
		while (keys.includes(`${b}-${i}`)) i += 1
		return `${b}-${i}`
	}

	const addTextField = () => {
		const n = fields.length + 1
		const key = ensureUniqueKey(`field-${n}`)
		setFields((prev) => [
			...prev,
			{ key, label: `項目 ${n}`, input_type: 'text' },
		])
	}

	const addSelectField = () => {
		const n = fields.length + 1
		const key = ensureUniqueKey(`select-${n}`)
		setFields((prev) => [
			...prev,
			{ key, label: `選択 ${n}`, input_type: 'select', options: [] },
		])
	}

	const quickAdd = (k: 'theme' | 'goal' | 'audience' | 'tone') => {
		const exists = fields.some((f) => f.key === k)
		if (exists) return
		const labels: Record<typeof k, string> = {
			theme: 'テーマ',
			goal: '目的',
			audience: '読者',
			tone: 'トーン',
		}
		setFields((prev) => [
			...prev,
			{ key: k, label: labels[k], input_type: 'text' },
		])
	}

	const updateField = (
		index: number,
		patch: Partial<Field>,
		{ sanitizeKeyOnly = false }: { sanitizeKeyOnly?: boolean } = {}
	) => {
		setFields((prev) => {
			const arr = [...prev]
			const old = arr[index]
			if (!old) return prev
			let next: Field = { ...old, ...patch }
			if (patch.key !== undefined) {
				const base = sanitizeKey(String(patch.key))
				next.key = ensureUniqueKey(base, index)
			} else if (sanitizeKeyOnly) {
				next.key = ensureUniqueKey(sanitizeKey(old.key), index)
			}
			if (patch.input_type && patch.input_type !== 'select') {
				next = {
					key: next.key,
					label: next.label,
					input_type:
						(patch.input_type as Field['input_type']) ||
						(next.input_type as Field['input_type']),
				}
			}
			if (patch.options) {
				const opts = (patch.options || [])
					.map((o) => String(o).trim())
					.filter((o) => !!o)
				next.options = Array.from(new Set(opts))
			}
			arr[index] = next
			return arr
		})
	}

	const removeFieldRow = (index: number) => {
		setFields((prev) => prev.filter((_, i) => i !== index))
	}

	// 初期ロード
	useEffect(() => {
		let mounted = true
		;(async () => {
			try {
				const [wres, tres] = await Promise.all([
					fetch(
						`${API_BASE}/api/article-templates/widgets/available`
					),
					fetch(
						`${API_BASE}/api/article-templates/${encodeURIComponent(
							type
						)}`
					),
				])
				if (mounted && wres.ok) {
					const data = await wres.json()
					setAvailableWidgets(
						Array.isArray(data.widgets) ? data.widgets : []
					)
				}
				if (mounted && tres.ok) {
					const t = (await tres.json()) as ServerArticleTemplate
					setName(String(t.name || ''))
					setDescription(String(t.description || ''))
					setFields(Array.isArray(t.fields) ? t.fields : [])
					setPromptText(String(t.prompt_template || ''))
					const wids = Array.isArray(t.widgets) ? t.widgets : []
					setWidgets(wids.map((id) => ({ id, uid: newUid() })))
				}
			} catch {
				if (mounted) setError('読み込みに失敗しました')
			} finally {
				if (mounted) setLoading(false)
			}
		})()
		return () => {
			mounted = false
		}
	}, [type])

	// DnD: widgets / fields 並べ替え
	const onDragEnd = (result: DropResult) => {
		const { destination, source } = result
		if (!destination) return
		if (
			destination.droppableId === source.droppableId &&
			destination.index === source.index
		)
			return
		if (
			source.droppableId === 'widgets' &&
			destination.droppableId === 'widgets'
		) {
			setWidgets((prev) => {
				const arr = [...prev]
				const [m] = arr.splice(source.index, 1)
				arr.splice(destination.index, 0, m)
				return arr
			})
			return
		}
		if (
			source.droppableId === 'fields' &&
			destination.droppableId === 'fields'
		) {
			setFields((prev) => {
				const arr = [...prev]
				const [m] = arr.splice(source.index, 1)
				arr.splice(destination.index, 0, m as Field)
				return arr
			})
			return
		}
	}

	// 追加/削除
	const addWidget = (id: string) => {
		if (!id) return
		setWidgets((prev) => [...prev, { id, uid: newUid() }])
	}
	const removeWidget = (uid: string) => {
		setWidgets((prev) => prev.filter((w) => w.uid !== uid))
	}

	// 保存（PUT）
	const save = async () => {
		try {
			setSaving(true)
			setError('')
			const payload: ServerArticleTemplate = {
				type,
				name: String(name || ''),
				description: String(description || ''),
				fields: fields.map((f) => ({
					key: f.key,
					label: f.label,
					input_type: f.input_type,
					options:
						f.input_type === 'select' ? f.options || [] : undefined,
				})),
				prompt_template: String(promptText || ''),
				widgets: widgets.map((w) => w.id),
			}
			const res = await fetch(
				`${API_BASE}/api/article-templates/${encodeURIComponent(type)}`,
				{
					method: 'PUT',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(payload),
				}
			)
			if (!res.ok) {
				const text = await res.text().catch(() => '')
				throw new Error(text || '保存に失敗しました')
			}
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e)
			setError(msg || '保存に失敗しました')
		} finally {
			setSaving(false)
		}
	}

	// LLM によるプロンプトテンプレート提案
	const aiPropose = async () => {
		try {
			setProposing(true)
			setError('')
			const enabled = widgets.map((w) => w.id)
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
			const fieldKeys = (fields || [])
				.map((f) => (f.key || '').trim())
				.filter(Boolean)
			const placeholders = Array.from(
				new Set([...placeholdersBase, ...fieldKeys])
			)

			const fieldsSpec = (fields || []).map((f) => ({
				key: f.key,
				label: f.label,
				input_type: f.input_type,
			}))

			const prompt = [
				'あなたはブログ記事やメモ生成のプロンプト設計アシスタントです。',
				'現在のテンプレートで有効なウィジェット一覧:',
				widgetMeta || '(なし)',
				'',
				'利用可能なプレースホルダー（{{var}} 形式で使用）:',
				placeholders.map((p) => `- {{${p}}}`).join('\n'),
				'',
				'ユーザが入力可能なフィールド一覧（任意）:',
				JSON.stringify(fieldsSpec, null, 2),
				'',
				'上記を踏まえ、生成に適したプロンプトテンプレートを日本語で提案してください。',
				'要件:',
				'- そのまま貼り付けて使えるテンプレート本文のみを出力（説明やコードフェンスは不要）',
				'- {{base}} を中核に、利用可能なプレースホルダーを必要に応じて活用する',
				'- 無いウィジェット由来の変数には依存しない',
			].join('\n')

			const res = await fetch('/api/ai/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt }),
			})
			if (res.ok) {
				const json = await res.json()
				setPromptText(String(json.text || ''))
			} else {
				setError('提案の生成に失敗しました')
			}
		} catch (e) {
			setError('提案の生成中にエラーが発生しました')
		} finally {
			setProposing(false)
		}
	}

	// ウィジェットの変数ヒント
	const varsForWidget = (widgetId: string): string[] => {
		if (widgetId === 'scrape') return ['url', 'selector', 'mode']
		if (widgetId === 'x') return ['url', 'mode', 'maxPosts']
		return []
	}

	const previewSummary = useMemo(() => {
		try {
			const summary = {
				type,
				name,
				description,
				fields: fields.map((f) => ({
					key: f.key,
					label: f.label,
					input_type: f.input_type,
					options:
						f.input_type === 'select' ? f.options || [] : undefined,
				})),
				widgets: widgets.map((w) => w.id),
			}
			return JSON.stringify(summary, null, 2)
		} catch {
			return ''
		}
	}, [type, name, description, fields, widgets])

	if (loading) return <div style={{ padding: 12 }}>読み込み中…</div>

	return (
		<div style={{ padding: 12 }}>
			<button
				onClick={() => router.push('/templates')}
				style={{ marginBottom: 8 }}>
				← 一覧へ
			</button>
			<h1>テンプレート編集: {type}</h1>

			{error && (
				<div style={{ color: '#a00', marginTop: 8 }}>{error}</div>
			)}

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
				<button onClick={save} disabled={saving}>
					{saving ? '保存中…' : '保存'}
				</button>
			</div>

			<div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
				{/* 入力項目（フィールド）設定 */}
				<div>
					<strong>入力項目（フィールド）</strong>
					<div
						style={{
							display: 'flex',
							gap: 6,
							marginTop: 6,
							alignItems: 'center',
							flexWrap: 'wrap',
						}}>
						<button onClick={addTextField} style={{ fontSize: 12 }}>
							+ テキスト項目
						</button>
						<button
							onClick={addSelectField}
							style={{ fontSize: 12 }}>
							+ 選択項目
						</button>
						<span style={{ fontSize: 12, color: '#666' }}>
							よく使う項目のクイック追加:
						</span>
						<button
							onClick={() => quickAdd('theme')}
							style={{ fontSize: 12 }}>
							テーマ
						</button>
						<button
							onClick={() => quickAdd('goal')}
							style={{ fontSize: 12 }}>
							目的
						</button>
						<button
							onClick={() => quickAdd('audience')}
							style={{ fontSize: 12 }}>
							読者
						</button>
						<button
							onClick={() => quickAdd('tone')}
							style={{ fontSize: 12 }}>
							トーン
						</button>
					</div>
					{fields.length === 0 ? (
						<div
							style={{ fontSize: 12, color: '#666', padding: 8 }}>
							入力項目は未設定です
						</div>
					) : (
						<div style={{ border: '1px solid #ddd', marginTop: 6 }}>
							<DragDropContext onDragEnd={onDragEnd}>
								<Droppable droppableId="fields">
									{(provided, snapshot) => (
										<div
											ref={provided.innerRef}
											{...provided.droppableProps}
											className={`dnd-list${
												snapshot.isDraggingOver
													? ' drag-over'
													: ''
											}`}>
											{fields.map((f, i) => (
												<Draggable
													key={`field-${f.key}-${i}`}
													draggableId={`field-${f.key}-${i}`}
													index={i}>
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
															}`}
															style={{
																padding: 6,
																borderTop:
																	i === 0
																		? 'none'
																		: '1px solid #eee',
															}}>
															<div
																style={{
																	display:
																		'grid',
																	gridTemplateColumns:
																		'18px minmax(120px, 1fr) minmax(140px, 1fr) 130px 1fr 60px',
																	gap: 6,
																	alignItems:
																		'center',
																}}>
																<span
																	{...dragProvided.dragHandleProps}
																	className="dnd-handle"
																	title="ドラッグして移動"
																	aria-label="ドラッグハンドル"
																	style={{
																		userSelect:
																			'none',
																	}}>
																	≡
																</span>
																<input
																	value={
																		f.key
																	}
																	onChange={(
																		e
																	) =>
																		updateField(
																			i,
																			{
																				key: e
																					.target
																					.value,
																			}
																		)
																	}
																	onBlur={() =>
																		updateField(
																			i,
																			{},
																			{
																				sanitizeKeyOnly:
																					true,
																			}
																		)
																	}
																	placeholder="key (a-z0-9_-)"
																	title="キー（英数字・ハイフン・アンダースコア）"
																/>
																<input
																	value={
																		f.label
																	}
																	onChange={(
																		e
																	) =>
																		updateField(
																			i,
																			{
																				label: e
																					.target
																					.value,
																			}
																		)
																	}
																	placeholder="ラベル"
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
																			{
																				input_type:
																					e
																						.target
																						.value as Field['input_type'],
																			}
																		)
																	}>
																	<option value="text">
																		text
																	</option>
																	<option value="textarea">
																		textarea
																	</option>
																	<option value="date">
																		date
																	</option>
																	<option value="select">
																		select
																	</option>
																</select>
																{f.input_type ===
																'select' ? (
																	<input
																		value={(
																			f.options ||
																			[]
																		).join(
																			', '
																		)}
																		onChange={(
																			e
																		) =>
																			updateField(
																				i,
																				{
																					options:
																						e.target.value
																							.split(
																								','
																							)
																							.map(
																								(
																									s
																								) =>
																									s.trim()
																							)
																							.filter(
																								(
																									s
																								) =>
																									!!s
																							),
																				}
																			)
																		}
																		placeholder="選択肢（カンマ区切り）"
																	/>
																) : (
																	<div
																		style={{
																			color: '#999',
																			fontSize: 12,
																		}}>
																		{f.input_type ===
																		'textarea'
																			? '複数行入力'
																			: f.input_type ===
																			  'date'
																			? '日付入力'
																			: '単一行入力'}
																	</div>
																)}
																<button
																	onClick={() =>
																		removeFieldRow(
																			i
																		)
																	}
																	style={{
																		fontSize: 12,
																		color: '#a00',
																	}}
																	title="削除">
																	削除
																</button>
															</div>
														</div>
													)}
												</Draggable>
											))}
											{provided.placeholder}
										</div>
									)}
								</Droppable>
							</DragDropContext>
						</div>
					)}
				</div>

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
														(
															{
																id: widgetId,
																uid,
															},
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
																	key={uid}
																	draggableId={
																		uid
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
																			}`}
																			style={{
																				padding: 8,
																				borderBottom:
																					'1px solid #eee',
																			}}>
																			<span
																				{...dragProvided.dragHandleProps}
																				className="dnd-handle"
																				title="ドラッグして移動"
																				aria-label="ドラッグハンドル"
																				style={{
																					marginRight: 8,
																				}}>
																				≡
																			</span>
																			<div
																				className="dnd-item-main"
																				style={{
																					display:
																						'grid',
																					gap: 4,
																				}}>
																				<div
																					style={{
																						display:
																							'flex',
																						gap: 8,
																						alignItems:
																							'center',
																					}}>
																					<strong>
																						{widget
																							? widget.name
																							: widgetId}
																					</strong>
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
																					<div
																						style={{
																							flex: 1,
																						}}
																					/>
																					<button
																						onClick={() =>
																							removeWidget(
																								uid
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

																				{widgetId ===
																					'scrape' && (
																					<ScrapeWidget
																						url={
																							scrapeMap[
																								uid
																							]
																								?.url ||
																							''
																						}
																						selector={
																							scrapeMap[
																								uid
																							]
																								?.selector ||
																							'body'
																						}
																						mode={
																							(scrapeMap[
																								uid
																							]
																								?.mode as ScrapeState['mode']) ||
																							'text'
																						}
																						timeoutMs={
																							scrapeMap[
																								uid
																							]
																								?.timeoutMs ??
																							10000
																						}
																						headless={
																							scrapeMap[
																								uid
																							]
																								?.headless ??
																							true
																						}
																						width={
																							scrapeMap[
																								uid
																							]
																								?.width ??
																							1200
																						}
																						height={
																							scrapeMap[
																								uid
																							]
																								?.height ??
																							800
																						}
																						apiBase={
																							API_BASE
																						}
																						onChange={(
																							patch: Partial<ScrapeState>
																						) =>
																							setScrapeMap(
																								(
																									prev
																								) => ({
																									...prev,
																									[uid]: {
																										url:
																											prev[
																												uid
																											]
																												?.url ||
																											'',
																										selector:
																											prev[
																												uid
																											]
																												?.selector ||
																											'body',
																										mode:
																											(prev[
																												uid
																											]
																												?.mode as ScrapeState['mode']) ||
																											'text',
																										timeoutMs:
																											prev[
																												uid
																											]
																												?.timeoutMs ??
																											10000,
																										headless:
																											prev[
																												uid
																											]
																												?.headless ??
																											true,
																										width:
																											prev[
																												uid
																											]
																												?.width ??
																											1200,
																										height:
																											prev[
																												uid
																											]
																												?.height ??
																											800,
																										...patch,
																									},
																								})
																							)
																						}
																					/>
																				)}

																				{widgetId ===
																					'x' && (
																					<XWidget
																						apiBase={
																							API_BASE
																						}
																						state={{
																							url: xMap[
																								uid
																							]
																								?.url,
																							mode:
																								(xMap[
																									uid
																								]
																									?.mode as XPreviewMode) ||
																								'thread',
																							maxPosts:
																								getMaxPosts(
																									xMap[
																										uid
																									]
																								),
																							rawText:
																								xMap[
																									uid
																								]
																									?.rawText ||
																								'',
																						}}
																						onChange={(
																							patch: Partial<XWidgetState>
																						) =>
																							setXMap(
																								(
																									prev
																								) => ({
																									...prev,
																									[uid]: {
																										url: prev[
																											uid
																										]
																											?.url,
																										mode:
																											(prev[
																												uid
																											]
																												?.mode as XPreviewMode) ||
																											'thread',
																										maxPosts:
																											getMaxPosts(
																												prev[
																													uid
																												]
																											),
																										rawText:
																											prev[
																												uid
																											]
																												?.rawText ||
																											'',
																										...patch,
																									},
																								})
																							)
																						}
																					/>
																				)}
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
									onChange={(e) => addWidget(e.target.value)}
									style={{ minWidth: 260 }}>
									<option value="">
										追加するウィジェットを選択
									</option>
									{availableWidgets.map((w) => (
										<option key={w.id} value={w.id}>
											{w.name} — {w.description}
										</option>
									))}
								</select>
								{availableWidgets.length === 0 && (
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
							{proposing
								? '提案を作成中…'
								: 'ウィジェットに基づき提案'}
						</button>
					</div>
					<textarea
						placeholder={
							'{{base}}\n---\n{{bullets}}\n---\n任意の変数: {{title}}, {{style}}, {{length}}, {{highlights}}, {{url_context}} など'
						}
						value={promptText}
						onChange={(e) => setPromptText(e.target.value)}
						rows={10}
						style={{ width: '100%', marginTop: 6 }}
					/>
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
						{previewSummary}
					</pre>
				</div>
			</div>
		</div>
	)
}
