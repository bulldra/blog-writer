'use client'

import React, { useState, useEffect } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import WidgetManager from './WidgetManager'
import PropertiesWidget from './PropertiesWidget'
import KindleHighlightWidget from './KindleHighlightWidget'
import PastPostsWidget from './PastPostsWidget'
import GenerationHistoryWidget from './GenerationHistoryWidget'

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
	onGenerationComplete?: (title: string, content: string, reasoning: string) => void
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function IntegratedWidgetManager(props: IntegratedWidgetManagerProps) {
	const [availableWidgets, setAvailableWidgets] = useState<WidgetType[]>([])
	const [selectedWidgets, setSelectedWidgets] = useState<string[]>([])
	const [showWidgetManager, setShowWidgetManager] = useState(false)

	useEffect(() => {
		// Load available widgets
		const loadWidgets = async () => {
			try {
				const response = await fetch(`${API_BASE}/api/article-templates/widgets/available`)
				if (response.ok) {
					const data = await response.json()
					setAvailableWidgets(data.widgets || [])
				}
			} catch (error) {
				console.error('Failed to load widgets:', error)
			}
		}
		loadWidgets()
	}, [])

	useEffect(() => {
		// Sync selected widgets with template definition
		if (props.articleTplDef?.widgets) {
			setSelectedWidgets(props.articleTplDef.widgets)
		} else {
			setSelectedWidgets([])
		}
	}, [props.articleTplDef])

	const handleWidgetsChange = (widgets: string[]) => {
		setSelectedWidgets(widgets)
		// Here we would typically save the widget configuration to the template
		// For now, we'll just update the local state
	}

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
									onChange={(e) => props.onChangeUrlCtx(e.target.value)}
									className="flex-1 p-2 border rounded text-sm"
								/>
								{props.urlCtx && (
									<button
										onClick={() => props.onChangeUrlCtx('')}
										className="px-2 py-1 text-xs bg-gray-500 text-white rounded"
									>
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
			
			default:
				return (
					<div className="component-container">
						<strong>未知のウィジェット: {widgetId}</strong>
					</div>
				)
		}
	}

	const handleOnDragEnd = (result: DropResult) => {
		if (!result.destination) return

		const items = Array.from(selectedWidgets)
		const [reorderedItem] = items.splice(result.source.index, 1)
		items.splice(result.destination.index, 0, reorderedItem)

		handleWidgetsChange(items)
	}

	if (showWidgetManager) {
		return (
			<>
				<div className="flex justify-between items-center mb-4">
					<h3 className="text-lg font-medium">ウィジェット設定</h3>
					<button
						onClick={() => setShowWidgetManager(false)}
						className="px-3 py-1 bg-gray-500 text-white rounded text-sm"
					>
						設定を閉じる
					</button>
				</div>
				<WidgetManager
					availableWidgets={availableWidgets}
					selectedWidgets={selectedWidgets}
					onWidgetsChange={handleWidgetsChange}
				/>
			</>
		)
	}

	return (
		<div>
			<div className="flex justify-between items-center mb-4">
				<h3 className="text-lg font-medium">ウィジェット</h3>
				<button
					onClick={() => setShowWidgetManager(true)}
					className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
				>
					ウィジェット管理
				</button>
			</div>

			{selectedWidgets.length === 0 ? (
				<div className="component-container">
					<div className="text-sm text-gray-500">
						ウィジェットが選択されていません。「ウィジェット管理」ボタンからウィジェットを追加してください。
					</div>
				</div>
			) : (
				<DragDropContext onDragEnd={handleOnDragEnd}>
					<Droppable droppableId="active-widgets">
						{(provided) => (
							<div
								{...provided.droppableProps}
								ref={provided.innerRef}
								className="grid gap-4"
							>
								{selectedWidgets.map((widgetId, index) => (
									<Draggable
										key={widgetId}
										draggableId={widgetId}
										index={index}
									>
										{(provided, snapshot) => (
											<div
												ref={provided.innerRef}
												{...provided.draggableProps}
												className={`${
													snapshot.isDragging ? 'opacity-75' : ''
												}`}
											>
												<div className="relative">
													<div
														{...provided.dragHandleProps}
														className="absolute top-2 right-2 cursor-move text-gray-400 hover:text-gray-600 z-10"
													>
														⋮⋮
													</div>
													{renderWidget(widgetId)}
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
			)}
		</div>
	)
}