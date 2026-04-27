type Signal = "strong_buy" | "buy" | "hold" | "sell" | "strong_sell" | null | undefined

interface SignalConfig {
  label: string
  indicator: string
  className: string
}

const SIGNAL_MAP: Record<string, SignalConfig> = {
  strong_buy: {
    label: "Strong Buy",
    indicator: "▲▲",
    className:
      "bg-emerald-500/15 text-emerald-700 border border-emerald-300 dark:text-emerald-400 dark:border-emerald-800",
  },
  buy: {
    label: "Accumulate",
    indicator: "▲",
    className:
      "bg-teal-500/15 text-teal-700 border border-teal-300 dark:text-teal-400 dark:border-teal-800",
  },
  hold: {
    label: "Hold",
    indicator: "—",
    className:
      "bg-zinc-100 text-zinc-600 border border-zinc-300 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-600",
  },
  sell: {
    label: "Watch",
    indicator: "▼",
    className:
      "bg-amber-500/15 text-amber-700 border border-amber-300 dark:text-amber-400 dark:border-amber-800",
  },
  strong_sell: {
    label: "Reduce",
    indicator: "▼▼",
    className:
      "bg-red-500/15 text-red-700 border border-red-300 dark:text-red-400 dark:border-red-800",
  },
}

const PENDING: SignalConfig = {
  label: "Pending",
  indicator: "·",
  className:
    "bg-zinc-50 text-zinc-400 border border-dashed border-zinc-300 dark:bg-zinc-900 dark:border-zinc-700",
}

interface Props {
  signal: Signal
}

export function SignalBadge({ signal }: Props) {
  const config = (signal && SIGNAL_MAP[signal]) ?? PENDING

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums tracking-wide ${config.className}`}
    >
      <span className="text-[10px] leading-none">{config.indicator}</span>
      {config.label}
    </span>
  )
}
