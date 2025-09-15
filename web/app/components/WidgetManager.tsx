'use client'

import React from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'

type WidgetType = {
	id: string
	name: string
	description: string
}

type WidgetManagerProps = {
	availableWidgets: WidgetType[]
	selectedWidgets: string[]
	onWidgetsChange: (widgets: string[]) => void
}

export default function WidgetManager({
	availableWidgets,
	selectedWidgets,
	onWidgetsChange,
}: WidgetManagerProps) {
	const handleOnDragEnd = (result: DropResult) => {
		if (!result.destination) return

		const items = Array.from(selectedWidgets)
		const [reorderedItem] = items.splice(result.source.index, 1)
		items.splice(result.destination.index, 0, reorderedItem)

		onWidgetsChange(items)
	}

	const addWidget = (widgetId: string) => {
		if (!selectedWidgets.includes(widgetId)) {
			onWidgetsChange([...selectedWidgets, widgetId])
		}
	}

	const removeWidget = (widgetId: string) => {
		onWidgetsChange(selectedWidgets.filter(id => id !== widgetId))
	}

	const getWidgetInfo = (widgetId: string) => {
		return availableWidgets.find(w => w.id === widgetId)
	}

	return (
		<div className="component-container">
			<strong>ウィジェット管理</strong>
			
			{/* 利用可能なウィジェット */}
			<div className="mt-6">
				<h4 className="text-sm font-medium mb-2">利用可能なウィジェット</h4>
				<div className="grid gap-2">
					{availableWidgets.map(widget => (
						<div key={widget.id} className="flex justify-between items-center p-2 border rounded">
							<div>
								<div className="text-sm font-medium">{widget.name}</div>
								<div className="text-xs text-gray-600">{widget.description}</div>
							</div>
							<button
								onClick={() => addWidget(widget.id)}
								disabled={selectedWidgets.includes(widget.id)}
								className="px-2 py-1 text-xs bg-blue-500 text-white rounded disabled:bg-gray-300"
							>
								{selectedWidgets.includes(widget.id) ? '追加済み' : '追加'}
							</button>
						</div>
					))}
				</div>
			</div>

			{/* 選択されたウィジェット（ドラッグ&ドロップ対応） */}
			<div className="mt-6">
				<h4 className="text-sm font-medium mb-2">選択されたウィジェット</h4>
				{selectedWidgets.length === 0 ? (
					<div className="text-sm text-gray-500">ウィジェットが選択されていません</div>
				) : (
					<DragDropContext onDragEnd={handleOnDragEnd}>
						<Droppable droppableId="widgets">
							{(provided) => (
								<div
									{...provided.droppableProps}
									ref={provided.innerRef}
									className="grid gap-2"
								>
									{selectedWidgets.map((widgetId, index) => {
										const widget = getWidgetInfo(widgetId)
										if (!widget) return null

										return (
											<Draggable
												key={widgetId}
												draggableId={widgetId}
												index={index}
											>
												{(provided, snapshot) => (
													<div
														ref={provided.innerRef}
														{...provided.draggableProps}
														{...provided.dragHandleProps}
														className={`flex justify-between items-center p-2 border rounded ${
															snapshot.isDragging ? 'bg-blue-50' : 'bg-white'
														}`}
													>
														<div className="flex items-center">
															<div className="mr-2 cursor-move">⋮⋮</div>
															<div>
																<div className="text-sm font-medium">{widget.name}</div>
																<div className="text-xs text-gray-600">{widget.description}</div>
															</div>
														</div>
														<button
															onClick={() => removeWidget(widgetId)}
															className="px-2 py-1 text-xs bg-red-500 text-white rounded"
														>
															削除
														</button>
													</div>
												)}
											</Draggable>
										)
									})}
									{provided.placeholder}
								</div>
							)}
						</Droppable>
					</DragDropContext>
				)}
			</div>
		</div>
	)
}