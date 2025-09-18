'use client'

import React from 'react'

type TemplateField = {
	key: string
	label: string
	input_type: 'text' | 'textarea' | 'date' | 'select'
	options?: string[]
}

type PropertiesWidgetProps = {
	fields: TemplateField[]
	values: Record<string, string>
	onFieldChange: (key: string, value: string) => void
}

export default function PropertiesWidget({
	fields,
	values,
	onFieldChange,
}: PropertiesWidgetProps) {
	if (!fields || fields.length === 0) {
		return (
			<div className="component-container">
				<strong>プロパティセット</strong>
				<div className="mt-4 text-sm text-gray-500">
					このテンプレートにはプロパティが定義されていません
				</div>
			</div>
		)
	}

	return (
		<div className="component-container">
			<strong>プロパティセット</strong>
			<div className="grid gap-4 mt-4">
				{fields.map((field) => {
					const value = values[field.key] || ''
					const commonProps = {
						value,
						onChange: (
							e: React.ChangeEvent<
								| HTMLInputElement
								| HTMLTextAreaElement
								| HTMLSelectElement
							>
						) => onFieldChange(field.key, e.target.value),
					}
					return (
						<div key={field.key} className="grid gap-2">
							<label className="text-sm font-medium">
								{field.label}
							</label>
							{field.input_type === 'textarea' && (
								<textarea
									placeholder={field.key}
									{...(commonProps as any)}
									rows={3}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'text' && (
								<input
									type="text"
									placeholder={field.key}
									{...(commonProps as any)}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'date' && (
								<input
									type="date"
									{...(commonProps as any)}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'select' && (
								<select
									{...(commonProps as any)}
									className="w-full p-2 border rounded text-sm">
									<option value="">選択してください</option>
									{(field.options || []).map((opt) => (
										<option key={opt} value={opt}>
											{opt}
										</option>
									))}
								</select>
							)}
						</div>
					)
				})}
			</div>
		</div>
	)
}
