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
		<div className="component-container">
			<strong>Kindle ハイライト（任意）</strong>
			<p className="text-sm text-gray-600 mt-1 mb-4">
				書籍を選択すると、その書籍のすべてのハイライトが記事作成の参考として使用されます。
			</p>
			<div className="grid-gap-6 mt-6">
				<div className="flex-row">
					<input
						placeholder="書籍名フィルタ"
						value={bookFilter}
						onChange={(e) => onBookFilterChange(e.target.value)}
						className="flex-1"
					/>
					<select
						value={selectedBook}
						onChange={(e) => onBookSelect(e.target.value)}
						className="flex-1">
						<option value="">（書籍を選択してすべてのハイライトを使用）</option>
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
					<a href="/settings" style={{ textDecoration: 'none' }}>
						⚙️ 設定
					</a>
				</div>
				{obsidianError && (
					<div className="kindle-error">
						{obsidianError}
					</div>
				)}
				<div className="kindle-preview-info">
					{selectedBook ? (
						<>
							<strong>「{selectedBook}」の全ハイライト({highlights.length}件)を記事生成に使用します。</strong>
							<br />
							プレビュー表示は最大 {HIGHLIGHT_PREVIEW_LIMIT} 件までですが、
							記事生成時は選択した書籍のすべてのハイライトが参考にされます。
						</>
					) : (
						'書籍を選択すると、その書籍のすべてのハイライトが記事生成の参考に使用されます。'
					)}
					{highlights.some((h) => !h.asin) && (
						<span className="kindle-asin-warning">
							<br />
							一部のハイライトに ASIN
							がありません。引用記法に ASIN
							が付与されない場合があります。
						</span>
					)}
				</div>
				<div className="kindle-highlights-container">
					<ul className="kindle-highlights-list">
						{visibleHighlights.map((h) => (
							<li key={h.id} className="kindle-highlight-item">
								<span className="kindle-highlight-text">
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