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

interface Props {
	serverId: string
	toolName: string
	arguments: Record<string, unknown>
	onChange: (update: Partial<{
		serverId: string
		toolName: string
		arguments: Record<string, unknown>
	}>) => void
}

export default function MCPWidget(props: Props) {
	const [mcpSettings, setMcpSettings] = useState<MCPSettings>({
		servers: {},
		enabled: false,
	})
	const [availableTools, setAvailableTools] = useState<{ [key: string]: MCPTool[] }>({})
	const [loading, setLoading] = useState(false)
	const [result, setResult] = useState<string>('')
	const [argumentsInput, setArgumentsInput] = useState<string>('')

	useEffect(() => {
		loadMcpSettings()
	}, [])

	useEffect(() => {
		// Initialize arguments input with current arguments
		setArgumentsInput(JSON.stringify(props.arguments, null, 2))
	}, [props.arguments])

	useEffect(() => {
		if (props.serverId && mcpSettings.servers[props.serverId]?.enabled) {
			loadServerTools(props.serverId)
		}
	}, [props.serverId, mcpSettings])

	const loadMcpSettings = async () => {
		try {
			const res = await fetch(`${API_BASE}/api/mcp/settings`)
			if (res.ok) {
				const data = await res.json()
				setMcpSettings(data)
			}
		} catch (error) {
			console.error('Failed to load MCP settings:', error)
		}
	}

	const loadServerTools = async (serverId: string) => {
		try {
			const res = await fetch(`${API_BASE}/api/mcp/servers/${serverId}/tools`)
			if (res.ok) {
				const result = await res.json()
				setAvailableTools(prev => ({ ...prev, [serverId]: result.tools }))
			}
		} catch (error) {
			console.error('Failed to load server tools:', error)
		}
	}

	const callTool = async () => {
		if (!props.serverId || !props.toolName) return

		setLoading(true)
		try {
			const res = await fetch(`${API_BASE}/api/mcp/call-tool`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					server_id: props.serverId,
					tool_name: props.toolName,
					arguments: props.arguments,
				}),
			})
			if (res.ok) {
				const result = await res.json()
				setResult(result.result || '結果なし')
			} else {
				setResult('ツール呼び出しに失敗しました')
			}
		} catch (error) {
			console.error('Failed to call tool:', error)
			setResult('エラーが発生しました')
		} finally {
			setLoading(false)
		}
	}

	const updateArguments = () => {
		try {
			const parsed = JSON.parse(argumentsInput)
			props.onChange({ arguments: parsed })
		} catch (error) {
			console.error('Invalid JSON:', error)
		}
	}

	const enabledServers = Object.entries(mcpSettings.servers)
		.filter(([, server]) => server.enabled)

	return (
		<div className="component-container">
			<strong>MCP クライアント</strong>
			<div className="mt-4 grid gap-3 text-sm">
				{!mcpSettings.enabled && (
					<div className="text-red-600 text-xs">
						MCP統合が無効になっています。設定ページで有効にしてください。
					</div>
				)}

				{mcpSettings.enabled && enabledServers.length === 0 && (
					<div className="text-yellow-600 text-xs">
						有効なMCPサーバーがありません。設定ページでサーバーを追加してください。
					</div>
				)}

				{mcpSettings.enabled && enabledServers.length > 0 && (
					<>
						<label className="grid gap-1">
							<span className="text-xs text-gray-600">MCPサーバー</span>
							<select
								value={props.serverId}
								onChange={(e) => props.onChange({ serverId: e.target.value })}
								className="p-2 border rounded"
							>
								<option value="">サーバーを選択</option>
								{enabledServers.map(([serverId, server]) => (
									<option key={serverId} value={serverId}>
										{server.name} ({serverId})
									</option>
								))}
							</select>
						</label>

						{props.serverId && availableTools[props.serverId] && (
							<label className="grid gap-1">
								<span className="text-xs text-gray-600">ツール</span>
								<select
									value={props.toolName}
									onChange={(e) => props.onChange({ toolName: e.target.value })}
									className="p-2 border rounded"
								>
									<option value="">ツールを選択</option>
									{availableTools[props.serverId].map(tool => (
										<option key={tool.name} value={tool.name}>
											{tool.name}
											{tool.description && ` - ${tool.description}`}
										</option>
									))}
								</select>
							</label>
						)}

						{props.toolName && (
							<div className="grid gap-1">
								<label className="flex justify-between items-center">
									<span className="text-xs text-gray-600">引数 (JSON)</span>
									<button
										onClick={updateArguments}
										className="px-2 py-1 text-xs bg-blue-500 text-white rounded"
									>
										適用
									</button>
								</label>
								<textarea
									value={argumentsInput}
									onChange={(e) => setArgumentsInput(e.target.value)}
									className="p-2 border rounded font-mono text-xs"
									rows={6}
									placeholder='{"key": "value"}'
								/>
							</div>
						)}

						{props.serverId && props.toolName && (
							<button
								onClick={callTool}
								disabled={loading}
								className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
							>
								{loading ? 'ツール実行中...' : 'ツールを実行'}
							</button>
						)}

						{result && (
							<div className="mt-4 p-3 bg-gray-50 rounded">
								<h4 className="font-medium mb-2 text-xs text-gray-600">実行結果:</h4>
								<pre className="text-xs whitespace-pre-wrap">{result}</pre>
							</div>
						)}
					</>
				)}

				{mcpSettings.enabled && (
					<div className="text-xs text-gray-500 border-t pt-2">
						<p>
							<a
								href="/mcp-settings"
								target="_blank"
								className="text-blue-500 hover:underline"
							>
								MCP設定ページ
							</a>
							で新しいサーバーを追加できます。
						</p>
					</div>
				)}
			</div>
		</div>
	)
}