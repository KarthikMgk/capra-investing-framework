import { useState, useRef, useEffect } from "react"
import { Search } from "lucide-react"
import { useNavigate } from "@tanstack/react-router"
import { Input } from "@/components/ui/input"
import { useStockList } from "./useStockScore"
import type { StockListItem } from "@/shared/types/stock"

interface Props {
  initialSymbol?: string
}

export function StockSearch({ initialSymbol = "" }: Props) {
  const { data } = useStockList()
  const [query, setQuery] = useState(initialSymbol)
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  const items: StockListItem[] = data?.items ?? []
  const q = query.toLowerCase()
  const filtered = q
    ? items.filter(
        (i) =>
          i.stock_symbol.toLowerCase().includes(q) ||
          i.name.toLowerCase().includes(q),
      )
    : []

  function pick(item: StockListItem) {
    setQuery(item.stock_symbol)
    setOpen(false)
    navigate({ to: "/stock/$symbol", params: { symbol: item.stock_symbol } })
  }

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  return (
    <div ref={ref} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search Nifty 50 by name or symbol…"
          className="pl-9"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => query && setOpen(true)}
        />
      </div>

      {open && filtered.length > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg">
          {filtered.slice(0, 8).map((item) => (
            <button
              key={item.stock_symbol}
              className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent text-left"
              onMouseDown={() => pick(item)}
            >
              <span>
                <span className="font-mono font-semibold">{item.stock_symbol}</span>
                <span className="text-muted-foreground ml-2">{item.name}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
