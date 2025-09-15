'use client'

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Phrase = { id: number; text: string; note?: string }

export default function PhrasesPage() {
	const [items, setItems] = useState<Phrase[]>([])
	const [text, setText] = useState('')

	const load = async () => {
		const res = await fetch(`${API_BASE}/api/phrases`)
		const json = await res.json()
		setItems(json)
	}
	useEffect(() => {
		load()
	}, [])

	const add = async () => {
		if (!text.trim()) return
		await fetch(`${API_BASE}/api/phrases`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ text }),
		})
		setText('')
		load()
	}

	const remove = async (id: number) => {
		await fetch(`${API_BASE}/api/phrases/${id}`, { method: 'DELETE' })
		load()
	}

	return (
		<div style={{ maxWidth: 900 }}>
			<h1>いい回し 管理</h1>
			<div style={{ display: 'flex', gap: 8 }}>
				<input
					value={text}
					onChange={(e) => setText(e.target.value)}
					style={{ flex: 1 }}
				/>
				<button onClick={add}>追加</button>
				<button onClick={load}>更新</button>
			</div>
			<ul>
				{items.map((p) => (
					<li
						key={p.id}
						style={{
							display: 'flex',
							alignItems: 'center',
							gap: 8,
						}}>
						<span style={{ flex: 1 }}>{p.text}</span>
						<button onClick={() => remove(p.id)}>削除</button>
					</li>
				))}
			</ul>
		</div>
	)
}
