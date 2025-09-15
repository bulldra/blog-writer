'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Collapsible from './components/Collapsible'
import ArticleTemplateSelector from './components/ArticleTemplateSelector'
import EditRequest from './components/EditRequest'
import TodoManager, { type TodoItem } from './components/TodoManager'
import PlanPanel from './components/PlanPanel'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const HIGHLIGHT_PREVIEW_LIMIT = 200

type TemplateField = {
	key: string
	label: string
	input_type: 'text' | 'textarea'
}

type TemplateDef = {
	name: string
	fields: TemplateField[]
	prompt_template: string
	widgets?: string[]
} | null

type TemplateListItem = { type: string; name: string }

type Book = { title: string; author?: string }
type Highlight = { id: string; text: string; asin?: string | null }
type SavedPost = { filename: string; title: string }

export default function Page() {
	const [mounted, setMounted] = useState(false)

	// 記事テンプレ
	const [articleTplList, setArticleTplList] = useState<TemplateListItem[]>([])
	const [articleTpl, setArticleTpl] = useState<string>('')
	const [articleTplDef, setArticleTplDef] = useState<TemplateDef>(null)
	const [articleTplFields, setArticleTplFields] = useState<
		Record<string, string>
	>({})
	const articleTplPrompt = useMemo(
		() => (articleTplDef ? articleTplDef.prompt_template || '' : ''),
		[articleTplDef]
	)

	// 追加コンテキスト（URL）
	const [urlCtx, setUrlCtx] = useState('')

	// プラン/TODO
	const [plan, setPlan] = useState('')
	const [todos, setTodos] = useState<TodoItem[]>([])

	// 生成/結果
	const [draft, setDraft] = useState('')
	const [promptPreview, setPromptPreview] = useState('')
	const [reasoning, setReasoning] = useState('')
	const [resultEditable, setResultEditable] = useState(false)
	const [showPreview, setShowPreview] = useState(true)
	const [commitWithGit, setCommitWithGit] = useState(false)

	// ストリーミング
	const [isStreaming, setIsStreaming] = useState(false)
	const [streamCtl, setStreamCtl] = useState<AbortController | null>(null)
	const inReasoningRef = useRef(false)
	const sawOutputMarkerRef = useRef(false)
	const previewRef = useRef<HTMLDivElement | null>(null)
	const textRef = useRef<HTMLTextAreaElement | null>(null)
	const reasoningRef = useRef<HTMLDivElement | null>(null)

	// 画像
	const [eyecatchUrl, setEyecatchUrl] = useState('')
	const [eyecatchTheme, setEyecatchTheme] = useState<'light' | 'dark'>(
		'light'
	)

	// 編集依頼
	const [editInstruction, setEditInstruction] = useState('')
	const [isEditing, setIsEditing] = useState(false)

	// 箇条書き入力（UIは省略・空可）
	const [bulletInput] = useState('')
	const [bulletTitle] = useState('')
	const [bulletStyle] = useState('')
	const [bulletLength] = useState('')

	// Kindle ウィジェット
	const [obsBooks, setObsBooks] = useState<Book[]>([])
	const [bookFilter, setBookFilter] = useState('')
	const [selectedBook, setSelectedBook] = useState('')
	const [highlights, setHighlights] = useState<Highlight[]>([])
	const [obsidianError, setObsidianError] = useState('')

	// 過去記事ウィジェット
	const [savedPosts, setSavedPosts] = useState<SavedPost[]>([])
	const [selectedPost, setSelectedPost] = useState('')
	const [selectedPostContent, setSelectedPostContent] = useState('')

	// 初期ロード
	useEffect(() => {
		setMounted(true)
		;(async () => {
			try {
				const listRes = await fetch(`${API_BASE}/api/article-templates`)
				if (listRes.ok) {
					const list = (await listRes.json()) as TemplateListItem[]
					setArticleTplList(list)
					const saved = localStorage.getItem('articleTpl') || ''
					const first = saved || list[0]?.type || ''
					setArticleTpl(first)
					if (first) {
						const defRes = await fetch(
							`${API_BASE}/api/article-templates/${encodeURIComponent(
								first
							)}`
						)
						if (defRes.ok) {
							const def = await defRes.json()
							setArticleTplDef(def as TemplateDef)
							const initFields: Record<string, string> = {}
							;(def.fields || []).forEach((f: TemplateField) => {
								initFields[f.key] = ''
							})
							setArticleTplFields(initFields)
						}
					}
				}
			} catch {}

			try {
				const postsRes = await fetch(`${API_BASE}/api/drafts/posts`)
				if (postsRes.ok) setSavedPosts(await postsRes.json())
			} catch {}

			try {
				const booksRes = await fetch(`${API_BASE}/api/obsidian/books`)
				if (booksRes.ok) setObsBooks(await booksRes.json())
			} catch {
				setObsidianError('Obsidian 書籍一覧の取得に失敗しました')
			}

			try {
				const re = localStorage.getItem('resultEditable')
				if (re != null) setResultEditable(re === 'true')
				const rawTodos = localStorage.getItem('genTodos')
				if (rawTodos) setTodos(JSON.parse(rawTodos) as TodoItem[])
				const pl = localStorage.getItem('genPlan')
				if (pl) setPlan(pl)
			} catch {}
		})()
	}, [])

	// 設定の永続化
	useEffect(() => {
		if (!mounted) return
		try {
			localStorage.setItem('resultEditable', String(resultEditable))
		} catch {}
	}, [mounted, resultEditable])

	useEffect(() => {
		if (!mounted) return
		try {
			localStorage.setItem('genTodos', JSON.stringify(todos))
		} catch {}
	}, [mounted, todos])

	useEffect(() => {
		if (!mounted) return
		try {
			localStorage.setItem('genPlan', plan)
		} catch {}
	}, [mounted, plan])

	const loadHighlights = async (book: string) => {
		setSelectedBook(book)
		setHighlights([])
		if (!book) return
		try {
			const res = await fetch(
				`${API_BASE}/api/obsidian/highlights?book=${encodeURIComponent(
					book
				)}`
			)
			if (res.ok) setHighlights(await res.json())
		} catch {}
	}

	const visibleHighlights = useMemo(
		() => highlights.slice(0, HIGHLIGHT_PREVIEW_LIMIT),
		[highlights]
	)

	// 記事テンプレのフィールド（プロパティ）を Markdown として整形
	const buildPropertiesAppend = () => {
		const fields = articleTplDef?.fields || []
		const lines: string[] = []
		for (const f of fields) {
			const v = (articleTplFields[f.key] || '').trim()
			if (!v) continue
			const label = f.label || f.key
			lines.push(`- ${label}: ${v}`)
		}
		if (!lines.length) return ''
		return ['# プロパティ', ...lines].join('\n')
	}

	const buildTodosAppend = () => {
		if (!todos.length) return ''
		const items = todos.map((t) => `- [${t.done ? 'x' : ' '}] ${t.text}`)
		return ['# TODO', ...items].join('\n')
	}

	const buildPlanAppend = () => {
		const p = plan.trim()
		if (!p) return ''
		return ['# PLAN', p].join('\n')
	}

	const generateFromBulletsStream = async () => {
		if (isStreaming) return
		const bullets = bulletInput
			.split(/\r?\n/)
			.map((s) => s.replace(/^[\-−•\s]+/, '').trim())
			.filter((s) => s.length > 0)
		const ctl = new AbortController()
		setStreamCtl(ctl)
		setIsStreaming(true)
		setDraft('')
		setReasoning('')
		inReasoningRef.current = false
		sawOutputMarkerRef.current = false
		try {
			try {
				const articlePrompt = articleTplPrompt || ''
				const basePrompt = (articlePrompt || '').trim()
				const propsSection = buildPropertiesAppend()
				const todosSection = buildTodosAppend()
				const planSection = buildPlanAppend()
				const withProps = propsSection
					? `${basePrompt}\n\n${propsSection}`
					: basePrompt
				const withTodos = todosSection
					? `${withProps}\n\n${todosSection}`
					: withProps
				const templateToSend = planSection
					? `${withTodos}\n\n${planSection}`
					: withTodos
				const useUrlCtx =
					articleTplDef?.widgets?.includes('url_context')
				const urlToSend = useUrlCtx
					? articleTplFields['url']?.trim() || urlCtx || ''
					: ''
				const useHighlights = articleTplDef?.widgets?.includes('kindle')
				const highlightsToSend = useHighlights
					? highlights.map((h) => h.text)
					: []
				const p = await fetch(
					`${API_BASE}/api/ai/from-bullets/prompt`,
					{
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({
							bullets,
							title: bulletTitle || undefined,
							style: bulletStyle || undefined,
							length: bulletLength || undefined,
							url_context: urlToSend || undefined,
							highlights: highlightsToSend,
							highlights_asin: useHighlights
								? highlights.map((h) => h.asin ?? null)
								: [],
							prompt_template: templateToSend || undefined,
							article_type: articleTpl || undefined,
							extra_context: articleTplFields,
						}),
					}
				)
				if (p.ok) {
					const json = await p.json()
					setPromptPreview(json.prompt || '')
				}
			} catch {}

			const articlePrompt = articleTplPrompt || ''
			const basePrompt = (articlePrompt || '').trim()
			const propsSection = buildPropertiesAppend()
			const todosSection = buildTodosAppend()
			const planSection = buildPlanAppend()
			const withProps = propsSection
				? `${basePrompt}\n\n${propsSection}`
				: basePrompt
			const withTodos = todosSection
				? `${withProps}\n\n${todosSection}`
				: withProps
			const templateToSend = planSection
				? `${withTodos}\n\n${planSection}`
				: withTodos
			const usePastPosts = articleTplDef?.widgets?.includes('past_posts')
			const extraHighlights = usePastPosts
				? selectedPostContent
					? [selectedPostContent.slice(0, 4000)]
					: []
				: []
			const extraAsins = extraHighlights.map(() => null)
			const useUrlCtx = articleTplDef?.widgets?.includes('url_context')
			const urlToSend = useUrlCtx
				? articleTplFields['url']?.trim() || urlCtx || ''
				: ''
			const useHighlights = articleTplDef?.widgets?.includes('kindle')
			const bookHighlights = useHighlights
				? highlights.map((h) => h.text)
				: []
			const bookAsins = useHighlights
				? highlights.map((h) => h.asin ?? null)
				: []
			const res = await fetch(`${API_BASE}/api/ai/from-bullets/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					bullets,
					title: bulletTitle || undefined,
					style: bulletStyle || undefined,
					length: bulletLength || undefined,
					url_context: urlToSend || undefined,
					highlights: [...bookHighlights, ...extraHighlights],
					highlights_asin: [...bookAsins, ...extraAsins],
					prompt_template: templateToSend || undefined,
					article_type: articleTpl || undefined,
					extra_context: articleTplFields,
				}),
				signal: ctl.signal,
				cache: 'no-store',
			})
			const reader = res.body?.getReader()
			if (!reader) return
			const decoder = new TextDecoder()
			while (true) {
				const { value, done } = await reader.read()
				if (done) break
				const chunkText = decoder.decode(value, { stream: true })
				if (!sawOutputMarkerRef.current) {
					if (
						!inReasoningRef.current &&
						chunkText.includes('[Reasoning]')
					) {
						inReasoningRef.current = true
					}
					if (inReasoningRef.current) {
						const marker = '[生成結果]'
						const idx = chunkText.indexOf(marker)
						if (idx >= 0) {
							const pre = chunkText.slice(0, idx)
							const post = chunkText.slice(idx + marker.length)
							setReasoning((prev) => prev + pre)
							sawOutputMarkerRef.current = true
							inReasoningRef.current = false
							setDraft((prev) => prev + post)
						} else {
							setReasoning((prev) => prev + chunkText)
						}
					} else {
						setDraft((prev) => prev + chunkText)
					}
				} else {
					setDraft((prev) => prev + chunkText)
				}
			}
		} catch {
			// ignore
		} finally {
			setIsStreaming(false)
			setStreamCtl(null)
		}
	}

	const generateFromTodosStream = async () => {
		if (isStreaming) return
		const hasTodos = todos.some((t) => t.text.trim().length > 0)
		const hasPlan = plan.trim().length > 0
		if (!hasTodos && !hasPlan) {
			const ok = window.confirm('TODO/PLAN が空です。続行しますか？')
			if (!ok) return
		}
		return generateFromBulletsStream()
	}

	const stopStreaming = () => {
		streamCtl?.abort()
	}

	// 自動スクロール
	useEffect(() => {
		if (!isStreaming) return
		if (showPreview && previewRef.current) {
			requestAnimationFrame(() => {
				try {
					previewRef.current!.scrollTop =
						previewRef.current!.scrollHeight
				} catch {}
			})
		}
		if (resultEditable && textRef.current) {
			requestAnimationFrame(() => {
				try {
					textRef.current!.scrollTop = textRef.current!.scrollHeight
				} catch {}
			})
		}
		const r = reasoningRef.current
		if (r) {
			requestAnimationFrame(() => {
				try {
					r.scrollTop = r.scrollHeight
				} catch {}
			})
		}
	}, [draft, isStreaming, resultEditable, showPreview])

	const save = async () => {
		const body = draft.trim()
		if (!body) return alert('空の文書は保存できません')
		const res = await fetch(`${API_BASE}/api/drafts/save-markdown`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ content: body, git_commit: commitWithGit }),
		})
		if (res.ok) {
			const json = await res.json()
			alert(`保存しました\n${json.filename}`)
		} else {
			alert('保存に失敗しました')
		}
	}

	const generateEyecatch = async () => {
		try {
			const titleGuess = (draft.match(/^#\s*(.+)/m)?.[1] || '').trim()
			const res = await fetch(`${API_BASE}/api/images/eyecatch`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					title: titleGuess || bulletTitle || 'Blog Post',
					width: 1200,
					height: 630,
					theme: eyecatchTheme,
				}),
			})
			if (res.ok) {
				const json = await res.json()
				setEyecatchUrl(json.data_url || '')
			}
		} catch {}
	}

	const downloadEyecatchJpeg = async () => {
		try {
			if (!eyecatchUrl.startsWith('data:image/svg+xml')) return
			const svgText = atob(eyecatchUrl.split(',')[1] || '')
			const svg = new Blob([svgText], { type: 'image/svg+xml' })
			const url = URL.createObjectURL(svg)
			const img = new Image()
			await new Promise<void>((resolve, reject) => {
				img.onload = () => resolve()
				img.onerror = () => reject()
				img.src = url
			})
			const canvas = document.createElement('canvas')
			canvas.width = 1200
			canvas.height = 630
			const ctx = canvas.getContext('2d')
			if (!ctx) return
			ctx.fillStyle = '#fff'
			ctx.fillRect(0, 0, canvas.width, canvas.height)
			ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
			canvas.toBlob(
				(blob) => {
					if (!blob) return
					const a = document.createElement('a')
					a.href = URL.createObjectURL(blob)
					a.download =
						(draft.match(/^#\s*(.+)/m)?.[1] || 'eyecatch') + '.jpg'
					a.click()
				},
				'image/jpeg',
				0.92
			)
		} catch {}
	}

	const requestEdit = async () => {
		const content = draft.trim()
		const instruction = editInstruction.trim()
		if (!content || !instruction) return
		setIsEditing(true)
		setDraft('')
		try {
			const res = await fetch(`${API_BASE}/api/ai/edit/stream`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ content, instruction }),
			})
			const reader = res.body?.getReader()
			if (!reader) return
			const decoder = new TextDecoder()
			while (true) {
				const { value, done } = await reader.read()
				if (done) break
				const chunkText = decoder.decode(value, { stream: true })
				setDraft((prev) => prev + chunkText)
			}
		} finally {
			setIsEditing(false)
		}
	}

	const showKindleWidget = articleTplDef?.widgets?.includes('kindle')
	const showPastPostsWidget = articleTplDef?.widgets?.includes('past_posts')

	return (
		<div style={{ margin: '2rem auto', padding: '0 1rem' }}>
			<section style={{ display: 'grid', gap: 12 }}>
				<ArticleTemplateSelector
					articleTpl={articleTpl}
					articleTplList={articleTplList}
					onChangeArticleTpl={async (v) => {
						setArticleTpl(v)
						try {
							localStorage.setItem('articleTpl', v)
						} catch {}
						// def 取得
						try {
							const defRes = await fetch(
								`${API_BASE}/api/article-templates/${encodeURIComponent(
									v
								)}`
							)
							if (defRes.ok) {
								const def = (await defRes.json()) as TemplateDef
								setArticleTplDef(def)
								const initFields: Record<string, string> = {}
								;(def?.fields || []).forEach(
									(f) => (initFields[f.key] = '')
								)
								setArticleTplFields(initFields)
							}
						} catch {}
					}}
					articleTplDef={articleTplDef}
					articleTplFields={articleTplFields}
					onChangeField={(key, value) =>
						setArticleTplFields((prev) => ({
							...prev,
							[key]: value,
						}))
					}
					urlCtx={urlCtx}
					onChangeUrlCtx={setUrlCtx}
				/>

				{/* プランニング（AI が作成・実行で TODO 自動更新） */}
				<PlanPanel
					value={plan}
					onClear={() => setPlan('')}
					onGenerate={async () => {
						try {
							const articlePrompt = articleTplPrompt || ''
							const basePrompt = (articlePrompt || '').trim()
							const propsSection = buildPropertiesAppend()
							const todosSection = buildTodosAppend()
							const withProps = propsSection
								? `${basePrompt}\n\n${propsSection}`
								: basePrompt
							const withTodos = todosSection
								? `${withProps}\n\n${todosSection}`
								: withProps
							const planInstr = [
								'以下の情報をもとに、記事生成のための実行プランを作成してください。',
								'- 出力はMarkdownのみで、前置きや補足は書かない。',
								'- 箇条書き（3-10項目程度）と簡潔な章立て（H2/H3推奨）を含める。',
								'- 制約・優先順位・チェックリストがあれば併記する。',
							].join('\n')
							const prompt = `${planInstr}\n\n[指示]\n${withTodos}`
							const useUrlCtx =
								articleTplDef?.widgets?.includes('url_context')
							const urlToSend = useUrlCtx
								? articleTplFields['url']?.trim() ||
								  urlCtx ||
								  ''
								: ''
							const useHighlights =
								articleTplDef?.widgets?.includes('kindle')
							const highlightsToSend = useHighlights
								? highlights.map((h) => h.text)
								: []
							const res = await fetch(
								`${API_BASE}/api/ai/generate`,
								{
									method: 'POST',
									headers: {
										'Content-Type': 'application/json',
									},
									body: JSON.stringify({
										prompt,
										url_context: urlToSend || undefined,
										highlights: highlightsToSend,
									}),
								}
							)
							if (res.ok) {
								const json = await res.json()
								setPlan(String(json.text || ''))
							}
						} catch {}
					}}
					onExecute={async () => {
						try {
							const p = plan.trim()
							const propsSection = buildPropertiesAppend()
							const context = [propsSection, p]
								.filter(Boolean)
								.join('\n\n')
							const instr = [
								'あなたは編集アシスタントです。以下のPLANとプロパティを読み、',
								'ブログ記事生成に必要な具体的なTODOリストを作成・更新してください。',
								'- 出力はMarkdownのチェックボックスリストのみ (# TODO 見出し不要)。',
								'- フォーマット: "- [ ] 文言" または "- [x] 文言"。',
								'- 既存TODOがある場合は整合を取り、重複を統合し、足りない項目を補い、完了済を [x] に。',
								'- 項目は10件以内で簡潔に。',
							].join('\n')
							const prompt = `${instr}\n\n[CONTEXT]\n${context}\n\n[EXISTING TODO]\n${buildTodosAppend()}`
							const res = await fetch(
								`${API_BASE}/api/ai/generate`,
								{
									method: 'POST',
									headers: {
										'Content-Type': 'application/json',
									},
									body: JSON.stringify({ prompt }),
								}
							)
							if (res.ok) {
								const json = await res.json()
								const text = String(json.text || '')
								const lines = text
									.split(/\r?\n/)
									.map((s) => s.trim())
									.filter((s) => s)
								const items = lines
									.filter((s) => /^- \[( |x)\]/.test(s))
									.map((s) => {
										const done = /\[x\]/i.test(s)
										const tx = s.replace(
											/^- \[( |x)\]\s*/i,
											''
										)
										return {
											id: `${Date.now()}-${Math.random()
												.toString(36)
												.slice(2, 7)}`,
											text: tx,
											done,
										} as TodoItem
									})
									.slice(0, 10)
								if (items.length) setTodos(items)
							}
						} catch {}
					}}
				/>

				{/* TODO（Plan の下に自動生成・編集可能） */}
				<div
					style={{
						marginTop: 8,
						padding: 8,
						border: '1px solid #ddd',
						background: '#fff',
					}}>
					<strong>TODO</strong>
					<div style={{ marginTop: 6 }}>
						<TodoManager value={todos} onChange={setTodos} />
						<div
							style={{
								fontSize: 12,
								color: '#666',
								marginTop: 4,
							}}>
							生成時に TODO を # TODO
							セクションとしてプロンプトに付加します。完了にチェックすると打ち消し線になります。
						</div>
					</div>
				</div>

				<div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
					{!isStreaming ? (
						<>
							<button onClick={generateFromBulletsStream}>
								生成
							</button>
							<button
								onClick={generateFromTodosStream}
								title="TODO もPLANも空でも続行可能です">
								TODOで生成
							</button>
						</>
					) : (
						<button onClick={stopStreaming}>停止</button>
					)}
				</div>

				{/* kindle ハイライト（任意） */}
				{showKindleWidget && (
					<div
						style={{
							marginTop: 8,
							padding: 8,
							border: '1px solid #ddd',
							background: '#fff',
						}}>
						<strong>Kindle ハイライト（任意）</strong>
						<div style={{ display: 'grid', gap: 6, marginTop: 6 }}>
							<div
								style={{
									display: 'flex',
									gap: 6,
									alignItems: 'center',
								}}>
								<input
									placeholder="書籍名フィルタ"
									value={bookFilter}
									onChange={(e) =>
										setBookFilter(e.target.value)
									}
									style={{ flex: 1 }}
								/>
								<select
									value={selectedBook}
									onChange={(e) =>
										loadHighlights(e.target.value)
									}
									style={{ flex: 1 }}>
									<option value="">（選択しない）</option>
									{obsBooks
										.filter((b) =>
											bookFilter
												? b.title?.includes(
														bookFilter
												  ) ||
												  b.author?.includes(bookFilter)
												: true
										)
										.map((b) => (
											<option
												key={b.title}
												value={b.title}>
												{b.title}
												{b.author
													? ` / ${b.author}`
													: ''}
											</option>
										))}
								</select>
								<a
									href="/obsidian"
									style={{ textDecoration: 'none' }}>
									📚 Obsidian
								</a>
							</div>
							{obsidianError && (
								<div style={{ color: '#a00', fontSize: 12 }}>
									{obsidianError}
								</div>
							)}
							<div style={{ fontSize: 12, color: '#666' }}>
								プレビューは最大 {HIGHLIGHT_PREVIEW_LIMIT} 件。
								{highlights.some((h) => !h.asin) && (
									<span
										style={{
											color: '#a00',
											marginLeft: 8,
										}}>
										一部のハイライトに ASIN
										がありません。引用記法に ASIN
										が付与されない場合があります。
									</span>
								)}
							</div>
							<div
								style={{
									maxHeight: 220,
									overflow: 'auto',
									border: '1px solid #eee',
									padding: 6,
									background: '#fafafa',
								}}>
								<ul
									style={{
										margin: 0,
										padding: 0,
										listStyle: 'none',
									}}>
									{visibleHighlights.map((h) => (
										<li
											key={h.id}
											style={{ padding: '4px 0' }}>
											<span
												style={{
													whiteSpace: 'pre-wrap',
												}}>
												{h.text}
											</span>
										</li>
									))}
								</ul>
							</div>
						</div>
					</div>
				)}

				{/* 過去記事をコンテキストに含める（任意） */}
				{showPastPostsWidget && (
					<div
						style={{
							marginTop: 8,
							padding: 8,
							border: '1px solid #ddd',
							background: '#fff',
						}}>
						<strong>過去記事コンテキスト（任意）</strong>
						<div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
							<select
								value={selectedPost}
								onChange={async (e) => {
									const f = e.target.value
									setSelectedPost(f)
									setSelectedPostContent('')
									if (!f) return
									try {
										const res = await fetch(
											`${API_BASE}/api/drafts/posts/${encodeURIComponent(
												f
											)}`
										)
										if (res.ok) {
											const json = await res.json()
											setSelectedPostContent(
												String(json.content || '')
											)
										}
									} catch {}
								}}
								style={{ flex: 1 }}>
								<option value="">（選択しない）</option>
								{savedPosts.map((p) => (
									<option key={p.filename} value={p.filename}>
										{p.title}
									</option>
								))}
							</select>
							{selectedPost && (
								<span style={{ fontSize: 12, color: '#666' }}>
									本文先頭を一部（最大4000文字）参照に送信します
								</span>
							)}
						</div>
					</div>
				)}

				{/* prompt（折りたたみ） */}
				{promptPreview && (
					<Collapsible
						title="Prompt"
						count={promptPreview.length}
						previewText={promptPreview}
						previewLines={3}
						contentAsMarkdown
						contentHeight={240}>
						{promptPreview}
					</Collapsible>
				)}

				{/* Reasoning ログ（折りたたみ） */}
				{reasoning && (
					<Collapsible
						title="Reasoning"
						count={reasoning.length}
						contentRef={reasoningRef}
						previewText={reasoning}
						previewLines={3}
						previewTail
						contentAsMarkdown
						contentHeight={240}
						previewHeight={72}>
						{reasoning}
					</Collapsible>
				)}

				{/* 生成結果表示設定（単一プレビュー＋ソース折りたたみ） */}
				<div
					style={{
						marginTop: 8,
						padding: 8,
						border: '1px solid #ddd',
						background: '#f8f8f8',
						display: 'grid',
						gap: 8,
					}}>
					<div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
						<label
							style={{
								display: 'flex',
								alignItems: 'center',
								gap: 4,
							}}>
							<input
								type="checkbox"
								checked={resultEditable}
								onChange={(e) =>
									setResultEditable(e.target.checked)
								}
							/>
							<span style={{ fontSize: 12 }}>編集モード</span>
						</label>
						<label
							style={{
								display: 'flex',
								alignItems: 'center',
								gap: 4,
							}}>
							<input
								type="checkbox"
								checked={showPreview}
								onChange={(e) =>
									setShowPreview(e.target.checked)
								}
							/>
							<span style={{ fontSize: 12 }}>プレビュー表示</span>
						</label>
						<button
							onClick={() => {
								navigator.clipboard
									.writeText(draft)
									.catch(() => {})
							}}
							style={{ fontSize: 12 }}>
							コピー
						</button>
						<button onClick={save} style={{ fontSize: 12 }}>
							保存
						</button>
						<label
							style={{
								display: 'flex',
								alignItems: 'center',
								gap: 6,
							}}>
							<input
								type="checkbox"
								checked={commitWithGit}
								onChange={(e) =>
									setCommitWithGit(e.target.checked)
								}
							/>
							<span style={{ fontSize: 12 }}>Gitでコミット</span>
						</label>
						<a href="/drafts" style={{ textDecoration: 'none' }}>
							🗂️ 保存一覧
						</a>
					</div>
					{/* アイキャッチ最小UI */}
					<div
						style={{
							display: 'flex',
							gap: 8,
							alignItems: 'center',
						}}>
						<button
							onClick={generateEyecatch}
							style={{ fontSize: 12 }}>
							アイキャッチ生成
						</button>
						<select
							value={eyecatchTheme}
							onChange={(e) =>
								setEyecatchTheme(
									e.target.value as 'light' | 'dark'
								)
							}
							style={{ fontSize: 12 }}>
							<option value="light">light</option>
							<option value="dark">dark</option>
						</select>
						{eyecatchUrl && (
							<>
								<a
									href={eyecatchUrl}
									download={
										(draft.match(/^#\s*(.+)/m)?.[1] ||
											'eyecatch') + '.svg'
									}
									style={{ fontSize: 12 }}>
									SVGをダウンロード
								</a>
								<button
									onClick={downloadEyecatchJpeg}
									style={{ fontSize: 12 }}>
									JPEGでダウンロード
								</button>
							</>
						)}
					</div>
					{/* プレビュー（単一） */}
					{showPreview && (
						<div
							ref={previewRef}
							style={{
								fontSize: 14,
								lineHeight: 1.6,
								background: '#fff',
								border: '1px solid #eee',
								padding: 12,
								height: 360,
								overflowY: 'auto',
							}}>
							<ReactMarkdown remarkPlugins={[remarkGfm]}>
								{draft || ''}
							</ReactMarkdown>
						</div>
					)}

					{/* ソース（Markdown）を折りたたみで表示 */}
					<Collapsible
						title="ソース（Markdown）"
						previewText={draft}
						previewLines={3}
						contentHeight={260}>
						<textarea
							ref={textRef}
							value={draft}
							onChange={(e) => setDraft(e.target.value)}
							disabled={!resultEditable}
							style={{
								width: '100%',
								minHeight: 220,
								maxHeight: 440,
								overflow: 'scroll',
								fontSize: 14,
								lineHeight: 1.5,
								fontFamily:
									'ui-monospace, SFMono-Regular, Menlo, monospace',
								whiteSpace: 'pre-wrap',
							}}
						/>
					</Collapsible>
				</div>

				{/* 編集を依頼 */}
				<EditRequest
					instruction={editInstruction}
					isEditing={isEditing}
					onChange={setEditInstruction}
					onSubmit={requestEdit}
				/>
			</section>
		</div>
	)
}
