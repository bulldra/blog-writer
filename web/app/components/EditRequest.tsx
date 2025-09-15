'use client'

type Props = {
	instruction: string
	isEditing: boolean
	onChange: (v: string) => void
	onSubmit: () => void
}

export default function EditRequest({
	instruction,
	isEditing,
	onChange,
	onSubmit,
}: Props) {
	return (
		<div className="edit-request-container">
			<strong>編集を依頼</strong>
			<textarea
				value={instruction}
				onChange={(e) => onChange(e.target.value)}
				placeholder={
					'例）導入を簡潔に、要点を先に。段落間の論理接続を明確に。語尾の重複を避ける。'
				}
				rows={3}
				className="edit-request-textarea"
			/>
			<div>
				<button onClick={onSubmit} disabled={isEditing}>
					{isEditing ? '編集中…' : '編集を依頼'}
				</button>
			</div>
		</div>
	)
}
