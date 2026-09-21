# app.py — Flask server (main entry point)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from portfolio import add_coin, remove_coin, get_portfolio_summary, build_portfolio_context
from ai_advisor import ask_advisor

app = Flask(__name__)
CORS(app)


# ── Pages ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── Portfolio API ───────────────────────────────────────────────────────
@app.route("/api/portfolio", methods=["GET"])
def api_get_portfolio():
    return jsonify(get_portfolio_summary())


@app.route("/api/portfolio/add", methods=["POST"])
def api_add_coin():
    data = request.get_json()
    symbol    = data.get("symbol", "").strip().upper()
    amount    = float(data.get("amount", 0))
    buy_price = float(data.get("buy_price", 0))

    if not symbol or amount <= 0 or buy_price <= 0:
        return jsonify({"error": "Invalid input. Provide symbol, amount, and buy_price."}), 400

    coin = add_coin(symbol, amount, buy_price)
    return jsonify({"success": True, "coin": coin, "portfolio": get_portfolio_summary()})


@app.route("/api/portfolio/remove/<symbol>", methods=["DELETE"])
def api_remove_coin(symbol):
    removed = remove_coin(symbol)
    if not removed:
        return jsonify({"error": f"{symbol} not found in portfolio."}), 404
    return jsonify({"success": True, "portfolio": get_portfolio_summary()})


# ── AI Chat API ─────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data    = request.get_json()
        message = data.get("message", "").strip()

        if not message:
            return jsonify({"error": "Message cannot be empty."}), 400

        portfolio_context = build_portfolio_context()
        reply = ask_advisor(message, portfolio_context)

        if reply == "OFF_TOPIC":
            return jsonify({
                "reply": "OFF_TOPIC",
                "message": "I only handle cryptocurrency portfolio questions. Please ask about your crypto holdings, market analysis, or blockchain topics."
            })

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"⚠️ Backend error: {str(e)}"}), 500
@app.route("/api/price/<symbol>", methods=["GET"])
def api_live_price(symbol):
    """Return live price for a single coin symbol."""
    try:
        from ai_advisor import fetch_live_prices
        data = fetch_live_prices([symbol.upper()])
        if data:
            return jsonify({"success": True, "data": data})
        return jsonify({"success": False, "error": "Symbol not found or API unavailable"}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True, port=5000)