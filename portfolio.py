# portfolio.py — Portfolio storage and calculations

CRYPTO_PRICES = {
    "BTC": 67420, "ETH": 3280, "SOL": 168, "BNB": 412,
    "MATIC": 0.72, "ADA": 0.43, "DOT": 7.8, "AVAX": 35.2,
    "LINK": 14.6, "UNI": 8.9, "ATOM": 9.1, "NEAR": 5.2,
    "XRP": 0.52, "DOGE": 0.12, "LTC": 78, "BCH": 380,
    "ALGO": 0.18, "VET": 0.035, "SAND": 0.42, "MANA": 0.38,
    "APT": 8.7, "ARB": 1.12, "OP": 2.4, "INJ": 24.5,
    "RNDR": 8.1, "FTM": 0.52, "HBAR": 0.095, "AAVE": 88,
}

# In-memory portfolio (per session — replace with DB for production)
portfolio = {}


def get_current_price(symbol: str, fallback: float) -> float:
    return CRYPTO_PRICES.get(symbol.upper(), fallback)


def add_coin(symbol: str, amount: float, buy_price: float) -> dict:
    symbol = symbol.upper()
    current_price = get_current_price(symbol, buy_price)

    if symbol in portfolio:
        existing = portfolio[symbol]
        total_amount = existing["amount"] + amount
        avg_price = (
            existing["buy_price"] * existing["amount"] + buy_price * amount
        ) / total_amount
        portfolio[symbol]["amount"] = total_amount
        portfolio[symbol]["buy_price"] = round(avg_price, 4)
        portfolio[symbol]["current_price"] = current_price
    else:
        portfolio[symbol] = {
            "symbol": symbol,
            "amount": amount,
            "buy_price": buy_price,
            "current_price": current_price,
        }

    return portfolio[symbol]


def remove_coin(symbol: str) -> bool:
    symbol = symbol.upper()
    if symbol in portfolio:
        del portfolio[symbol]
        return True
    return False


def get_portfolio_summary() -> dict:
    if not portfolio:
        return {"holdings": [], "total_value": 0, "total_cost": 0, "pnl": 0, "pnl_pct": 0}

    holdings = []
    total_value = 0
    total_cost = 0

    for sym, coin in portfolio.items():
        value = coin["amount"] * coin["current_price"]
        cost = coin["amount"] * coin["buy_price"]
        pnl = value - cost
        pnl_pct = ((coin["current_price"] - coin["buy_price"]) / coin["buy_price"]) * 100

        total_value += value
        total_cost += cost

        holdings.append({
            "symbol": sym,
            "amount": coin["amount"],
            "buy_price": coin["buy_price"],
            "current_price": coin["current_price"],
            "value": round(value, 2),
            "cost": round(cost, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "allocation": 0,  # filled below
        })

    # Fill allocation %
    for h in holdings:
        h["allocation"] = round((h["value"] / total_value) * 100, 2) if total_value else 0

    overall_pnl = total_value - total_cost
    overall_pnl_pct = ((overall_pnl / total_cost) * 100) if total_cost else 0

    return {
        "holdings": holdings,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "pnl": round(overall_pnl, 2),
        "pnl_pct": round(overall_pnl_pct, 2),
        "count": len(holdings),
        "risk": "HIGH" if len(holdings) <= 2 else "MEDIUM" if len(holdings) <= 4 else "LOW",
    }


def build_portfolio_context() -> str:
    summary = get_portfolio_summary()
    if not summary["holdings"]:
        return "The user has no crypto holdings added yet."

    lines = ["=== USER PORTFOLIO ==="]
    for h in summary["holdings"]:
        lines.append(
            f"• {h['symbol']}: {h['amount']} units | "
            f"Current ${h['current_price']} | Bought @ ${h['buy_price']} | "
            f"Value ${h['value']} | P&L {h['pnl_pct']}% | Allocation {h['allocation']}%"
        )
    lines.append(f"Total Value:  ${summary['total_value']}")
    lines.append(f"Cost Basis:   ${summary['total_cost']}")
    lines.append(f"Overall P&L:  {summary['pnl_pct']}%")
    lines.append(f"Holdings:     {summary['count']}")
    lines.append("======================")
    return "\n".join(lines)