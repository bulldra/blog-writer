'use client'

import { useMemo } from 'react'
import Collapsible from './Collapsible'

export type PlanPanelProps = {
	value: string
	onGenerate?: () => Promise<void> | void
	onClear?: () => void
	onExecute?: () => Promise<void> | void
}

export default function PlanPanel({
	value,
	onGenerate,
	onClear,
	onExecute,
}: PlanPanelProps) {
	const count = useMemo(() => (value ? value.length : 0), [value])

	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid #ddd',
				background: '#fff',
			}}>
			<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
				<strong>Plan</strong>
				<button onClick={() => onGenerate?.()} style={{ fontSize: 12 }}>
					プランを生成
				</button>
				<button onClick={() => onExecute?.()} style={{ fontSize: 12 }}>
					プランを実行
				</button>
				<button onClick={() => onClear?.()} style={{ fontSize: 12 }}>
					クリア
				</button>
				<span style={{ fontSize: 12, color: '#666' }}>
					生成時、# PLAN セクションとしてプロンプトに付与（編集不可）
				</span>
			</div>
			{value && (
				<Collapsible
					title="Plan"
					count={count}
					previewText={value}
					previewLines={3}
					contentAsMarkdown
					contentHeight={220}
					previewHeight={72}>
					{value}
				</Collapsible>
			)}
			{/* プランは編集不可。再生成で更新してください。 */}
		</div>
	)
}
