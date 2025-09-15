'use client'

import { PropsWithChildren, Ref, useEffect, useMemo, useRef } from 'react'
import { useState, useId } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

type Props = PropsWithChildren<{
	title: string
	count?: number
	defaultOpen?: boolean
	contentRef?: Ref<HTMLDivElement>
	previewText?: string
	previewLines?: number
	previewTail?: boolean
	previewAsMarkdown?: boolean
	contentAsMarkdown?: boolean
	contentHeight?: number
	previewHeight?: number
}>

export default function Collapsible({
	title,
	count,
	defaultOpen = false,
	contentRef,
	previewText,
	previewLines = 3,
	previewTail = false,
	previewAsMarkdown = false,
	contentAsMarkdown = false,
	contentHeight,
	previewHeight,
	children,
}: Props) {
	const [open, setOpen] = useState<boolean>(defaultOpen)
	const btnId = useId()
	const countLabel = useMemo(
		() => (typeof count === 'number' ? `${count} 文字` : undefined),
		[count]
	)

	// 内部参照と外部参照の両方にアサイン
	const innerRef = useRef<HTMLDivElement | null>(null)
	const setRefs = (el: HTMLDivElement | null) => {
		innerRef.current = el
		if (typeof contentRef === 'function') contentRef(el)
		else if (contentRef && typeof contentRef === 'object') {
			;(
				contentRef as React.MutableRefObject<HTMLDivElement | null>
			).current = el
		}
	}

	// 展開時に末尾へスクロール（ログや長文に最適）
	useEffect(() => {
		if (!open || !innerRef.current) return
		try {
			innerRef.current.scrollTop = innerRef.current.scrollHeight
		} catch {}
	}, [open])
	return (
		<div className="collapsible-wrapper">
			<div
				role="button"
				id={btnId}
				onClick={() => setOpen((v) => !v)}
				className="collapsible-header">
				<div className="collapsible-title">
					<span className="text-xs">
						{open ? '▼' : '▶︎'} {title}
					</span>
				</div>
				{countLabel && (
					<div className="collapsible-count">
						{countLabel}
					</div>
				)}
			</div>
			{!open && previewText && previewText.trim() && (
				<div
					className="collapsible-preview"
					style={{
						display: '-webkit-box',
						WebkitLineClamp: previewLines,
						WebkitBoxOrient:
							'vertical' as React.CSSProperties['WebkitBoxOrient'],
						height:
							typeof previewHeight === 'number'
								? previewHeight
								: undefined,
					}}>
					{(() => {
						const text = previewText.trimEnd()
						const lines = text.split(/\r?\n/)
						const sliced = previewTail
							? lines.slice(
									Math.max(0, lines.length - previewLines)
							  )
							: lines.slice(0, previewLines)
						const display = sliced.join('\n')
						return previewAsMarkdown ? (
							<ReactMarkdown remarkPlugins={[remarkGfm]}>
								{display}
							</ReactMarkdown>
						) : (
							display
						)
					})()}
				</div>
			)}
			{open && (
				<div
					ref={setRefs}
					className="collapsible-content-expanded"
					style={{
						height:
							typeof contentHeight === 'number'
								? contentHeight
								: 240,
					}}>
					{contentAsMarkdown ? (
						<ReactMarkdown remarkPlugins={[remarkGfm]}>
							{String(children as string | number | undefined)}
						</ReactMarkdown>
					) : (
						children
					)}
				</div>
			)}
		</div>
	)
}
