'use client'

import React, { useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Collapsible from './Collapsible'

interface ResultDisplayProps {
	draft: string
	resultEditable: boolean
	showPreview: boolean
	commitWithGit: boolean
	onDraftChange: (value: string) => void
	onResultEditableChange: (editable: boolean) => void
	onShowPreviewChange: (show: boolean) => void
	onCommitWithGitChange: (commit: boolean) => void
	onCopy: () => void
	onSave: () => void
}

export default function ResultDisplay({
	draft,
	resultEditable,
	showPreview,
	commitWithGit,
	onDraftChange,
	onResultEditableChange,
	onShowPreviewChange,
	onCommitWithGitChange,
	onCopy,
	onSave,
}: ResultDisplayProps) {
	const previewRef = useRef<HTMLDivElement | null>(null)
	const textRef = useRef<HTMLTextAreaElement | null>(null)

	return (
		<div className="result-container">
			<div className="result-controls">
				<label className="result-checkbox-label">
					<input
						type="checkbox"
						checked={resultEditable}
						onChange={(e) =>
							onResultEditableChange(e.target.checked)
						}
					/>
					<span className="text-xs">編集モード</span>
				</label>
				<label className="result-checkbox-label">
					<input
						type="checkbox"
						checked={showPreview}
						onChange={(e) => onShowPreviewChange(e.target.checked)}
					/>
					<span className="text-xs">プレビュー表示</span>
				</label>
				<button onClick={onCopy} className="text-xs">
					コピー
				</button>
				<button onClick={onSave} className="text-xs">
					保存
				</button>
				<label className="result-checkbox-label">
					<input
						type="checkbox"
						checked={commitWithGit}
						onChange={(e) =>
							onCommitWithGitChange(e.target.checked)
						}
					/>
					<span className="text-xs">Gitでコミット</span>
				</label>
				<a href="/drafts" className="result-drafts-link">
					🗂️ 保存一覧
				</a>
			</div>

			{/* Eyecatch 機能は一時的にオミット */}

			{showPreview && (
				<div ref={previewRef} className="result-preview">
					<ReactMarkdown remarkPlugins={[remarkGfm]}>
						{draft || ''}
					</ReactMarkdown>
				</div>
			)}

			<Collapsible
				title="ソース（Markdown）"
				previewText={draft}
				previewLines={3}
				contentHeight={260}>
				<textarea
					ref={textRef}
					value={draft}
					onChange={(e) => onDraftChange(e.target.value)}
					disabled={!resultEditable}
					className="result-textarea"
				/>
			</Collapsible>
		</div>
	)
}
