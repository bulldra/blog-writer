'use client'

import { useEffect, useState } from 'react'
import ComboBox from '../components/ComboBox'
import ThemeToggle from '../components/ThemeToggle'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function SettingsPage() {
	const [provider, setProvider] = useState<'gemini' | 'lmstudio'>('lmstudio')
	const [apiKey, setApiKey] = useState('')
	const [model, setModel] = useState('openai/gpt-oss-20b')
	const [maxLen, setMaxLen] = useState<number>(32768)
	const [saved, setSaved] = useState<string | null>(null)
	const [hasKey, setHasKey] = useState<boolean | null>(null)

	// Obsidian 設定用のstate
	const [obsidianDir, setObsidianDir] = useState('')
	const [obsidianDirInput, setObsidianDirInput] = useState('')
	const [healthDir, setHealthDir] = useState('')
	const [healthError, setHealthError] = useState('')
	const [obsidianSaving, setObsidianSaving] = useState(false)

	// EPUB 設定用のstate
	const [epubDir, setEpubDir] = useState('')
	const [epubDirInput, setEpubDirInput] = useState('')
	const [epubSaving, setEpubSaving] = useState(false)

	useEffect(() => {
		// AI設定の取得
		;(async () => {
			try {
				const res = await fetch(`${API_BASE}/api/ai/settings`)
				if (!res.ok) return
				const json = await res.json()
				setProvider(json.provider || 'lmstudio')
				setModel(
					json.model ||
						(json.provider === 'lmstudio'
							? 'openai/gpt-oss-20b'
							: 'gemini-2.5-flash')
				)
				setHasKey(!!json.hasKey)
				if (typeof json.max_prompt_len === 'number')
					setMaxLen(json.max_prompt_len)
			} catch {}
		})()

		// Obsidian設定の取得
		;(async () => {
			try {
				const r = await fetch(`${API_BASE}/api/obsidian/health`)
				if (!r.ok) {
					setHealthError(`health取得に失敗 (status ${r.status})`)
				} else {
					const j = await r.json()
					setHealthDir(j?.obsidianDir || '')
				}
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

		// EPUB設定の取得
		;(async () => {
			try {
				const r = await fetch(`${API_BASE}/api/epub/settings`)
				if (r.ok) {
					const j = await r.json()
					setEpubDir(j?.epub_directory || '')
					setEpubDirInput(j?.epub_directory || '')
				}
			} catch {
				/* noop */
			}
		})()
	}, [])

	const save = async () => {
		setSaved(null)
		const res = await fetch(`${API_BASE}/api/ai/settings`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				provider,
				api_key: apiKey,
				model,
				max_prompt_len: maxLen,
			}),
		})
		if (res.ok) {
			setSaved('保存しました')
			// 再取得して保存状態を反映
			try {
				const r = await fetch(`${API_BASE}/api/ai/settings`)
				if (r.ok) {
					const j = await r.json()
					setHasKey(!!j.hasKey)
				}
			} catch {}
		} else setSaved('保存に失敗しました')
	}

	const saveObsidian = async (path: string | null) => {
		setObsidianSaving(true)
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
			setObsidianSaving(false)
		}
	}

	const saveEpub = async (path: string | null) => {
		setEpubSaving(true)
		try {
			const config = {
				epub_directory: path || '',
				embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
				chunk_size: 500,
				overlap_size: 50,
				search_top_k: 5,
				min_similarity_score: 0.1
			}
			const r = await fetch(`${API_BASE}/api/epub/settings`, { 
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config)
			})
			if (r.ok) {
				setEpubDir(path || '')
				if (!path) setEpubDirInput('')
				alert('EPUB設定を保存しました')
			} else {
				alert('設定に失敗しました')
			}
		} catch {
			alert('設定に失敗しました（ネットワーク）')
		} finally {
			setEpubSaving(false)
		}
	}

	return (
		<main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
			<h1>AI 設定</h1>
			<p>
				プロバイダを選択してください。Gemini の場合は API キー、LM
				Studio の場合は Base URL（例:
				http://localhost:1234/v1）を保存します。
			</p>

			<label>Provider</label>
			<ComboBox
				value={provider}
				onChange={(v: string) =>
					setProvider(v === 'gemini' ? 'gemini' : 'lmstudio')
				}
				options={[
					{ value: 'gemini', label: 'Gemini' },
					{ value: 'lmstudio', label: 'LM Studio (OpenAI互換)' },
				]}
				placeholder="Provider を選択"
			/>

			<label style={{ display: 'block', marginTop: 12 }}>
				{provider === 'gemini' ? 'API Key' : 'LM Studio Base URL'}
			</label>
			<input
				type={provider === 'gemini' ? 'password' : 'text'}
				value={apiKey}
				onChange={(e) => setApiKey(e.target.value)}
				placeholder={
					provider === 'gemini'
						? 'AIza...'
						: 'http://localhost:1234/v1'
				}
				style={{ width: '100%' }}
			/>

			<label style={{ display: 'block', marginTop: 12 }}>Model</label>
			{provider === 'gemini' ? (
				<ComboBox
					value={model}
					onChange={setModel}
					options={['gemini-2.5-flash', 'gemini-2.5-pro']}
					placeholder="Model を選択"
				/>
			) : (
				<input
					value={model}
					onChange={(e) => setModel(e.target.value)}
					placeholder="openai/gpt-oss-20b"
					style={{ width: '100%' }}
				/>
			)}

			<label style={{ display: 'block', marginTop: 12 }}>
				最大コンテキスト長（文字数）
			</label>
			<input
				type="number"
				min={100}
				max={131072}
				step={256}
				value={maxLen}
				onChange={(e) =>
					setMaxLen(
						Math.max(
							100,
							Math.min(131072, Number(e.target.value) || 32768)
						)
					)
				}
				style={{ width: '100%' }}
			/>

			<div style={{ marginTop: 16 }}>
				<button onClick={save}>保存</button>
				{saved && <span style={{ marginLeft: 8 }}>{saved}</span>}
				{hasKey !== null && (
					<span
						style={{
							marginLeft: 12,
							color: hasKey ? 'green' : 'crimson',
						}}>
						APIキー: {hasKey ? '保存済み' : '未設定'}
					</span>
				)}
			</div>

			<hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />
			
			<h2>Obsidian設定</h2>
			<p>Obsidianのハイライトディレクトリを設定することで、Kindle Highlightを利用できます。</p>
			
			<section
				style={{
					margin: '16px 0',
					padding: 16,
					border: '1px solid var(--border-color)',
					borderRadius: '8px',
					backgroundColor: 'var(--background-secondary)',
				}}>
				<label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
					Obsidian ディレクトリ
				</label>
				<div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
					<input
						placeholder="/absolute/path/to/obsidian/kindle_highlight"
						value={obsidianDirInput}
						onChange={(e) => setObsidianDirInput(e.target.value)}
						style={{ flex: 1, padding: 8 }}
					/>
					<button
						onClick={() => saveObsidian(obsidianDirInput.trim() || '')}
						disabled={obsidianSaving}
						style={{ padding: '8px 16px' }}>
						保存
					</button>
					<button
						onClick={() => saveObsidian(null)}
						disabled={obsidianSaving}
						style={{ padding: '8px 16px' }}>
						クリア
					</button>
				</div>
				<div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 8 }}>
					現在の設定: {obsidianDir || '(未設定)'}
				</div>
				<div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
					{healthError ? (
						<span style={{ color: 'var(--color-error)' }}>{healthError}</span>
					) : (
						<span>検出ディレクトリ: {healthDir || '(未検出)'}</span>
					)}
				</div>
			</section>

			<hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />
			
			<h2>EPUB設定</h2>
			<p>EPUBファイルが格納されているディレクトリを設定することで、書籍検索機能を利用できます。</p>
			
			<section
				style={{
					margin: '16px 0',
					padding: 16,
					border: '1px solid var(--border-color)',
					borderRadius: '8px',
					backgroundColor: 'var(--background-secondary)',
				}}>
				<label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
					EPUB ディレクトリ
				</label>
				<div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
					<input
						placeholder="/absolute/path/to/epub/files"
						value={epubDirInput}
						onChange={(e) => setEpubDirInput(e.target.value)}
						style={{ flex: 1, padding: 8 }}
					/>
					<button
						onClick={() => saveEpub(epubDirInput.trim() || '')}
						disabled={epubSaving}
						style={{ padding: '8px 16px' }}>
						保存
					</button>
					<button
						onClick={() => saveEpub(null)}
						disabled={epubSaving}
						style={{ padding: '8px 16px' }}>
						クリア
					</button>
				</div>
				<div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 8 }}>
					現在の設定: {epubDir || '(未設定)'}
				</div>
			</section>

			<hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />
			
			<h2>テーマ設定</h2>
			<p>アプリケーションの表示テーマを切り替えることができます。</p>
			<ThemeToggle />
		</main>
	)
}
