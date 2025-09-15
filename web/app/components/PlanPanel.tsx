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
		<div className="component-container">
			<div className="flex-row">
				<strong>Plan</strong>
				<button onClick={() => onGenerate?.()} className="text-xs">
					プランを生成
				</button>
				<button onClick={() => onExecute?.()} className="text-xs">
					プランを実行
				</button>
				<button onClick={() => onClear?.()} className="text-xs">
					クリア
				</button>
				<span className="text-xs text-secondary">
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
