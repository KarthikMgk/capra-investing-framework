import { createFileRoute } from "@tanstack/react-router"
import { PortfolioView } from "@/features/portfolio/PortfolioView"

export const Route = createFileRoute("/_layout/")({
  component: PortfolioView,
  head: () => ({
    meta: [{ title: "Portfolio - Capra Investing" }],
  }),
})
