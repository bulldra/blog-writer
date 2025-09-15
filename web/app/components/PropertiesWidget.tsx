'use client'

import React from 'react'

type TemplateField = {
	key: string
	label: string
	input_type: 'text' | 'textarea'
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
				{fields.map((field) => (
					<div key={field.key} className="grid gap-2">
						<label className="text-sm font-medium">
							{field.label}
						</label>
						{field.input_type === 'textarea' ? (
							<textarea
								placeholder={field.key}
								value={values[field.key] || ''}
								onChange={(e) => onFieldChange(field.key, e.target.value)}
								rows={3}
								className="w-full p-2 border rounded text-sm"
							/>
						) : (
							<input
								type="text"
								placeholder={field.key}
								value={values[field.key] || ''}
								onChange={(e) => onFieldChange(field.key, e.target.value)}
								className="w-full p-2 border rounded text-sm"
							/>
						)}
					</div>
				))}
			</div>
		</div>
	)
}