'use client'

import React from 'react'

interface GenerationControlsProps {
	isStreaming: boolean
	onGenerate: () => void
	onGenerateFromTodos: () => void
	onStop: () => void
}

export default function GenerationControls({
	isStreaming,
	onGenerate,
	onGenerateFromTodos,
	onStop,
}: GenerationControlsProps) {
	return (
		<div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
			{!isStreaming ? (
				<>
					<button onClick={onGenerate}>生成</button>
					<button
						onClick={onGenerateFromTodos}
						title="TODO もPLANも空でも続行可能です">
						TODOで生成
					</button>
				</>
			) : (
				<button onClick={onStop}>停止</button>
			)}
		</div>
	)
}