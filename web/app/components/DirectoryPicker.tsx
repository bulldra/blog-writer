'use client'

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface DirEntry {
	name: string
	path: string
	is_dir: boolean
}

interface ListResponse {
	path: string
	parent: string | null
	entries: DirEntry[]
}

interface DirectoryPickerProps {
	initialPath?: string
	onSelect: (path: string) => void
	onClose: () => void
}

export default function DirectoryPicker({
	initialPath,
	onSelect,
	onClose,
}: DirectoryPickerProps) {
	const [currentPath, setCurrentPath] = useState<string>(initialPath || '')
	const [entries, setEntries] = useState<DirEntry[]>([])
	const [parent, setParent] = useState<string | null>(null)
	const [loading, setLoading] = useState<boolean>(false)
	const [error, setError] = useState<string>('')

	useEffect(() => {
		if (initialPath) {
			load(initialPath)
		} else {
			fetch(`${API_BASE}/api/fs/home`)
				.then((r) => r.json())
				.then((j) => load(j.home))
				.catch(() => setError('ホームディレクトリの取得に失敗しました'))
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [])

	const load = async (path: string) => {
		setLoading(true)
		setError('')
		try {
			const res = await fetch(
				`${API_BASE}/api/fs/list?path=${encodeURIComponent(path)}`
			)
			if (!res.ok) {
				const msg = `ディレクトリの取得に失敗しました (status ${res.status})`
				setError(msg)
				setEntries([])
				setParent(null)
				return
			}
			const data: ListResponse = await res.json()
			setCurrentPath(data.path)
			setParent(data.parent)
			setEntries(data.entries)
		} catch {
			setError('ディレクトリの取得に失敗しました（ネットワーク）')
			setEntries([])
			setParent(null)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="fixed inset-0 flex items-center justify-center bg-black/30 z-50">
			<div className="bg-white text-black rounded shadow w-[720px] max-w-[95vw]">
				<div className="p-3 border-b flex items-center justify-between">
					<strong>ディレクトリを選択</strong>
					<button
						onClick={onClose}
						className="text-sm px-2 py-1 border rounded">
						閉じる
					</button>
				</div>
				<div className="p-3 border-b text-sm">
					<div className="flex items-center gap-2">
						<span className="text-gray-600">現在:</span>
						<code className="px-2 py-1 bg-gray-100 rounded break-all">
							{currentPath || '(未選択)'}
						</code>
						<div className="flex-1" />
						<button
							onClick={() => parent && load(parent)}
							disabled={!parent || loading}
							className="px-2 py-1 border rounded disabled:opacity-50">
							一つ上へ
						</button>
						<button
							onClick={() => onSelect(currentPath)}
							disabled={!currentPath}
							className="ml-2 px-3 py-1 bg-blue-600 text-white rounded disabled:bg-gray-300">
							このフォルダを選択
						</button>
					</div>
				</div>
				<div className="p-3 h-[360px] overflow-auto">
					{error && (
						<div className="text-red-600 text-sm mb-2">{error}</div>
					)}
					{loading ? (
						<div className="text-sm text-gray-600">
							読み込み中...
						</div>
					) : (
						<ul className="divide-y">
							{entries.map((ent) => (
								<li
									key={ent.path}
									className="py-2 flex items-center justify-between">
									<button
										onClick={() => load(ent.path)}
										className="text-left flex-1 hover:underline"
										title={ent.path}>
										📁 {ent.name}
									</button>
									<button
										onClick={() => onSelect(ent.path)}
										className="ml-2 px-2 py-1 text-xs border rounded">
										選択
									</button>
								</li>
							))}
							{entries.length === 0 && (
								<li className="py-2 text-sm text-gray-600">
									ディレクトリがありません
								</li>
							)}
						</ul>
					)}
				</div>
			</div>
		</div>
	)
}
