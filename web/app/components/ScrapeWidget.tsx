'use client'

import React from 'react'

type Props = {
	url: string
	selector: string
	mode: 'text' | 'screenshot' | 'both'
	timeoutMs: number
	headless: boolean
	width: number
	height: number
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
			</div>
		</div>
	)
}
