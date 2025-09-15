'use client'

import React from 'react'

const HIGHLIGHT_PREVIEW_LIMIT = 200

type Book = { title: string; author?: string }
type Highlight = { id: string; text: string; asin?: string | null }

interface KindleHighlightWidgetProps {
	books: Book[]
	bookFilter: string
	selectedBook: string
	highlights: Highlight[]
	obsidianError: string
	onBookFilterChange: (filter: string) => void
	onBookSelect: (book: string) => void
}

export default function KindleHighlightWidget({
	books,
	bookFilter,
	selectedBook,
	highlights,
	obsidianError,
	onBookFilterChange,
	onBookSelect,
}: KindleHighlightWidgetProps) {
	const visibleHighlights = highlights.slice(0, HIGHLIGHT_PREVIEW_LIMIT)

	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid var(--border-color)',
				background: 'var(--bg-secondary)',
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
						onChange={(e) => onBookFilterChange(e.target.value)}
						style={{ flex: 1 }}
					/>
					<select
						value={selectedBook}
						onChange={(e) => onBookSelect(e.target.value)}
						style={{ flex: 1 }}>
						<option value="">（選択しない）</option>
						{books
							.filter((b) =>
								bookFilter
									? b.title?.includes(bookFilter) ||
									  b.author?.includes(bookFilter)
									: true
							)
							.map((b) => (
								<option key={b.title} value={b.title}>
									{b.title}
									{b.author ? ` / ${b.author}` : ''}
								</option>
							))}
					</select>
					<a href="/obsidian" style={{ textDecoration: 'none' }}>
						📚 Obsidian
					</a>
				</div>
				{obsidianError && (
					<div style={{ color: '#a00', fontSize: 12 }}>
						{obsidianError}
					</div>
				)}
				<div style={{ fontSize: 12, color: 'var(--text-color)' }}>
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
						border: '1px solid var(--border-color)',
						padding: 6,
						background: 'var(--bg-color)',
					}}>
					<ul
						style={{
							margin: 0,
							padding: 0,
							listStyle: 'none',
						}}>
						{visibleHighlights.map((h) => (
							<li key={h.id} style={{ padding: '4px 0' }}>
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
	)
}