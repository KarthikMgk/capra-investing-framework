"""
Framework constants for the Multi-Layer Capital Allocation System v3.0.

All numeric parameters live here — computation_engine.py contains zero literals.
Values marked "MVP default" should be calibrated after backtesting.
"""

# ── Nifty 50 universe ─────────────────────────────────────────────────────────

NIFTY_50_SYMBOLS: list[str] = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
    "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
    "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT",
    "LTIM", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN",
    "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
    "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO", "WIPRO",
]

NIFTY_50_NAMES: dict[str, str] = {
    "ADANIENT":   "Adani Enterprises Ltd",
    "ADANIPORTS": "Adani Ports & SEZ Ltd",
    "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
    "ASIANPAINT": "Asian Paints Ltd",
    "AXISBANK":   "Axis Bank Ltd",
    "BAJAJ-AUTO": "Bajaj Auto Ltd",
    "BAJFINANCE": "Bajaj Finance Ltd",
    "BAJAJFINSV": "Bajaj Finserv Ltd",
    "BPCL":       "Bharat Petroleum Corporation Ltd",
    "BHARTIARTL": "Bharti Airtel Ltd",
    "BRITANNIA":  "Britannia Industries Ltd",
    "CIPLA":      "Cipla Ltd",
    "COALINDIA":  "Coal India Ltd",
    "DIVISLAB":   "Divi's Laboratories Ltd",
    "DRREDDY":    "Dr. Reddy's Laboratories Ltd",
    "EICHERMOT":  "Eicher Motors Ltd",
    "GRASIM":     "Grasim Industries Ltd",
    "HCLTECH":    "HCL Technologies Ltd",
    "HDFCBANK":   "HDFC Bank Ltd",
    "HDFCLIFE":   "HDFC Life Insurance Co Ltd",
    "HEROMOTOCO": "Hero MotoCorp Ltd",
    "HINDALCO":   "Hindalco Industries Ltd",
    "HINDUNILVR": "Hindustan Unilever Ltd",
    "ICICIBANK":  "ICICI Bank Ltd",
    "ITC":        "ITC Ltd",
    "INDUSINDBK": "IndusInd Bank Ltd",
    "INFY":       "Infosys Ltd",
    "JSWSTEEL":   "JSW Steel Ltd",
    "KOTAKBANK":  "Kotak Mahindra Bank Ltd",
    "LT":         "Larsen & Toubro Ltd",
    "LTIM":       "LTIMindtree Ltd",
    "M&M":        "Mahindra & Mahindra Ltd",
    "MARUTI":     "Maruti Suzuki India Ltd",
    "NESTLEIND":  "Nestle India Ltd",
    "NTPC":       "NTPC Ltd",
    "ONGC":       "Oil & Natural Gas Corporation Ltd",
    "POWERGRID":  "Power Grid Corporation of India Ltd",
    "RELIANCE":   "Reliance Industries Ltd",
    "SBILIFE":    "SBI Life Insurance Co Ltd",
    "SHRIRAMFIN": "Shriram Finance Ltd",
    "SBIN":       "State Bank of India",
    "SUNPHARMA":  "Sun Pharmaceutical Industries Ltd",
    "TCS":        "Tata Consultancy Services Ltd",
    "TATACONSUM": "Tata Consumer Products Ltd",
    "TATAMOTORS": "Tata Motors Ltd",
    "TATASTEEL":  "Tata Steel Ltd",
    "TECHM":      "Tech Mahindra Ltd",
    "TITAN":      "Titan Company Ltd",
    "ULTRACEMCO": "UltraTech Cement Ltd",
    "WIPRO":      "Wipro Ltd",
}

# ── Factor weights (Part 5, Framework v3.0) ───────────────────────────────────
# 9 factors, weights sum to exactly 1.0.
# ⚠️  DATA GAP (MVP): usd_lens, gold_lens, sector_strength have no live data
#     source yet. Score service feeds them 0.0 (neutral) until Kite or an
#     external feed provides Nifty/USD, Nifty/Gold, and sector index prices.

FACTOR_WEIGHTS: dict[str, float] = {
    "liquidity":        0.25,  # RBI system liquidity — highest weight
    "rates":            0.15,  # Repo rate trend
    "valuation":        0.15,  # PE / PB (lower = cheaper = positive)
    "credit_growth":    0.10,  # Bank credit growth YoY
    "relative_strength":0.10,  # Stock vs Nifty 6M return ratio
    "earnings":         0.10,  # EPS growth + ROE quality
    "usd_lens":         0.05,  # Nifty / USD — global capital flow proxy ⚠️
    "gold_lens":        0.05,  # Nifty / Gold — inflation-adjusted lens ⚠️
    "sector_strength":  0.05,  # Sector index vs Nifty 50 ⚠️
}

# ── Decision matrix bucketing thresholds ──────────────────────────────────────
# Classify composite_score, ROC (momentum), and asymmetry_index into buckets,
# then look up the 3-tuple in DECISION_MATRIX.

