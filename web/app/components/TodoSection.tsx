'use client'

import React from 'react'
import TodoManager, { type TodoItem } from './TodoManager'

interface TodoSectionProps {
	todos: TodoItem[]
	onTodosChange: (todos: TodoItem[]) => void
}

export default function TodoSection({ todos, onTodosChange }: TodoSectionProps) {
	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid var(--border-color)',
				background: 'var(--bg-secondary)',
			}}>
			<strong>TODO</strong>
			<div style={{ marginTop: 6 }}>
				<TodoManager value={todos} onChange={onTodosChange} />
				<div
					style={{
						fontSize: 12,
						color: 'var(--text-color)',
						marginTop: 4,
					}}>
					生成時に TODO を # TODO
					セクションとしてプロンプトに付加します。完了にチェックすると打ち消し線になります。
				</div>
			</div>
		</div>
	)
}