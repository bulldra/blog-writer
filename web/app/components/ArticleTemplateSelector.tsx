'use client'

import React from 'react'

type TemplateDef = {
	name: string
	fields: {
		key: string
		label: string
		input_type: 'text' | 'textarea' | 'date' | 'select'
		options?: string[]
	}[]
	widgets?: string[]
} | null

type Props = {
	articleTpl: string | ''
	articleTplList: { type: string; name: string }[]
	onChangeArticleTpl: (v: string) => void
	articleTplDef: TemplateDef
}

export default function ArticleTemplateSelector({
	articleTpl,
	articleTplList,
	onChangeArticleTpl,
}: Props) {
	return (
		<div className="component-container">
			<strong>記事テンプレート（任意）</strong>
			<div className="flex-row mt-6">
				<select
					value={articleTpl}
					onChange={(e) => onChangeArticleTpl(e.target.value)}
					className="select-width">
					{articleTplList.map((t) => (
						<option key={t.type} value={t.type}>
							{t.name} ({t.type})
						</option>
					))}
				</select>
				<a href="/templates" className="text-xs">
					⚙︎ 管理
				</a>
			</div>
		</div>
	)
}
