'use client'

import { useTheme } from './ThemeProvider'

export default function ThemeToggle() {
	const { theme, toggleTheme } = useTheme()

	return (
		<div
			style={{
				display: 'flex',
				alignItems: 'center',
				gap: 8,
				marginTop: 16,
			}}>
			<label htmlFor="theme-toggle">ダークモード</label>
			<button
				id="theme-toggle"
				onClick={toggleTheme}
				style={{
					display: 'flex',
					alignItems: 'center',
					gap: 6,
					padding: '8px 12px',
					border: '1px solid var(--border-color)',
					borderRadius: '8px',
					background: 'var(--bg-secondary)',
					color: 'var(--text-color)',
					cursor: 'pointer',
					fontSize: '14px',
					minWidth: '100px',
					justifyContent: 'center',
				}}
				aria-label={`${
					theme === 'dark' ? 'ライト' : 'ダーク'
				}モードに切り替え`}>
				<span style={{ fontSize: '16px' }}>
					{theme === 'dark' ? '🌙' : '☀️'}
				</span>
				<span>{theme === 'dark' ? 'ダーク' : 'ライト'}</span>
			</button>
		</div>
	)
}