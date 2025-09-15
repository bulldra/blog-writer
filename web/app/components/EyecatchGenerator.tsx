'use client'

import React from 'react'

interface EyecatchGeneratorProps {
	eyecatchUrl: string
	eyecatchTheme: 'light' | 'dark'
	draft: string
	onThemeChange: (theme: 'light' | 'dark') => void
	onGenerate: () => void
	onDownloadJpeg: () => void
}

export default function EyecatchGenerator({
	eyecatchUrl,
	eyecatchTheme,
	draft,
	onThemeChange,
	onGenerate,
	onDownloadJpeg,
}: EyecatchGeneratorProps) {
	return (
		<div
			style={{
				display: 'flex',
				gap: 8,
				alignItems: 'center',
			}}>
			<button onClick={onGenerate} style={{ fontSize: 12 }}>
				アイキャッチ生成
			</button>
			<select
				value={eyecatchTheme}
				onChange={(e) => onThemeChange(e.target.value as 'light' | 'dark')}
				style={{ fontSize: 12 }}>
				<option value="light">light</option>
				<option value="dark">dark</option>
			</select>
			{eyecatchUrl && (
				<>
					<a
						href={eyecatchUrl}
						download={
							(draft.match(/^#\s*(.+)/m)?.[1] || 'eyecatch') +
							'.svg'
						}
						style={{ fontSize: 12 }}>
						SVGをダウンロード
					</a>
					<button onClick={onDownloadJpeg} style={{ fontSize: 12 }}>
						JPEGでダウンロード
					</button>
				</>
			)}
		</div>
	)
}