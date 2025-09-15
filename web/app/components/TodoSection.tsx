'use client'

import React from 'react'
import TodoManager, { type TodoItem } from './TodoManager'

interface TodoSectionProps {
	todos: TodoItem[]
	onTodosChange: (todos: TodoItem[]) => void
}

export default function TodoSection({ todos, onTodosChange }: TodoSectionProps) {
	return (
		<div className="component-container">
			<strong>TODO</strong>
			<div className="mt-6">
				<TodoManager value={todos} onChange={onTodosChange} />
				<div className="todo-description">
					生成時に TODO を # TODO
					セクションとしてプロンプトに付加します。完了にチェックすると打ち消し線になります。
				</div>
			</div>
		</div>
	)
}