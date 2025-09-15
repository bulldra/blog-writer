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
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid #ddd',
				background: '#fff',
				display: 'grid',
				gap: 8,
			}}>
			<strong>編集を依頼</strong>
			<textarea
				value={instruction}
				onChange={(e) => onChange(e.target.value)}
				placeholder={
					'例）導入を簡潔に、要点を先に。段落間の論理接続を明確に。語尾の重複を避ける。'
				}
				rows={3}
				style={{ width: '100%' }}
			/>
			<div>
				<button onClick={onSubmit} disabled={isEditing}>
					{isEditing ? '編集中…' : '編集を依頼'}
				</button>
			</div>
		</div>
	)
}
