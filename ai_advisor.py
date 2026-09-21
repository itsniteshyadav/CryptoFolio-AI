# ai_advisor.py — Gemini integration with strict crypto domain guard + Live Prices

import os
import re
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── CoinGecko symbol → ID map ────────────────────────────────────────
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "BNB": "binancecoin", "MATIC": "matic-network", "ADA": "cardano",
    "DOT": "polkadot", "AVAX": "avalanche-2", "LINK": "chainlink",
    "UNI": "uniswap", "ATOM": "cosmos", "NEAR": "near",
    "XRP": "ripple", "DOGE": "dogecoin", "LTC": "litecoin",
    "BCH": "bitcoin-cash", "ALGO": "algorand", "VET": "vechain",
    "SAND": "the-sandbox", "MANA": "decentraland", "APT": "aptos",
    "ARB": "arbitrum", "OP": "optimism", "INJ": "injective-protocol",
    "RNDR": "render-token", "FTM": "fantom", "HBAR": "hedera-hashgraph",
    "AAVE": "aave", "SHIB": "shiba-inu", "TRX": "tron",
    "TON": "the-open-network", "PEPE": "pepe", "SUI": "sui",
    "SEI": "sei-network", "WIF": "dogwifcoin", "BONK": "bonk",
}

# Name → symbol for natural language detection
NAME_TO_SYMBOL = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
    "binance": "BNB", "cardano": "ADA", "ripple": "XRP",
    "dogecoin": "DOGE", "polkadot": "DOT", "avalanche": "AVAX",
    "chainlink": "LINK", "uniswap": "UNI", "cosmos": "ATOM",
    "litecoin": "LTC", "algorand": "ALGO", "fantom": "FTM",
    "shiba": "SHIB", "tron": "TRX", "pepe": "PEPE",
    "sui": "SUI", "arbitrum": "ARB", "optimism": "OP",
    "near": "NEAR", "aptos": "APT", "injective": "INJ",
    "render": "RNDR", "hedera": "HBAR", "aave": "AAVE",
    "matic": "MATIC", "polygon": "MATIC", "toncoin": "TON",
}

SYSTEM_PROMPT = """
You are CryptoFolio AI, an expert cryptocurrency portfolio advisor.

You ONLY answer questions strictly related to:
- Cryptocurrency investments, trading, and portfolio management
- Blockchain technology and specific cryptocurrencies (BTC, ETH, SOL, etc.)
- Crypto market analysis, risk assessment, and portfolio strategies
- DCA (dollar cost averaging), rebalancing, and allocation advice
- Crypto market trends, technical analysis, and on-chain fundamentals
- Staking, DeFi, yield farming, NFTs, and Web3 concepts

You MUST REFUSE any question NOT related to cryptocurrency or blockchain.
For ANY off-topic question (cooking, weather, coding help, general trivia, etc.),
respond with ONLY this single word: OFF_TOPIC

IMPORTANT: When LIVE PRICE DATA is provided at the top of the message, you MUST
use those exact numbers in your answer. Never say you lack real-time data —
the live data is already fetched and given to you. State prices confidently.

Rules:
- Keep responses concise (max 200 words)
- Use bullet points for structured answers
- Always reference the user's portfolio data when it is provided
- Be data-driven and actionable
- Add a one-line disclaimer at the end: "⚠️ Not financial advice."
"""

CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "blockchain", "coin", "token", "defi", "nft", "wallet", "portfolio",
    "invest", "trade", "buy", "sell", "hodl", "market cap", "altcoin",
    "stablecoin", "yield", "stake", "staking", "mining", "exchange",
    "binance", "coinbase", "dex", "uniswap", "solana", "sol", "bnb",
    "xrp", "cardano", "ada", "polkadot", "avalanche", "chainlink",
    "matic", "polygon", "dogecoin", "shib", "price", "bull", "bear",
    "dip", "rally", "correction", "allocation", "rebalance", "diversif",
    "risk", "return", "profit", "loss", "pnl", "dca", "dollar cost",
    "apy", "apr", "volume", "technical", "whitepaper", "halving",
    "satoshi", "dominance", "rsi", "macd", "support", "resistance",
    "trend", "breakout", "ath", "all time high", "proof of work",
    "proof of stake", "validator", "fork", "airdrop", "ico", "ido",
    "tokenomics", "supply", "circulating", "web3", "smart contract",
    "gas", "fee", "layer", "l1", "l2", "rollup", "my portfolio",
    "my holdings", "my coins", "analyze", "analysis", "performance",
    "gain", "holding", "asset", "market", "current", "now", "today",
    "live", "latest", "real", "worth", "how much", "rate", "trading",
]


# ── Live data fetching (CoinGecko — free, no key needed) ─────────────

