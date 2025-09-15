'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
	theme: Theme
	setTheme: (theme: Theme) => void
	toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
	const [theme, setTheme] = useState<Theme>('light')
	const [mounted, setMounted] = useState(false)

	useEffect(() => {
		setMounted(true)
		const saved = localStorage.getItem('theme') as Theme | null
		if (saved) {
			setTheme(saved)
		} else {
			// システムのダークモード設定を確認
			const prefersDark = window.matchMedia(
				'(prefers-color-scheme: dark)'
			).matches
			setTheme(prefersDark ? 'dark' : 'light')
		}
	}, [])

	useEffect(() => {
		if (!mounted) return
		localStorage.setItem('theme', theme)
		document.documentElement.setAttribute('data-theme', theme)
	}, [theme, mounted])

	const toggleTheme = () => {
		setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'))
	}

	// ハイドレーション不一致を防ぐため、マウント前は何も表示しない
	if (!mounted) {
		return null
	}

	return (
		<ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
			{children}
		</ThemeContext.Provider>
	)
}

export function useTheme() {
	const context = useContext(ThemeContext)
	if (context === undefined) {
		throw new Error('useTheme must be used within a ThemeProvider')
	}
	return context
}