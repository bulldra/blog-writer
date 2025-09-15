'use client'

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

// 書籍選択やハイライトの参照は Writer タブで行う
export default function ObsidianPage() {
	const [obsidianDir, setObsidianDir] = useState('')
	const [obsidianDirInput, setObsidianDirInput] = useState('')
	const [healthDir, setHealthDir] = useState('')
	const [healthError, setHealthError] = useState('')
	const [saving, setSaving] = useState(false)

	useEffect(() => {
		;(async () => {
			try {
				const r = await fetch(`${API_BASE}/api/obsidian/health`)
				if (!r.ok) {
					setHealthError(`health取得に失敗 (status ${r.status})`)
					return
				}
				const j = await r.json()
				setHealthDir(j?.obsidianDir || '')
			} catch {
				setHealthError('health取得に失敗（ネットワーク）')
			}
		})()
		;(async () => {
			try {
				const r = await fetch(`${API_BASE}/api/obsidian/config`)
				if (r.ok) {
					const j = await r.json()
					setObsidianDir(j?.rootDir || '')
					setObsidianDirInput(j?.rootDir || '')
				}
			} catch {
				/* noop */
			}
		})()
	}, [])

	const save = async (path: string | null) => {
		setSaving(true)
		try {
			const config = {
				root_dir: path || null,
				articles_dir: "articles",
				highlights_dir: "kindle_highlights"
			}
			const r = await fetch(`${API_BASE}/api/obsidian/config`, { 
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config)
			})
			if (r.ok) {
				const j = await r.json()
				setObsidianDir(j?.effective?.rootDir || '')
				if (!path) setObsidianDirInput('')
			} else {
				alert('設定に失敗しました')
			}
		} catch {
			alert('設定に失敗しました（ネットワーク）')
		} finally {
			setSaving(false)
		}
	}

	return (
		<div style={{ maxWidth: 900, margin: '2rem auto', padding: '0 1rem' }}>
			<h1>Obsidian 管理</h1>
			<section
				style={{
					margin: '8px 0 12px 0',
					padding: 8,
					border: '1px solid #ddd',
					background: '#fff',
					display: 'grid',
					gap: 6,
				}}>
				<strong>Obsidian ディレクトリ</strong>
				<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
					<input
						placeholder="/absolute/path/to/obsidian/kindle_highlight"
						value={obsidianDirInput}
						onChange={(e) => setObsidianDirInput(e.target.value)}
						style={{ flex: 1 }}
					/>
					<button
						onClick={() => save(obsidianDirInput.trim() || '')}
						disabled={saving}
						style={{ fontSize: 12 }}>
						保存
					</button>
					<button
						onClick={() => save(null)}
						disabled={saving}
						style={{ fontSize: 12 }}>
						クリア
					</button>
				</div>
				<div style={{ fontSize: 12, color: '#444' }}>
					現在の設定: {obsidianDir || '(未設定)'}
				</div>
			</section>
			<section style={{ marginTop: 10, fontSize: 14, color: '#333' }}>
				書籍の選択とハイライトの参照は Writer タブで行ってください。
				<a href="/" style={{ marginLeft: 8 }}>
					Writer を開く
				</a>
			</section>
			<div style={{ marginTop: 10, fontSize: 12, color: '#444' }}>
				{healthError ? (
					<span style={{ color: '#a00' }}>{healthError}</span>
				) : (
					<span>検出ディレクトリ: {healthDir || '(未検出)'}</span>
				)}
			</div>
		</div>
	)
}
