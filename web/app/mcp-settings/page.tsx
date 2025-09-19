'use client'

import { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface MCPServerConfig {
	name: string
	command: string
	args: string[]
	env: { [key: string]: string }
	enabled: boolean
}

interface MCPSettings {
	servers: { [key: string]: MCPServerConfig }
	enabled: boolean
}

interface MCPTool {
	name: string
	description?: string
	inputSchema?: Record<string, unknown>
}

export default function MCPSettingsPage() {
	const [settings, setSettings] = useState<MCPSettings>({
		servers: {},
		enabled: false,
	})
	const [saving, setSaving] = useState(false)
	const [testingServer, setTestingServer] = useState<string | null>(null)
	const [testResults, setTestResults] = useState<{ [key: string]: boolean }>({})
	const [serverTools, setServerTools] = useState<{ [key: string]: MCPTool[] }>({})
	const [showAddForm, setShowAddForm] = useState(false)
	const [newServer, setNewServer] = useState<{
		id: string
		config: MCPServerConfig
	}>({
		id: '',
		config: {
			name: '',
			command: 'npx',
			args: [],
			env: {},
			enabled: false,
		},
	})

	useEffect(() => {
		loadSettings()
	}, [])

	const loadSettings = async () => {
		try {
			const res = await fetch(`${API_BASE}/api/mcp/settings`)
			if (res.ok) {
				const data = await res.json()
				setSettings(data)
			}
		} catch (error) {
			console.error('Failed to load MCP settings:', error)
		}
	}

	const saveSettings = async () => {
		setSaving(true)
		try {
			const res = await fetch(`${API_BASE}/api/mcp/settings`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(settings),
			})
			if (res.ok) {
				console.log('MCP settings saved successfully')
			}
		} catch (error) {
			console.error('Failed to save MCP settings:', error)
		} finally {
			setSaving(false)
		}
	}

	const testConnection = async (serverId: string) => {
		setTestingServer(serverId)
		try {
			const res = await fetch(`${API_BASE}/api/mcp/test-connection`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ server_id: serverId }),
			})
			if (res.ok) {
				const result = await res.json()
				setTestResults(prev => ({ ...prev, [serverId]: result.success }))
			}
		} catch (error) {
			console.error('Failed to test connection:', error)
			setTestResults(prev => ({ ...prev, [serverId]: false }))
		} finally {
			setTestingServer(null)
		}
	}

	const loadServerTools = async (serverId: string) => {
		try {
			const res = await fetch(`${API_BASE}/api/mcp/servers/${serverId}/tools`)
			if (res.ok) {
				const result = await res.json()
				setServerTools(prev => ({ ...prev, [serverId]: result.tools }))
			}
		} catch (error) {
			console.error('Failed to load server tools:', error)
		}
	}

	const addServer = async () => {
		if (!newServer.id || !newServer.config.name) return

		try {
			const res = await fetch(`${API_BASE}/api/mcp/servers/${newServer.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newServer.config),
			})
			if (res.ok) {
				await loadSettings()
				setShowAddForm(false)
				setNewServer({
					id: '',
					config: {
						name: '',
						command: 'npx',
						args: [],
						env: {},
						enabled: false,
					},
				})
			}
		} catch (error) {
			console.error('Failed to add server:', error)
		}
	}

	const removeServer = async (serverId: string) => {
		try {
			const res = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
				method: 'DELETE',
			})
			if (res.ok) {
				await loadSettings()
			}
		} catch (error) {
			console.error('Failed to remove server:', error)
		}
	}

	const updateServerConfig = (
		serverId: string,
		key: keyof MCPServerConfig,
		value: string | string[] | boolean | Record<string, string>
	) => {
		setSettings(prev => ({
			...prev,
			servers: {
				...prev.servers,
				[serverId]: {
					...prev.servers[serverId],
					[key]: value,
				},
			},
		}))
	}

	const addEnvVar = (serverId: string, key: string, value: string) => {
		setSettings(prev => ({
			...prev,
			servers: {
				...prev.servers,
				[serverId]: {
					...prev.servers[serverId],
					env: {
						...prev.servers[serverId].env,
						[key]: value,
					},
				},
			},
		}))
	}

	const removeEnvVar = (serverId: string, key: string) => {
		const newEnv = { ...settings.servers[serverId].env }
		delete newEnv[key]
		setSettings(prev => ({
			...prev,
			servers: {
				...prev.servers,
				[serverId]: {
					...prev.servers[serverId],
					env: newEnv,
				},
			},
		}))
	}

	return (
		<main className="container mx-auto p-6 max-w-4xl">
			<h1 className="text-2xl font-bold mb-6">MCP 設定</h1>
			<p className="text-gray-600 mb-6">
				Model Context Protocol (MCP) サーバーの設定を管理します。
			</p>

			{/* Global Enable Toggle */}
			<div className="mb-6 p-4 border rounded">
				<label className="flex items-center gap-2">
					<input
						type="checkbox"
						checked={settings.enabled}
						onChange={e =>
							setSettings(prev => ({
								...prev,
								enabled: e.target.checked,
							}))
						}
					/>
					<span className="font-medium">MCP 統合を有効にする</span>
				</label>
			</div>

			{/* Server List */}
			<div className="space-y-4">
				{Object.entries(settings.servers).map(([serverId, server]) => (
					<div key={serverId} className="border rounded p-4">
						<div className="flex justify-between items-start mb-4">
							<div className="flex-1">
								<input
									type="text"
									value={server.name}
									onChange={e =>
										updateServerConfig(serverId, 'name', e.target.value)
									}
									className="text-lg font-medium w-full p-2 border rounded"
									placeholder="サーバー名"
								/>
								<p className="text-sm text-gray-600 mt-1">ID: {serverId}</p>
							</div>
							<div className="flex gap-2">
								<button
									onClick={() => testConnection(serverId)}
									disabled={testingServer === serverId}
									className="px-3 py-1 text-sm bg-blue-500 text-white rounded disabled:bg-gray-300"
								>
									{testingServer === serverId ? 'テスト中...' : '接続テスト'}
								</button>
								{server.enabled && (
									<button
										onClick={() => loadServerTools(serverId)}
										className="px-3 py-1 text-sm bg-green-500 text-white rounded"
									>
										ツール一覧
									</button>
								)}
								<button
									onClick={() => removeServer(serverId)}
									className="px-3 py-1 text-sm bg-red-500 text-white rounded"
								>
									削除
								</button>
							</div>
						</div>

						{/* Connection Test Result */}
						{serverId in testResults && (
							<div
								className={`mb-4 p-2 rounded text-sm ${
									testResults[serverId]
										? 'bg-green-100 text-green-800'
										: 'bg-red-100 text-red-800'
								}`}
							>
								接続テスト:{' '}
								{testResults[serverId] ? '成功' : '失敗'}
							</div>
						)}

						{/* Server Config */}
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
							<div>
								<label className="block text-sm font-medium mb-1">
									コマンド
								</label>
								<input
									type="text"
									value={server.command}
									onChange={e =>
										updateServerConfig(serverId, 'command', e.target.value)
									}
									className="w-full p-2 border rounded"
									placeholder="npx"
								/>
							</div>
							<div>
								<label className="block text-sm font-medium mb-1">
									引数 (1行に1つ)
								</label>
								<textarea
									value={server.args.join('\n')}
									onChange={e =>
										updateServerConfig(
											serverId,
											'args',
											e.target.value.split('\n').filter(Boolean)
										)
									}
									className="w-full p-2 border rounded"
									rows={3}
								/>
							</div>
						</div>

						{/* Environment Variables */}
						<div className="mb-4">
							<label className="block text-sm font-medium mb-2">
								環境変数
							</label>
							<div className="space-y-2">
								{Object.entries(server.env).map(([key, value]) => (
									<div key={key} className="flex gap-2">
										<input
											type="text"
											value={key}
											readOnly
											className="w-1/3 p-2 border rounded bg-gray-50"
										/>
										<input
											type="password"
											value={value}
											onChange={e =>
												addEnvVar(serverId, key, e.target.value)
											}
											className="w-1/2 p-2 border rounded"
										/>
										<button
											onClick={() => removeEnvVar(serverId, key)}
											className="px-3 py-1 text-sm bg-red-500 text-white rounded"
										>
											削除
										</button>
									</div>
								))}
								<div className="flex gap-2">
									<input
										type="text"
										placeholder="変数名"
										className="w-1/3 p-2 border rounded"
										onKeyDown={e => {
											if (e.key === 'Enter') {
												const key = e.currentTarget.value.trim()
												if (key) {
													addEnvVar(serverId, key, '')
													e.currentTarget.value = ''
												}
											}
										}}
									/>
									<span className="flex items-center text-gray-500">
										Enterで追加
									</span>
								</div>
							</div>
						</div>

						{/* Enable Toggle */}
						<label className="flex items-center gap-2">
							<input
								type="checkbox"
								checked={server.enabled}
								onChange={e =>
									updateServerConfig(serverId, 'enabled', e.target.checked)
								}
							/>
							<span>このサーバーを有効にする</span>
						</label>

						{/* Tools List */}
						{serverTools[serverId] && (
							<div className="mt-4 p-3 bg-gray-50 rounded">
								<h4 className="font-medium mb-2">利用可能なツール:</h4>
								<ul className="space-y-1">
									{serverTools[serverId].map(tool => (
										<li key={tool.name} className="text-sm">
											<strong>{tool.name}</strong>
											{tool.description && (
												<span className="text-gray-600">
													{' '}
													- {tool.description}
												</span>
											)}
										</li>
									))}
								</ul>
							</div>
						)}
					</div>
				))}
			</div>

			{/* Add Server Form */}
			{showAddForm && (
				<div className="mt-6 p-4 border rounded bg-gray-50">
					<h3 className="text-lg font-medium mb-4">新しいサーバーを追加</h3>
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
						<div>
							<label className="block text-sm font-medium mb-1">
								サーバーID
							</label>
							<input
								type="text"
								value={newServer.id}
								onChange={e =>
									setNewServer(prev => ({ ...prev, id: e.target.value }))
								}
								className="w-full p-2 border rounded"
								placeholder="例: my-mcp-server"
							/>
						</div>
						<div>
							<label className="block text-sm font-medium mb-1">
								サーバー名
							</label>
							<input
								type="text"
								value={newServer.config.name}
								onChange={e =>
									setNewServer(prev => ({
										...prev,
										config: { ...prev.config, name: e.target.value },
									}))
								}
								className="w-full p-2 border rounded"
								placeholder="例: My MCP Server"
							/>
						</div>
					</div>
					<div className="flex gap-2">
						<button
							onClick={addServer}
							className="px-4 py-2 bg-blue-500 text-white rounded"
						>
							追加
						</button>
						<button
							onClick={() => setShowAddForm(false)}
							className="px-4 py-2 bg-gray-500 text-white rounded"
						>
							キャンセル
						</button>
					</div>
				</div>
			)}

			{/* Add Server Button */}
			{!showAddForm && (
				<button
					onClick={() => setShowAddForm(true)}
					className="mt-6 px-4 py-2 bg-green-500 text-white rounded"
				>
					サーバーを追加
				</button>
			)}

			{/* Save Button */}
			<div className="mt-6 flex justify-end">
				<button
					onClick={saveSettings}
					disabled={saving}
					className="px-6 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
				>
					{saving ? '保存中...' : '設定を保存'}
				</button>
			</div>
		</main>
	)
}