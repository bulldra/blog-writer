'use client'

import { useCallback, useRef, useState } from 'react'
import { type TodoItem } from '../components/TodoManager'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface UseStreamingGeneratorProps {
	articleTpl: string
	articleTplPrompt: string
	articleTplDef: {
		fields?: Array<{ key: string; label: string }>
		widgets?: string[]
	} | null
	articleTplFields: Record<string, string>
	urlCtx: string
	plan: string
	todos: TodoItem[]
	highlights: Array<{ text: string; asin?: string | null }>
	selectedPostContent: string
	bulletInput: string
	bulletTitle: string
	bulletStyle: string
	bulletLength: string
}

export function useStreamingGenerator({
	articleTpl,
	articleTplPrompt,
	articleTplDef,
	articleTplFields,
	urlCtx,
	plan,
	todos,
	highlights,
	selectedPostContent,
	bulletInput,
	bulletTitle,
	bulletStyle,
	bulletLength,
}: UseStreamingGeneratorProps) {
	const [isStreaming, setIsStreaming] = useState(false)
	const [streamCtl, setStreamCtl] = useState<AbortController | null>(null)
	const [draft, setDraft] = useState('')
	const [reasoning, setReasoning] = useState('')
	const [promptPreview, setPromptPreview] = useState('')

	const inReasoningRef = useRef(false)
	const sawOutputMarkerRef = useRef(false)

	const buildPropertiesAppend = useCallback(() => {
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
	}, [articleTplDef, articleTplFields])

	const buildTodosAppend = useCallback(() => {
		if (!todos.length) return ''
		const items = todos.map((t) => `- [${t.done ? 'x' : ' '}] ${t.text}`)
		return ['# TODO', ...items].join('\n')
	}, [todos])

	const buildPlanAppend = useCallback(() => {
		const p = plan.trim()
		if (!p) return ''
		return ['# PLAN', p].join('\n')
	}, [plan])

	const generateFromBulletsStream = useCallback(async () => {
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
			// Prompt preview generation
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

			// Actual streaming generation
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
	}, [
		isStreaming,
		bulletInput,
		articleTplPrompt,
		buildPropertiesAppend,
		buildTodosAppend,
		buildPlanAppend,
		articleTplDef,
		articleTplFields,
		urlCtx,
		highlights,
		bulletTitle,
		bulletStyle,
		bulletLength,
		articleTpl,
		selectedPostContent,
	])

	const generateFromTodosStream = useCallback(async () => {
		if (isStreaming) return
		const hasTodos = todos.some((t) => t.text.trim().length > 0)
		const hasPlan = plan.trim().length > 0
		if (!hasTodos && !hasPlan) {
			const ok = window.confirm('TODO/PLAN が空です。続行しますか？')
			if (!ok) return
		}
		return generateFromBulletsStream()
	}, [isStreaming, todos, plan, generateFromBulletsStream])

	const stopStreaming = useCallback(() => {
		streamCtl?.abort()
	}, [streamCtl])

	return {
		isStreaming,
		draft,
		reasoning,
		promptPreview,
		setDraft,
		generateFromBulletsStream,
		generateFromTodosStream,
		stopStreaming,
		buildPropertiesAppend,
		buildTodosAppend,
		buildPlanAppend,
	}
}