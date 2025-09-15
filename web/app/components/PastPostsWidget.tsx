'use client'

import React from 'react'

type SavedPost = { filename: string; title: string }

interface PastPostsWidgetProps {
	savedPosts: SavedPost[]
	selectedPost: string
	onPostSelect: (filename: string) => void
}

export default function PastPostsWidget({
	savedPosts,
	selectedPost,
	onPostSelect,
}: PastPostsWidgetProps) {
	return (
		<div
			style={{
				marginTop: 8,
				padding: 8,
				border: '1px solid var(--border-color)',
				background: 'var(--bg-secondary)',
			}}>
			<strong>過去記事コンテキスト（任意）</strong>
			<div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
				<select
					value={selectedPost}
					onChange={(e) => onPostSelect(e.target.value)}
					style={{ flex: 1 }}>
					<option value="">（選択しない）</option>
					{savedPosts.map((p) => (
						<option key={p.filename} value={p.filename}>
							{p.title}
						</option>
					))}
				</select>
				{selectedPost && (
					<span style={{ fontSize: 12, color: 'var(--text-color)' }}>
						本文先頭を一部（最大4000文字）参照に送信します
					</span>
				)}
			</div>
		</div>
	)
}