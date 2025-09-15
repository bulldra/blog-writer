'use client'

import React, { useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Collapsible from './Collapsible'
import EyecatchGenerator from './EyecatchGenerator'

interface ResultDisplayProps {
	draft: string
	resultEditable: boolean
	showPreview: boolean
	commitWithGit: boolean
	eyecatchUrl: string
	eyecatchTheme: 'light' | 'dark'
	onDraftChange: (value: string) => void
	onResultEditableChange: (editable: boolean) => void
	onShowPreviewChange: (show: boolean) => void
	onCommitWithGitChange: (commit: boolean) => void
	onEyecatchThemeChange: (theme: 'light' | 'dark') => void
	onCopy: () => void
	onSave: () => void
	onGenerateEyecatch: () => void
	onDownloadEyecatchJpeg: () => void
}

export default function ResultDisplay({
	draft,
	resultEditable,
	showPreview,
	commitWithGit,
	eyecatchUrl,
	eyecatchTheme,
	onDraftChange,
	onResultEditableChange,
	onShowPreviewChange,
	onCommitWithGitChange,
	onEyecatchThemeChange,
	onCopy,
	onSave,
	onGenerateEyecatch,
	onDownloadEyecatchJpeg,
}: ResultDisplayProps) {
	const previewRef = useRef<HTMLDivElement | null>(null)
	const textRef = useRef<HTMLTextAreaElement | null>(null)

	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid #ddd',
				background: '#f8f8f8',
				display: 'grid',
				gap: 8,
			}}>
			<div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
				<label
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: 4,
					}}>
					<input
						type="checkbox"
						checked={resultEditable}
						onChange={(e) => onResultEditableChange(e.target.checked)}
					/>
					<span style={{ fontSize: 12 }}>編集モード</span>
				</label>
				<label
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: 4,
					}}>
					<input
						type="checkbox"
						checked={showPreview}
						onChange={(e) => onShowPreviewChange(e.target.checked)}
					/>
					<span style={{ fontSize: 12 }}>プレビュー表示</span>
				</label>
				<button onClick={onCopy} style={{ fontSize: 12 }}>
					コピー
				</button>
				<button onClick={onSave} style={{ fontSize: 12 }}>
					保存
				</button>
				<label
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: 6,
					}}>
					<input
						type="checkbox"
						checked={commitWithGit}
						onChange={(e) => onCommitWithGitChange(e.target.checked)}
					/>
					<span style={{ fontSize: 12 }}>Gitでコミット</span>
				</label>
				<a href="/drafts" style={{ textDecoration: 'none' }}>
					🗂️ 保存一覧
				</a>
			</div>

			<EyecatchGenerator
				eyecatchUrl={eyecatchUrl}
				eyecatchTheme={eyecatchTheme}
				draft={draft}
				onThemeChange={onEyecatchThemeChange}
				onGenerate={onGenerateEyecatch}
				onDownloadJpeg={onDownloadEyecatchJpeg}
			/>

			{showPreview && (
				<div
					ref={previewRef}
					style={{
						fontSize: 14,
						lineHeight: 1.6,
						background: '#fff',
						border: '1px solid #eee',
						padding: 12,
						height: 360,
						overflowY: 'auto',
					}}>
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
					style={{
						width: '100%',
						minHeight: 220,
						maxHeight: 440,
						overflow: 'scroll',
						fontSize: 14,
						lineHeight: 1.5,
						fontFamily:
							'ui-monospace, SFMono-Regular, Menlo, monospace',
						whiteSpace: 'pre-wrap',
					}}
				/>
			</Collapsible>
		</div>
	)
}