SCORE_HIGH_THRESHOLD: float = 0.5    # score > 0.5  → "high"
SCORE_LOW_THRESHOLD: float = -0.5    # score < -0.5 → "low"
                                      # else         → "mid"

MOMENTUM_UP_THRESHOLD: float = 0.05  # ROC > 0.05  → "up"   (MVP default)
MOMENTUM_DOWN_THRESHOLD: float = -0.05  # ROC < -0.05 → "down"
                                         # else         → "flat"

ASYMMETRY_POS_THRESHOLD: float = 0.3   # asymmetry > 0.3  → "pos"  (MVP default)
ASYMMETRY_NEG_THRESHOLD: float = -0.3  # asymmetry < -0.3 → "neg"
                                         # else              → "neutral"

# ── Decision matrix (27 entries covering all bucket combinations) ─────────────
# Key: (score_bucket, momentum_bucket, asymmetry_bucket)
# Value: one of {"strong_buy", "buy", "hold", "sell", "strong_sell"}

DECISION_MATRIX: dict[tuple[str, str, str], str] = {
    # High score
    ("high", "up",   "pos"):     "strong_buy",
    ("high", "up",   "neutral"): "buy",
    ("high", "up",   "neg"):     "buy",
    ("high", "flat", "pos"):     "buy",
    ("high", "flat", "neutral"): "hold",
    ("high", "flat", "neg"):     "hold",
    ("high", "down", "pos"):     "hold",
    ("high", "down", "neutral"): "sell",
    ("high", "down", "neg"):     "sell",
    # Mid score
    ("mid",  "up",   "pos"):     "buy",
    ("mid",  "up",   "neutral"): "buy",
    ("mid",  "up",   "neg"):     "hold",
    ("mid",  "flat", "pos"):     "hold",
    ("mid",  "flat", "neutral"): "hold",
    ("mid",  "flat", "neg"):     "hold",
    ("mid",  "down", "pos"):     "hold",
    ("mid",  "down", "neutral"): "sell",
    ("mid",  "down", "neg"):     "sell",
    # Low score
    ("low",  "up",   "pos"):     "sell",
    ("low",  "up",   "neutral"): "sell",
    ("low",  "up",   "neg"):     "strong_sell",
    ("low",  "flat", "pos"):     "sell",
    ("low",  "flat", "neutral"): "strong_sell",
    ("low",  "flat", "neg"):     "strong_sell",
    ("low",  "down", "pos"):     "sell",
    ("low",  "down", "neutral"): "strong_sell",
    ("low",  "down", "neg"):     "strong_sell",
}

# ── Position sizing — Layer 1: base allocation per signal ─────────────────────
# Maps each of the 5 signal states to a base portfolio allocation percentage.
# "65% base × 1.5x conviction" for "Early Accumulate" (Score +0.61) confirmed
# in PRD example → buy = 65.0.

POSITION_BASE_TABLE: dict[str, float] = {
    "strong_buy":  85.0,
    "buy":         65.0,  # PRD-confirmed
    "hold":        30.0,
    "sell":        15.0,
    "strong_sell":  5.0,
}

# ── Position sizing — Layer 2: conviction multiplier by composite score ───────
# List of (score_low_inclusive, score_high_exclusive, multiplier).
# Covers [-1.0, +1.0] with no gaps. Framework: Strong=1.5x, Moderate=1.0x, Weak=0.5x.

CONVICTION_MULTIPLIER_TABLE: list[tuple[float, float, float]] = [
    (-1.01, 0.0,  0.5),   # weak: score < 0
    ( 0.0,  0.5,  1.0),   # moderate: 0 ≤ score < 0.5
    ( 0.5,  1.01, 1.5),   # strong: score ≥ 0.5
]

# ── Position sizing — Layer 3: volatility (beta) adjustment ───────────────────
# List of (beta_low_inclusive, beta_high_exclusive, adjustment_factor).
# MVP default — calibrate after observing live beta distribution of holdings.

VOLATILITY_ADJUSTMENT: list[tuple[float, float, float]] = [
    (0.0,  0.8,  1.1),   # low vol → size up slightly
    (0.8,  1.2,  1.0),   # market-like → no adjustment
    (1.2, 10.0,  0.8),   # high vol → size down
]

# ── Time Stop ─────────────────────────────────────────────────────────────────
# Percentage monthly price change (as decimal) required to reset the time stop
# counter. Framework: "no meaningful movement for 12–18 months → exit".
# compute_time_stop returns the count; action threshold is the caller's decision.

MEANINGFUL_MOVEMENT_THRESHOLD: float = 0.05  # 5% monthly change (MVP default)

# ── Factor normalisation ranges ───────────────────────────────────────────────
# Used by score_service._norm() to map raw values → [-1, +1].
# Tuple: (low_bound, high_bound, invert)
# invert=True → high raw value maps to -1 (e.g. high PE = expensive = bad)
# All values are MVP defaults — calibrate after backtesting.

