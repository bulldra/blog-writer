import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
	title: 'Blog Writer',
	description: 'AI-assisted blog writing tool',
}

export default function RootLayout({
	children,
}: {
	children: React.ReactNode
}) {
	return (
		<html lang="ja">
			<body>
				<div className="app-shell">
					<aside className="sidebar">
						<div className="brand">Blog Writer</div>
						<nav className="nav">
							<a href="/" className="nav-item">
								<span className="nav-icon" aria-hidden>
									✍️
								</span>
								<span className="nav-label">Writer</span>
							</a>
							<a href="/phrases" className="nav-item">
								<span className="nav-icon" aria-hidden>
									🔖
								</span>
								<span className="nav-label">いい回し</span>
							</a>
							<a href="/dictionary" className="nav-item">
								<span className="nav-icon" aria-hidden>
									📘
								</span>
								<span className="nav-label">辞書</span>
							</a>
							<a href="/templates" className="nav-item">
								<span className="nav-icon" aria-hidden>
									🧩
								</span>
								<span className="nav-label">
									プロンプトテンプレート
								</span>
							</a>
							<a href="/obsidian" className="nav-item">
								<span className="nav-icon" aria-hidden>
									📚
								</span>
								<span className="nav-label">Obsidian 管理</span>
							</a>
							<a
								href="/settings"
								className="nav-item"
								aria-label="設定">
								<span className="nav-icon" aria-hidden>
									<svg
										width="18"
										height="18"
										viewBox="0 0 24 24"
										fill="none"
										xmlns="http://www.w3.org/2000/svg">
										<path
											d="M12 15.5C13.933 15.5 15.5 13.933 15.5 12C15.5 10.067 13.933 8.5 12 8.5C10.067 8.5 8.5 10.067 8.5 12C8.5 13.933 10.067 15.5 12 15.5Z"
											fill="currentColor"
										/>
										<path
											d="M19.43 12.98C19.47 12.66 19.5 12.34 19.5 12C19.5 11.66 19.47 11.34 19.43 11.02L21.54 9.37C21.73 9.22 21.79 8.96 21.69 8.74L19.69 5.26C19.58 5.05 19.34 4.96 19.12 5.02L16.65 5.76C16.12 5.36 15.54 5.03 14.91 4.78L14.5 2.2C14.46 1.97 14.26 1.8 14.03 1.8H9.97C9.74 1.8 9.54 1.97 9.5 2.2L9.09 4.78C8.46 5.03 7.88 5.36 7.35 5.76L4.88 5.02C4.66 4.96 4.42 5.05 4.31 5.26L2.31 8.74C2.21 8.96 2.27 9.22 2.46 9.37L4.57 11.02C4.53 11.34 4.5 11.66 4.5 12C4.5 12.34 4.53 12.66 4.57 12.98L2.46 14.63C2.27 14.78 2.21 15.04 2.31 15.26L4.31 18.74C4.42 18.95 4.66 19.04 4.88 18.98L7.35 18.24C7.88 18.64 8.46 18.97 9.09 19.22L9.5 21.8C9.54 22.03 9.74 22.2 9.97 22.2H14.03C14.26 22.2 14.46 22.03 14.5 21.8L14.91 19.22C15.54 18.97 16.12 18.64 16.65 18.24L19.12 18.98C19.34 19.04 19.58 18.95 19.69 18.74L21.69 15.26C21.79 15.04 21.73 14.78 21.54 14.63L19.43 12.98ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17Z"
											fill="currentColor"
										/>
									</svg>
								</span>
								<span className="nav-label">設定</span>
							</a>
						</nav>
					</aside>
					<main className="content">{children}</main>
				</div>
			</body>
		</html>
	)
}
