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
		<div className="component-container">
			<strong>過去記事コンテキスト（任意）</strong>
			<div className="flex-row mt-6">
				<select
					value={selectedPost}
					onChange={(e) => onPostSelect(e.target.value)}
					className="flex-1">
					<option value="">（選択しない）</option>
					{savedPosts.map((p) => (
						<option key={p.filename} value={p.filename}>
							{p.title}
						</option>
					))}
				</select>
				{selectedPost && (
					<span className="text-xs text-secondary">
						本文先頭を一部（最大4000文字）参照に送信します
					</span>
				)}
			</div>
		</div>
	)
}