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
		<div
			style={{
				marginTop: 8,
				border: '1px dashed var(--border-color)',
				background: 'var(--bg-secondary)',
				borderRadius: 4,
			}}>
			<div
				role="button"
				id={btnId}
				onClick={() => setOpen((v) => !v)}
				style={{
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'space-between',
					gap: 8,
					padding: '8px 10px',
					cursor: 'pointer',
					background: 'var(--bg-color)',
					userSelect: 'none',
				}}>
				<div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
					<span style={{ fontSize: 12 }}>
						{open ? '▼' : '▶︎'} {title}
					</span>
				</div>
				{countLabel && (
					<div style={{ fontSize: 11, color: 'var(--text-color)' }}>
						{countLabel}
					</div>
				)}
			</div>
			{!open && previewText && previewText.trim() && (
				<div
					style={{
						padding: '6px 10px 8px 10px',
						color: 'var(--text-color)',
						fontSize: 12,
						fontFamily:
							'ui-monospace, SFMono-Regular, Menlo, monospace',
						background: 'var(--bg-color)',
						borderTop: '1px solid var(--border-color)',
						display: '-webkit-box',
						WebkitLineClamp: previewLines,
						WebkitBoxOrient:
							'vertical' as React.CSSProperties['WebkitBoxOrient'],
						overflow: 'hidden',
						whiteSpace: 'pre-wrap',
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
					style={{
						padding: 8,
						whiteSpace: 'pre-wrap',
						fontSize: 12,
						fontFamily:
							'ui-monospace, SFMono-Regular, Menlo, monospace',
						height:
							typeof contentHeight === 'number'
								? contentHeight
								: 240,
						overflow: 'auto',
						background: 'var(--bg-secondary)',
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
