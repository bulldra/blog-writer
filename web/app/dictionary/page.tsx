'use client'

import { useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Entry = {
	term: string
	definitions: { pos?: string; def: string }[]
	synonyms: string[]
	antonyms: string[]
}

export default function DictionaryPage() {
	const [term, setTerm] = useState('')
	const [entry, setEntry] = useState<Entry | null>(null)

	const lookup = async () => {
		if (!term.trim()) return
		const res = await fetch(
			`${API_BASE}/api/dict?term=${encodeURIComponent(term)}`
		)
		const json = await res.json()
		setEntry(json)
	}

	return (
		<div style={{ maxWidth: 900 }}>
			<h1>辞書</h1>
			<div style={{ display: 'flex', gap: 8 }}>
				<input
					value={term}
					onChange={(e) => setTerm(e.target.value)}
					style={{ flex: 1 }}
				/>
				<button onClick={lookup}>検索</button>
			</div>
			{entry && (
				<div style={{ marginTop: 16 }}>
					<h2>{entry.term}</h2>
					<h3>定義</h3>
					<ul>
						{entry.definitions.map((d, i) => (
							<li key={i}>
								{d.pos ? `${d.pos} ` : ''}
								{d.def}
							</li>
						))}
					</ul>
					{!!entry.synonyms?.length && (
						<>
							<h3>類語</h3>
							<p>{entry.synonyms.join(', ')}</p>
						</>
					)}
					{!!entry.antonyms?.length && (
						<>
							<h3>反義語</h3>
							<p>{entry.antonyms.join(', ')}</p>
						</>
					)}
				</div>
			)}
		</div>
	)
}
