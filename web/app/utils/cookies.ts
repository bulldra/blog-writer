export type SameSite = 'lax' | 'strict' | 'none'

export function getCookie(name: string): string | undefined {
	if (typeof document === 'undefined') return undefined
	const prefix = `${name}=`
	const pair = document.cookie
		.split('; ')
		.find((row) => row.startsWith(prefix))
	if (!pair) return undefined
	const value = pair.slice(prefix.length)
	try {
		return decodeURIComponent(value)
	} catch {
		return value
	}
}

export function setCookie(
	name: string,
	value: string,
	opts?: {
		days?: number
		secure?: boolean
		sameSite?: SameSite
		path?: string
	}
): void {
	if (typeof document === 'undefined') return
	const days = opts?.days ?? 7
	const secure = opts?.secure ?? false
	const sameSite = (opts?.sameSite ?? 'lax').toLowerCase() as SameSite
	const path = opts?.path ?? '/'

	const encoded = encodeURIComponent(value)
	let cookie = `${name}=${encoded}; Path=${path};`
	if (Number.isFinite(days)) {
		const d = new Date()
		d.setTime(d.getTime() + (days as number) * 24 * 60 * 60 * 1000)
		cookie += ` Expires=${d.toUTCString()};`
	}
	if (secure) cookie += ' Secure;'
	const s =
		sameSite === 'none' ? 'None' : sameSite === 'strict' ? 'Strict' : 'Lax'
	cookie += ` SameSite=${s}`
	document.cookie = cookie
}

export function deleteCookie(name: string, path: string = '/'): void {
	if (typeof document === 'undefined') return
	document.cookie = `${name}=; Path=${path}; Expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`
}
