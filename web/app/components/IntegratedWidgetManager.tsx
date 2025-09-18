'use client'

import React, { useState, useEffect } from 'react'
import PropertiesWidget from './PropertiesWidget'
import KindleHighlightWidget from './KindleHighlightWidget'
import PastPostsWidget from './PastPostsWidget'
import GenerationHistoryWidget from './GenerationHistoryWidget'
import EpubWidget from './EpubWidget'
import ScrapeWidget from './ScrapeWidget'

type WidgetType = {
	id: string
	name: string
	description: string
}

type TemplateField = {
	key: string
	label: string
	input_type: 'text' | 'textarea'
}

type TemplateDef = {
	name: string
	fields: TemplateField[]
	widgets?: string[]
} | null

type Book = { title: string; author?: string }
type Highlight = { id: string; text: string; asin?: string | null }
type SavedPost = { filename: string; title: string }

type IntegratedWidgetManagerProps = {
	articleTplDef: TemplateDef
	articleTplFields: Record<string, string>
	onFieldChange: (key: string, value: string) => void
	urlCtx: string
	onChangeUrlCtx: (v: string) => void

	// Kindle widget props
	obsBooks: Book[]
	bookFilter: string
	selectedBook: string
	highlights: Highlight[]
	obsidianError: string
	onBookFilterChange: (filter: string) => void
	onBookSelect: (book: string) => void

	// Past posts widget props
	savedPosts: SavedPost[]
	selectedPost: string
	onPostSelect: (filename: string) => void

	// Generation callbacks
	onGenerationComplete?: (
		title: string,
		content: string,
		reasoning: string
	) => void

	// Scrape widget (optional lift-state)
	scrapeCfg?: {
		url: string
		selector: string
		mode: 'text' | 'screenshot' | 'both'
		timeoutMs: number
		headless: boolean
		width: number
		height: number
	}
	onChangeScrapeCfg?: (
		next: Partial<{
			url: string
			selector: string
			mode: 'text' | 'screenshot' | 'both'
			timeoutMs: number
			headless: boolean
			width: number
			height: number
		}>
	) => void
}

export default function IntegratedWidgetManager(
	props: IntegratedWidgetManagerProps
) {
	const [selectedWidgets, setSelectedWidgets] = useState<string[]>([])
	const [scrapeCfgLocal, setScrapeCfgLocal] = useState({
		url: '',
		selector: '',
		mode: 'text' as 'text' | 'screenshot' | 'both',
		timeoutMs: 10000,
		headless: true,
		width: 1200,
		height: 2000,
	})

	// 実際に使う設定は props 優先、なければローカル
	const scrapeCfg = props.scrapeCfg ?? scrapeCfgLocal
	const updateScrapeCfg =
		props.onChangeScrapeCfg ??
		((next: Partial<typeof scrapeCfgLocal>) =>
			setScrapeCfgLocal((prev) => ({ ...prev, ...next })))

	useEffect(() => {
		// Sync selected widgets with template definition
		if (props.articleTplDef?.widgets) {
			setSelectedWidgets(props.articleTplDef.widgets)
		} else {
			setSelectedWidgets([])
		}
	}, [props.articleTplDef])

	const renderWidget = (widgetId: string) => {
		switch (widgetId) {
			case 'properties':
				return (
					<PropertiesWidget
						fields={props.articleTplDef?.fields || []}
						values={props.articleTplFields}
						onFieldChange={props.onFieldChange}
					/>
				)

			case 'url_context':
				return (
					<div className="component-container">
						<strong>URL コンテキスト</strong>
						<div className="mt-4 grid gap-2">
							<div className="text-xs text-gray-600">
								指定したURLの内容を取得して記事作成の参考にします
							</div>
							<div className="flex gap-2">
								<input
									placeholder="https://example.com/...（未指定可）"
									value={props.urlCtx}
									onChange={(e) =>
										props.onChangeUrlCtx(e.target.value)
									}
									className="flex-1 p-2 border rounded text-sm"
								/>
								{props.urlCtx && (
									<button
										onClick={() => props.onChangeUrlCtx('')}
										className="px-2 py-1 text-xs bg-gray-500 text-white rounded">
										クリア
									</button>
								)}
							</div>
						</div>
					</div>
				)

			case 'kindle':
				return (
					<KindleHighlightWidget
						books={props.obsBooks}
						bookFilter={props.bookFilter}
						selectedBook={props.selectedBook}
						highlights={props.highlights}
						obsidianError={props.obsidianError}
						onBookFilterChange={props.onBookFilterChange}
						onBookSelect={props.onBookSelect}
					/>
				)

			case 'past_posts':
				return (
					<PastPostsWidget
						savedPosts={props.savedPosts}
						selectedPost={props.selectedPost}
						onPostSelect={props.onPostSelect}
					/>
				)

			case 'generation_history':
				return (
					<GenerationHistoryWidget
						onLoadHistory={(history) => {
							// Load historical generation settings
							if (props.onGenerationComplete) {
								props.onGenerationComplete(
									history.title,
									history.generated_content,
									history.reasoning
								)
							}
						}}
					/>
				)

			case 'epub':
				return (
					<EpubWidget
						onResultChange={(result) => {
							// EPUBの検索結果をプロパティに設定
							if (props.onFieldChange) {
								props.onFieldChange('epub_context', result)
							}
						}}
						isEnabled={true}
					/>
				)

			case 'scrape':
				return (
					<ScrapeWidget
						url={scrapeCfg.url}
						selector={scrapeCfg.selector}
						mode={scrapeCfg.mode}
						timeoutMs={scrapeCfg.timeoutMs}
						headless={scrapeCfg.headless}
						width={scrapeCfg.width}
						height={scrapeCfg.height}
						onChange={updateScrapeCfg}
					/>
				)

			default:
				return (
					<div className="component-container">
						<strong>未知のウィジェット: {widgetId}</strong>
					</div>
				)
		}
	}

	return (
		<div>
			<div className="flex justify-between items-center mb-4">
				<h3 className="text-lg font-medium">ウィジェット</h3>
			</div>

			{selectedWidgets.length === 0 ? (
				<div className="component-container">
					<div className="text-sm text-gray-500">
						このテンプレートにウィジェットは定義されていません。
					</div>
				</div>
			) : (
				<div className="grid gap-4">
					{selectedWidgets.map((widgetId) => (
						<div key={widgetId}>{renderWidget(widgetId)}</div>
					))}
				</div>
			)}
		</div>
	)
}
