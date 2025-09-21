'use client'

import React, { useState } from 'react'
import Image from 'next/image'

type Props = {
	url: string
	selector: string
	mode: 'text' | 'screenshot' | 'both'
	timeoutMs: number
	headless: boolean
	width: number
	height: number
	apiBase?: string
	onChange: (
		next: Partial<{
			url: string
			selector: string
			mode: 'text' | 'screenshot' | 'both'
			timeoutMs: number
			headless: boolean
			width: number
			height: number
		}>
	) => void
}

export default function ScrapeWidget(props: Props) {
	const [isPreviewing, setIsPreviewing] = useState(false)
	const [previewText, setPreviewText] = useState('')
	const [previewImg, setPreviewImg] = useState('')
	const [error, setError] = useState('')

	const runPreview = async () => {
		setIsPreviewing(true)
		setError('')
		setPreviewText('')
		setPreviewImg('')
		try {
			const base = (props.apiBase || '').replace(/\/$/, '')
			const res = await fetch(`${base}/api/widgets/scrape/preview`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					url: props.url,
					selector: props.selector || 'body',
					mode: props.mode,
					timeout_ms: props.timeoutMs,
					headless: props.headless,
					viewport: { width: props.width, height: props.height },
				}),
			})
			if (!res.ok) {
				setError('プレビューの実行に失敗しました')
				return
			}
			const json = await res.json()
			if (!json.ok) {
				setError(json.error || 'スクレイプに失敗しました')
				return
			}
			setPreviewText(String(json.text || ''))
			setPreviewImg(String(json.image_data_url || ''))
		} catch {
			setError('通信エラー')
		} finally {
			setIsPreviewing(false)
		}
	}

	return (
		<div className="component-container">
			<strong>スクレイピング</strong>
			<div className="mt-4 grid gap-3 text-sm">
				<div className="text-xs text-gray-600">
					Selenium + ChromeDriver
					でページ本文抽出やスクリーンショットを取得します
				</div>

				<label className="grid gap-1">
					<span className="text-xs text-gray-600">URL</span>
					<input
						className="p-2 border rounded"
						placeholder="https://example.com/..."
						value={props.url}
						onChange={(e) =>
							props.onChange({ url: e.target.value })
						}
					/>
				</label>

				<label className="grid gap-1">
					<span className="text-xs text-gray-600">
						CSS セレクタ（任意）
					</span>
					<input
						className="p-2 border rounded"
						placeholder="main, article, #content など"
						value={props.selector}
						onChange={(e) =>
							props.onChange({ selector: e.target.value })
						}
					/>
				</label>

				<div className="grid grid-cols-1 md:grid-cols-3 gap-3">
					<label className="grid gap-1">
						<span className="text-xs text-gray-600">モード</span>
						<select
							className="p-2 border rounded"
							value={props.mode}
							onChange={(e) =>
								props.onChange({
									mode: e.target.value as Props['mode'],
								})
							}>
							<option value="text">text</option>
							<option value="screenshot">screenshot</option>
							<option value="both">both</option>
						</select>
					</label>

					<label className="grid gap-1">
						<span className="text-xs text-gray-600">
							タイムアウト(ms)
						</span>
						<input
							type="number"
							className="p-2 border rounded"
							min={1000}
							step={500}
							value={props.timeoutMs}
							onChange={(e) =>
								props.onChange({
									timeoutMs: Number(e.target.value),
								})
							}
						/>
					</label>

					<label className="flex items-center gap-2 mt-6 md:mt-0">
						<input
							type="checkbox"
							checked={props.headless}
							onChange={(e) =>
								props.onChange({ headless: e.target.checked })
							}
						/>
						<span className="text-xs text-gray-600">
							ヘッドレス
						</span>
					</label>
				</div>

				<div className="grid grid-cols-2 gap-3">
					<label className="grid gap-1">
						<span className="text-xs text-gray-600">幅(px)</span>
						<input
							type="number"
							className="p-2 border rounded"
							min={320}
							step={10}
							value={props.width}
							onChange={(e) =>
								props.onChange({
									width: Number(e.target.value),
								})
							}
						/>
					</label>
					<label className="grid gap-1">
						<span className="text-xs text-gray-600">高さ(px)</span>
						<input
							type="number"
							className="p-2 border rounded"
							min={320}
							step={10}
							value={props.height}
							onChange={(e) =>
								props.onChange({
									height: Number(e.target.value),
								})
							}
						/>
					</label>
				</div>

				<div className="flex items-center gap-2">
					<button
						onClick={runPreview}
						disabled={isPreviewing || !props.url}
						className="px-3 py-1 text-xs bg-blue-600 text-white rounded disabled:opacity-50">
						{isPreviewing ? 'プレビュー中…' : 'プレビュー'}
					</button>
					{error && (
						<span className="text-xs text-red-600">{error}</span>
					)}
				</div>

				{(previewText || previewImg) && (
					<div className="mt-3 grid gap-2">
						<div className="text-xs text-gray-600">
							プレビュー結果
						</div>
						{previewText && (
							<textarea
								readOnly
								className="p-2 border rounded text-xs"
								style={{ height: 100 }}
								value={previewText}
							/>
						)}
						{previewImg && (
							<div className="border rounded p-1">
								<Image
									src={previewImg}
									alt="screenshot preview"
									width={Math.max(1, props.width || 800)}
									height={Math.max(1, props.height || 600)}
									sizes="(max-width: 768px) 100vw, 50vw"
									style={{
										width: '100%',
										height: 'auto',
										maxHeight: 240,
										objectFit: 'contain',
									}}
									unoptimized
								/>
							</div>
						)}
					</div>
				)}
			</div>
		</div>
	)
}
