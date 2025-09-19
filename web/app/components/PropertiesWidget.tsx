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
	onFieldsChange?: (fields: TemplateField[]) => void
	editable?: boolean
}

type FieldEditorProps = {
	field: TemplateField
	onSave: (field: TemplateField) => void
	onCancel: () => void
}

function FieldEditor({ field, onSave, onCancel }: FieldEditorProps) {
	const [editField, setEditField] = React.useState<TemplateField>({ ...field })
	const [optionInput, setOptionInput] = React.useState('')

	const handleSave = () => {
		if (!editField.key.trim() || !editField.label.trim()) return
		
		// キーを正規化（英数字、アンダースコア、ハイフンのみ）
		const normalizedKey = editField.key.toLowerCase().replace(/[^a-z0-9_-]/g, '_')
		onSave({ ...editField, key: normalizedKey })
	}

	const addOption = () => {
		if (!optionInput.trim()) return
		const newOptions = [...(editField.options || []), optionInput.trim()]
		setEditField({ ...editField, options: newOptions })
		setOptionInput('')
	}

	const removeOption = (index: number) => {
		const newOptions = (editField.options || []).filter((_, i) => i !== index)
		setEditField({ ...editField, options: newOptions })
	}

	return (
		<div className="mt-4 p-4 border-2 border-blue-300 rounded bg-blue-50">
			<h3 className="text-sm font-bold mb-3">フィールド編集</h3>
			<div className="grid gap-3">
				<div>
					<label className="block text-xs font-medium mb-1">キー</label>
					<input
						type="text"
						value={editField.key}
						onChange={(e) => setEditField({ ...editField, key: e.target.value })}
						placeholder="field_key (英数字、_、- のみ)"
						className="w-full p-2 text-sm border rounded"
					/>
				</div>
				<div>
					<label className="block text-xs font-medium mb-1">ラベル</label>
					<input
						type="text"
						value={editField.label}
						onChange={(e) => setEditField({ ...editField, label: e.target.value })}
						placeholder="フィールドの表示名"
						className="w-full p-2 text-sm border rounded"
					/>
				</div>
				<div>
					<label className="block text-xs font-medium mb-1">入力タイプ</label>
					<select
						value={editField.input_type}
						onChange={(e) => setEditField({ 
							...editField, 
							input_type: e.target.value as TemplateField['input_type'],
							options: e.target.value === 'select' ? editField.options : undefined
						})}
						className="w-full p-2 text-sm border rounded"
					>
						<option value="text">テキスト</option>
						<option value="textarea">テキストエリア</option>
						<option value="date">日付</option>
						<option value="select">選択肢</option>
					</select>
				</div>
				{editField.input_type === 'select' && (
					<div>
						<label className="block text-xs font-medium mb-1">選択肢</label>
						<div className="space-y-2">
							{(editField.options || []).map((option, index) => (
								<div key={index} className="flex gap-2">
									<input
										type="text"
										value={option}
										readOnly
										className="flex-1 p-1 text-sm border rounded bg-gray-100"
									/>
									<button
										onClick={() => removeOption(index)}
										className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
									>
										削除
									</button>
								</div>
							))}
							<div className="flex gap-2">
								<input
									type="text"
									value={optionInput}
									onChange={(e) => setOptionInput(e.target.value)}
									onKeyDown={(e) => e.key === 'Enter' && addOption()}
									placeholder="新しい選択肢"
									className="flex-1 p-1 text-sm border rounded"
								/>
								<button
									onClick={addOption}
									className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
								>
									追加
								</button>
							</div>
						</div>
					</div>
				)}
			</div>
			<div className="flex gap-2 mt-4">
				<button
					onClick={handleSave}
					disabled={!editField.key.trim() || !editField.label.trim()}
					className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
				>
					保存
				</button>
				<button
					onClick={onCancel}
					className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
				>
					キャンセル
				</button>
			</div>
		</div>
	)
}

export default function PropertiesWidget({
	fields,
	values,
	onFieldChange,
	onFieldsChange,
	editable = false,
}: PropertiesWidgetProps) {
	const [editMode, setEditMode] = React.useState(false)
	const [editingField, setEditingField] = React.useState<TemplateField | null>(null)

	const addField = () => {
		if (!onFieldsChange) return
		const newField: TemplateField = {
			key: '',
			label: '',
			input_type: 'text'
		}
		setEditingField(newField)
	}

	const saveField = (field: TemplateField) => {
		if (!onFieldsChange || !field.key.trim() || !field.label.trim()) return
		
		const updatedFields = editingField && fields.some(f => f.key === editingField.key)
			? fields.map(f => f.key === editingField.key ? field : f)
			: [...fields, field]
		
		onFieldsChange(updatedFields)
		setEditingField(null)
	}

	const deleteField = (key: string) => {
		if (!onFieldsChange) return
		onFieldsChange(fields.filter(f => f.key !== key))
	}

	const editField = (field: TemplateField) => {
		setEditingField({ ...field })
	}
	if (!fields || fields.length === 0) {
		return (
			<div className="component-container">
				<div className="flex justify-between items-center">
					<strong>プロパティセット</strong>
					{editable && (
						<button 
							onClick={addField}
							className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
						>
							+ フィールド追加
						</button>
					)}
				</div>
				<div className="mt-4 text-sm text-gray-500">
					このテンプレートにはプロパティが定義されていません
				</div>
				{editingField && (
					<FieldEditor
						field={editingField}
						onSave={saveField}
						onCancel={() => setEditingField(null)}
					/>
				)}
			</div>
		)
	}

	return (
		<div className="component-container">
			<div className="flex justify-between items-center">
				<strong>プロパティセット</strong>
				{editable && (
					<div className="flex gap-2">
						<button 
							onClick={() => setEditMode(!editMode)}
							className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
						>
							{editMode ? '編集終了' : '編集'}
						</button>
						<button 
							onClick={addField}
							className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
						>
							+ フィールド追加
						</button>
					</div>
				)}
			</div>
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
							<div className="flex justify-between items-center">
								<label className="text-sm font-medium">
									{field.label}
								</label>
								{editable && editMode && (
									<div className="flex gap-1">
										<button
											onClick={() => editField(field)}
											className="px-1 py-0.5 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600"
										>
											編集
										</button>
										<button
											onClick={() => deleteField(field.key)}
											className="px-1 py-0.5 text-xs bg-red-500 text-white rounded hover:bg-red-600"
										>
											削除
										</button>
									</div>
								)}
							</div>
							{field.input_type === 'textarea' && (
								<textarea
									placeholder={field.key}
									value={commonProps.value}
									onChange={commonProps.onChange}
									rows={3}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'text' && (
								<input
									type="text"
									placeholder={field.key}
									value={commonProps.value}
									onChange={commonProps.onChange}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'date' && (
								<input
									type="date"
									value={commonProps.value}
									onChange={commonProps.onChange}
									className="w-full p-2 border rounded text-sm"
								/>
							)}
							{field.input_type === 'select' && (
								<select
									value={commonProps.value}
									onChange={commonProps.onChange}
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
			{editingField && (
				<FieldEditor
					field={editingField}
					onSave={saveField}
					onCancel={() => setEditingField(null)}
				/>
			)}
		</div>
	)
}