def fetch_live_prices(symbols: list) -> dict:
    """Fetch real-time USD prices + 24h change for a list of symbols."""
    ids = [COINGECKO_IDS[s.upper()] for s in symbols if s.upper() in COINGECKO_IDS]
    if not ids:
        return {}

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={','.join(ids)}&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptoFolioAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = {}
        for sym in symbols:
            sym = sym.upper()
            cg_id = COINGECKO_IDS.get(sym)
            if cg_id and cg_id in data:
                result[sym] = {
                    "price":     data[cg_id]["usd"],
                    "change_24h": round(data[cg_id].get("usd_24h_change", 0), 2),
                }
        return result

    except Exception as e:
        print(f"[CoinGecko] fetch_live_prices failed: {e}")
        return {}


def fetch_top_coins(limit: int = 10) -> list:
    """Fetch top N coins by market cap with live prices."""
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&order=market_cap_desc&per_page={limit}"
        "&page=1&sparkline=false&price_change_percentage=24h"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CryptoFolioAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [
            {
                "symbol":     c["symbol"].upper(),
                "name":       c["name"],
                "price":      c["current_price"],
                "change_24h": round(c.get("price_change_percentage_24h") or 0, 2),
                "market_cap": c["market_cap"],
                "rank":       c["market_cap_rank"],
            }
            for c in data
        ]
    except Exception as e:
        print(f"[CoinGecko] fetch_top_coins failed: {e}")
        return []


def detect_symbols(text: str) -> list:
    """Extract crypto symbols or coin names from user message."""
    found = set()

    # Match uppercase ticker symbols like BTC, ETH, SOL
    for word in re.findall(r'\b[A-Za-z]{2,6}\b', text):
        if word.upper() in COINGECKO_IDS:
            found.add(word.upper())

    # Match full coin names like "bitcoin", "ethereum"
    lower = text.lower()
    for name, sym in NAME_TO_SYMBOL.items():
        if name in lower:
            found.add(sym)

    return list(found)


def is_price_question(text: str) -> bool:
    triggers = [
        "price", "current", "now", "today", "live", "real-time",
        "worth", "value", "how much", "cost", "rate", "trading at",
        "what is", "what's", "tell me", "show me", "24h", "change",
        "performing", "trending", "market",
    ]
    lower = text.lower()
    return any(t in lower for t in triggers)


def is_top_coins_question(text: str) -> bool:
    triggers = [
        "top coin", "best coin", "top crypto", "top 10", "top ten",
        "market overview", "all coin", "ranking", "biggest", "largest",
        "list of", "leading crypto",
    ]
    lower = text.lower()
    return any(t in lower for t in triggers)


def build_live_context(user_message: str) -> str:
    """
    Detect what live data the question needs,
    fetch it from CoinGecko, and return a formatted string
    to prepend to the AI prompt.
    """
    lines = []

    # Top coins overview
    if is_top_coins_question(user_message):
        coins = fetch_top_coins(10)
        if coins:
            lines.append("=== LIVE TOP 10 CRYPTO PRICES (Source: CoinGecko, fetched right now) ===")
            for c in coins:
                sign = "+" if c["change_24h"] >= 0 else ""
                lines.append(
                    f"#{c['rank']} {c['name']} ({c['symbol']}): "
                    f"${c['price']:,} USD | 24h: {sign}{c['change_24h']}%"
                )
            lines.append("=========================================================================")

    # Specific coin price question
    elif is_price_question(user_message):
        symbols = detect_symbols(user_message)
        if symbols:
            live = fetch_live_prices(symbols)
            if live:
                lines.append("=== LIVE CRYPTO PRICES (Source: CoinGecko, fetched right now) ===")
                for sym, info in live.items():
                    sign = "+" if info["change_24h"] >= 0 else ""
                    lines.append(
                        f"{sym}: ${info['price']:,} USD | "
                        f"24h Change: {sign}{info['change_24h']}%"
                    )
                lines.append("===================================================================")

    return "\n".join(lines)


# ── Domain guard (unchanged from your original) ───────────────────────

def is_crypto_domain(text: str, has_portfolio: bool) -> bool:
    lower = text.lower()
    question_starters = [
        "analyze", "how", "what", "should", "give", "tell",
        "show", "help", "is", "are", "which", "why", "when",
        "price", "current", "today", "latest",
    ]
    if has_portfolio and any(lower.startswith(w) for w in question_starters):
        return True
    return any(kw in lower for kw in CRYPTO_KEYWORDS)


# ── Main function (same signature as your original) ───────────────────

def ask_advisor(user_message: str, portfolio_context: str) -> str:
    has_portfolio = "no crypto holdings" not in portfolio_context

    # Domain guard — same as your original
    if not is_crypto_domain(user_message, has_portfolio):
        return "OFF_TOPIC"

    # Fetch live market data if the question needs it
    live_context = build_live_context(user_message)

    # Build full message — inject live data at the top so Gemini sees it first
    parts = []
    if live_context:
        parts.append(live_context)
    parts.append(f"{portfolio_context}\n\nUser question: {user_message}")

    full_user_message = "\n\n".join(parts)

    # Everything below is identical to your original
    prompt = f"""
{SYSTEM_PROMPT}

{full_user_message}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    reply = response.text.strip()
    return reply