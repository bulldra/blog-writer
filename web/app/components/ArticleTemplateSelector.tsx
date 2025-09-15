'use client'

import React from 'react'

type TemplateDef = {
	name: string
	fields: {
		key: string
		label: string
		input_type: 'text' | 'textarea'
	}[]
	widgets?: string[]
} | null

type Props = {
	articleTpl: string | ''
	articleTplList: { type: string; name: string }[]
	onChangeArticleTpl: (v: string) => void
	articleTplDef: TemplateDef
	articleTplFields: Record<string, string>
	onChangeField: (key: string, value: string) => void
	urlCtx: string
	onChangeUrlCtx: (v: string) => void
}

export default function ArticleTemplateSelector({
	articleTpl,
	articleTplList,
	onChangeArticleTpl,
	articleTplDef,
	articleTplFields,
	onChangeField,
	urlCtx,
	onChangeUrlCtx,
}: Props) {
	const renderFields = () => {
		if (!articleTplDef || !articleTplDef.fields?.length) return null
		return (
			<div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
				{articleTplDef.fields.map((f) => (
					<div key={f.key} style={{ display: 'grid', gap: 4 }}>
						<label style={{ fontSize: 12 }}>{f.label}</label>
						{f.input_type === 'textarea' ? (
							<textarea
								placeholder={f.key}
								value={articleTplFields[f.key] || ''}
								onChange={(e) =>
									onChangeField(f.key, e.target.value)
								}
								rows={3}
							/>
						) : (
							<input
								placeholder={f.key}
								value={articleTplFields[f.key] || ''}
								onChange={(e) =>
									onChangeField(f.key, e.target.value)
								}
							/>
						)}
					</div>
				))}
			</div>
		)
	}

	const showUrlWidget = articleTplDef?.widgets?.includes('url_context')

	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid #ddd',
				background: '#fff',
			}}>
			<strong>記事テンプレート（任意）</strong>
			<div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
				<select
					value={articleTpl}
					onChange={(e) => onChangeArticleTpl(e.target.value)}
					style={{ width: 260 }}>
					{articleTplList.map((t) => (
						<option key={t.type} value={t.type}>
							{t.name} ({t.type})
						</option>
					))}
				</select>
				<a href="/templates" style={{ fontSize: 12 }}>
					⚙︎ 管理
				</a>
			</div>
			{articleTpl && renderFields()}
			{showUrlWidget && (
				<div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
					<div style={{ fontSize: 12, color: '#666' }}>
						URL コンテキストを利用します。テンプレートに url
						プロパティが
						あればそちらを優先し、未入力時は以下の値を送信します。
					</div>
					<div
						style={{
							display: 'flex',
							gap: 6,
							alignItems: 'center',
						}}>
						<input
							placeholder="https://example.com/...（未指定可）"
							value={urlCtx}
							onChange={(e) => onChangeUrlCtx(e.target.value)}
							style={{ flex: 1 }}
						/>
						{urlCtx && (
							<button
								onClick={() => onChangeUrlCtx('')}
								style={{ fontSize: 12 }}>
								クリア
							</button>
						)}
					</div>
				</div>
			)}
		</div>
	)
}