FACTOR_NORMALISATION: dict[str, tuple[float, float, bool]] = {
    "liquidity":         (-5.0,  5.0, False),  # RBI surplus/deficit (₹ lakh cr); positive = loose
    "rates":             ( 4.0, 10.0,  True),  # Repo rate %; lower = more accommodative
    "credit_growth":     ( 5.0, 25.0, False),  # YoY bank credit growth %; higher = acceleration
    "valuation":         (10.0, 40.0,  True),  # PE ratio; lower = cheaper = positive
    "earnings":          ( 5.0, 30.0, False),  # ROE %; higher = better quality earnings
    "relative_strength": ( 0.5,  2.0, False),  # RS ratio vs Nifty; >1 = outperforming
    "usd_lens":          (-0.3,  0.3, False),  # Nifty 6M return in USD; positive = good
    "gold_lens":         (-0.3,  0.3, False),  # Nifty 6M outperformance vs Gold
    "sector_strength":   (-0.2,  0.2, False),  # Sector 6M outperformance vs Nifty
}

# ── Cross-asset instruments (now wired) ───────────────────────────────────────

# Gold price proxy — GOLDBEES ETF on NSE tracks physical gold in INR.
# Simpler than MCX futures: no expiry roll, regular NSE equity history.
GOLD_INSTRUMENT: str = "GOLDBEES"

# USDINR spot — NSE Currency Derivatives Segment (CDS).
# Requires CDS segment access on Kite account (must be activated separately).
USDINR_SYMBOL: str = "USDINR"
USDINR_SEGMENT: str = "CDS"

# ── Stock → Sector index mapping (sector_strength factor) ────────────────────
# Maps each Nifty 50 symbol to its primary NSE sector index tradingsymbol
# (as returned by kite.instruments("NSE") with segment="INDICES").

STOCK_SECTOR_INDEX: dict[str, str] = {
    # Banking
    "HDFCBANK":   "NIFTY BANK",
    "ICICIBANK":  "NIFTY BANK",
    "KOTAKBANK":  "NIFTY BANK",
    "AXISBANK":   "NIFTY BANK",
    "SBIN":       "NIFTY PSU BANK",
    "INDUSINDBK": "NIFTY BANK",
    # Financial Services
    "BAJFINANCE":  "NIFTY FINANCIAL SERVICES",
    "BAJAJFINSV":  "NIFTY FINANCIAL SERVICES",
    "HDFCLIFE":    "NIFTY FINANCIAL SERVICES",
    "SBILIFE":     "NIFTY FINANCIAL SERVICES",
    "SHRIRAMFIN":  "NIFTY FINANCIAL SERVICES",
    # Information Technology
    "TCS":    "NIFTY IT",
    "INFY":   "NIFTY IT",
    "HCLTECH":"NIFTY IT",
    "WIPRO":  "NIFTY IT",
    "TECHM":  "NIFTY IT",
    "LTIM":   "NIFTY IT",
    # Automobiles
    "MARUTI":    "NIFTY AUTO",
    "TATAMOTORS":"NIFTY AUTO",
    "M&M":       "NIFTY AUTO",
    "BAJAJ-AUTO":"NIFTY AUTO",
    "HEROMOTOCO":"NIFTY AUTO",
    "EICHERMOT": "NIFTY AUTO",
    # FMCG
    "HINDUNILVR": "NIFTY FMCG",
    "ITC":        "NIFTY FMCG",
    "BRITANNIA":  "NIFTY FMCG",
    "NESTLEIND":  "NIFTY FMCG",
    "TATACONSUM": "NIFTY FMCG",
    # Pharma / Healthcare
    "SUNPHARMA": "NIFTY PHARMA",
    "DRREDDY":   "NIFTY PHARMA",
    "CIPLA":     "NIFTY PHARMA",
    "DIVISLAB":  "NIFTY PHARMA",
    "APOLLOHOSP":"NIFTY HEALTHCARE",
    # Metals
    "TATASTEEL": "NIFTY METAL",
    "JSWSTEEL":  "NIFTY METAL",
    "HINDALCO":  "NIFTY METAL",
    "COALINDIA": "NIFTY METAL",
    # Energy & Oil
    "RELIANCE": "NIFTY ENERGY",
    "ONGC":     "NIFTY OIL AND GAS",
    "BPCL":     "NIFTY OIL AND GAS",
    "NTPC":     "NIFTY ENERGY",
    "POWERGRID":"NIFTY INFRA",
    "ADANIENT": "NIFTY ENERGY",
    # Infrastructure & Conglomerates
    "LT":        "NIFTY INFRA",
    "ADANIPORTS":"NIFTY INFRA",
    "GRASIM":    "NIFTY INFRA",
    "ULTRACEMCO":"NIFTY INFRA",
    # Consumer Durables / Others
    "TITAN":     "NIFTY CONSUMER DURABLES",
    "ASIANPAINT":"NIFTY CONSUMER DURABLES",
    # Telecom (NSE classifies under Media & Entertainment index)
    "BHARTIARTL":"NIFTY MEDIA",
}
