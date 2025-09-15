'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

export type ComboOption = {
	value: string
	label?: string
}

type Props = {
	value: string
	onChange: (v: string) => void
	options: Array<string | ComboOption>
	placeholder?: string
	allowCustom?: boolean
	maxItems?: number
	className?: string
	onSelect?: (v: string) => void
}

export default function ComboBox({
	value,
	onChange,
	options,
	placeholder,
	allowCustom = false,
	maxItems = 200,
	className,
	onSelect,
}: Props) {
	const [open, setOpen] = useState(false)
	const [active, setActive] = useState(-1)
	const [input, setInput] = useState(value)
	const rootRef = useRef<HTMLDivElement | null>(null)
	const listRef = useRef<HTMLUListElement | null>(null)

	useEffect(() => setInput(value), [value])

	const norm = useMemo<ComboOption[]>(
		() =>
			options.map((o) =>
				typeof o === 'string'
					? { value: o, label: o }
					: { ...o, label: o.label ?? o.value }
			),
		[options]
	)

	const filtered = useMemo(() => {
		const q = input.trim().toLowerCase()
		const arr = q
			? norm.filter(
					(o) =>
						(o.label ?? o.value).toLowerCase().includes(q) ||
						o.value.toLowerCase().includes(q)
			  )
			: norm
		return arr.slice(0, maxItems)
	}, [norm, input, maxItems])

	useEffect(() => {
		const onDocClick = (e: MouseEvent) => {
			if (!rootRef.current) return
			if (!rootRef.current.contains(e.target as Node)) setOpen(false)
		}
		document.addEventListener('mousedown', onDocClick)
		return () => document.removeEventListener('mousedown', onDocClick)
	}, [])

	useEffect(() => {
		if (!listRef.current) return
		const el = listRef.current.children[active] as HTMLLIElement | undefined
		if (el) el.scrollIntoView({ block: 'nearest' })
	}, [active])

	const commit = (v: string) => {
		onChange(v)
		setInput(v)
		setOpen(false)
		setActive(-1)
		onSelect?.(v)
	}

	return (
		<div
			ref={rootRef}
			className={`combo-box ${className || ''}`}>
			<input
				placeholder={placeholder}
				value={input}
				onChange={(e) => {
					setInput(e.target.value)
					setOpen(true)
					setActive(-1)
				}}
				onFocus={() => setOpen(true)}
				onKeyDown={(e) => {
					if (e.key === 'ArrowDown') {
						e.preventDefault()
						setOpen(true)
						setActive((i) => Math.min(i + 1, filtered.length - 1))
					} else if (e.key === 'ArrowUp') {
						e.preventDefault()
						setActive((i) => Math.max(i - 1, -1))
					} else if (e.key === 'Enter') {
						e.preventDefault()
						if (active >= 0 && active < filtered.length)
							commit(filtered[active].value)
						else if (allowCustom) commit(input)
					} else if (e.key === 'Escape') {
						setOpen(false)
					}
				}}
				className="combo-input"
			/>
			{open && (
				<ul
					ref={listRef}
					className="combo-dropdown">
					{filtered.map((o, idx) => (
						<li
							key={`${o.value}-${idx}`}
							onMouseDown={(e) => e.preventDefault()}
							onClick={() => commit(o.value)}
							onMouseEnter={() => setActive(idx)}
							className={`combo-option ${idx === active ? 'selected' : ''}`}
							title={o.value}>
							{o.label ?? o.value}
						</li>
					))}
					{allowCustom &&
						input.trim() &&
						!filtered.some((o) => o.value === input.trim()) && (
							<li
								onMouseDown={(e) => e.preventDefault()}
								onClick={() => commit(input.trim())}
								className="combo-custom-option">
								「{input.trim()}」で検索
							</li>
						)}
				</ul>
			)}
		</div>
	)
}
