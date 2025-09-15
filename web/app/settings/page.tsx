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

	useEffect(() => {
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
			
			<h2>テーマ設定</h2>
			<p>アプリケーションの表示テーマを切り替えることができます。</p>
			<ThemeToggle />
		</main>
	)
}
