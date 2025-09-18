import './globals.css'
import type { Metadata } from 'next'
import { ThemeProvider } from './components/ThemeProvider'
import { AuthProvider } from './components/auth/AuthProvider'
import LoginButton from './components/auth/LoginButton'
import SidebarNav from './components/layout/SidebarNav'

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
				<ThemeProvider>
					<AuthProvider>
						<div className="app-shell">
							<aside className="sidebar">
								<div className="brand">Blog Writer</div>
								<SidebarNav />
								<div className="sidebar-footer">
									<LoginButton />
								</div>
							</aside>
							<main className="content">{children}</main>
						</div>
					</AuthProvider>
				</ThemeProvider>
			</body>
		</html>
	)
}
