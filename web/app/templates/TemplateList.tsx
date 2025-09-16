'use client'
import React from 'react'

export type ArticleTemplate = {
	type: string
	name: string
}

type Props = {
	list: ArticleTemplate[]
	currentType: string
	onSelect: (type: string) => void
	onDelete: (type: string) => void
}

export default function TemplateList({
	list,
	currentType,
	onSelect,
	onDelete,
}: Props) {
	return (
		<ul style={{ listStyle: 'none', padding: 0, margin: 8 }}>
			{list.map((tpl) => {
				const isBuiltin = ['url', 'note', 'review'].includes(tpl.type)
				return (
					<li key={tpl.type} style={{ marginBottom: 6 }}>
						<div
							style={{
								display: 'flex',
								alignItems: 'stretch',
								gap: 6,
							}}>
							{!isBuiltin && (
								<button
									onClick={() => onDelete(tpl.type)}
									style={{
										fontSize: 12,
										padding: '6px 8px',
										border: '1px solid #ddd',
										background: '#fff',
										color: '#a00',
										cursor: 'pointer',
									}}
									title="削除">
									削除
								</button>
							)}
							<button
								onClick={() => onSelect(tpl.type)}
								style={{
									flex: 1,
									textAlign: 'left',
									padding: '6px 8px',
									background:
										currentType === tpl.type
											? '#eef5ff'
											: '#f9f9f9',
									border: '1px solid #ddd',
									cursor: 'pointer',
								}}>
								<div style={{ fontWeight: 600 }}>
									{tpl.name || tpl.type}
								</div>
								<div style={{ fontSize: 12, color: '#666' }}>
									{tpl.type}
								</div>
							</button>
						</div>
					</li>
				)
			})}
			{list.length === 0 ? (
				<li style={{ fontSize: 12, color: '#666' }}>
					テンプレートが見つかりません
				</li>
			) : null}
		</ul>
	)
}
