'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { setCookie } from '../../utils/cookies'

export default function AuthCallback() {
	const router = useRouter()

	useEffect(() => {
		const handleCallback = async () => {
			try {
				const response = await fetch(
					'/api/auth/callback' + window.location.search
				)

				if (response.ok) {
					const data = await response.json()

					// トークンをCookieに保存
					setCookie('auth_token', data.access_token, {
						days: 7,
						secure: process.env.NODE_ENV === 'production',
						sameSite: 'lax',
					})

					// メインページにリダイレクト
					router.push('/')
				} else {
					throw new Error('認証に失敗しました')
				}
			} catch (error) {
				console.error('Auth callback error:', error)
				router.push('/?error=auth_failed')
			}
		}

		handleCallback()
	}, [router])

	return (
		<div className="flex items-center justify-center min-h-screen">
			<div className="text-center">
				<div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
				<p className="mt-4 text-lg">認証処理中...</p>
			</div>
		</div>
	)
}
