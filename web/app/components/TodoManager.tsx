'use client'

import { useEffect, useId, useMemo, useState } from 'react'

export type TodoItem = {
	id: string
	text: string
	done: boolean
}

type Props = {
	value: TodoItem[]
	onChange: (items: TodoItem[]) => void
}

export default function TodoManager({ value, onChange }: Props) {
	const [input, setInput] = useState('')
	const idPrefix = useId()

	const add = () => {
		const t = input.trim()
		if (!t) return
		const item: TodoItem = {
			id: `${idPrefix}-${Date.now()}-${Math.random()
				.toString(36)
				.slice(2, 7)}`,
			text: t,
			done: false,
		}
		onChange([...(value || []), item])
		setInput('')
	}
	const toggle = (id: string) => {
		onChange(
			value.map((it) => (it.id === id ? { ...it, done: !it.done } : it))
		)
	}
	const update = (id: string, text: string) => {
		onChange(value.map((it) => (it.id === id ? { ...it, text } : it)))
	}
	const remove = (id: string) => {
		onChange(value.filter((it) => it.id !== id))
	}
	const move = (id: string, dir: -1 | 1) => {
		const idx = value.findIndex((it) => it.id === id)
		if (idx < 0) return
		const j = idx + dir
		if (j < 0 || j >= value.length) return
		const arr = value.slice()
		const [it] = arr.splice(idx, 1)
		arr.splice(j, 0, it)
		onChange(arr)
	}

	const hasItems = useMemo(() => (value || []).length > 0, [value])

	useEffect(() => {
		// フォーカス時に Enter で追加
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) add()
		}
		window.addEventListener('keydown', onKey)
		return () => window.removeEventListener('keydown', onKey)
		// add は安定しているため依存に含めない
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [])

	return (
		<div style={{ display: 'grid', gap: 8 }}>
			<div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
				<input
					placeholder="TODO を追加（Cmd/Ctrl+Enter で追加）"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					style={{ flex: 1 }}
				/>
				<button onClick={add} style={{ fontSize: 12 }}>
					追加
				</button>
			</div>
			{hasItems && (
				<ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
					{value.map((it, i) => (
						<li
							key={it.id}
							style={{
								display: 'flex',
								gap: 6,
								alignItems: 'center',
								padding: '4px 0',
							}}>
							<input
								type="checkbox"
								checked={it.done}
								onChange={() => toggle(it.id)}
							/>
							<input
								value={it.text}
								onChange={(e) => update(it.id, e.target.value)}
								style={{
									flex: 1,
									textDecoration: it.done
										? 'line-through'
										: 'none',
									color: it.done ? '#666' : 'inherit',
								}}
							/>
							<div style={{ display: 'flex', gap: 4 }}>
								<button
									onClick={() => move(it.id, -1)}
									disabled={i === 0}
									title="上へ"
									style={{ fontSize: 12 }}>
									↑
								</button>
								<button
									onClick={() => move(it.id, 1)}
									disabled={i === value.length - 1}
									title="下へ"
									style={{ fontSize: 12 }}>
									↓
								</button>
								<button
									onClick={() => remove(it.id)}
									title="削除"
									style={{ fontSize: 12 }}>
									削除
								</button>
							</div>
						</li>
					))}
				</ul>
			)}
		</div>
	)
}
