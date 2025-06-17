from flask import Flask, render_template_string, request, jsonify
import yfinance as yf
import os

app = Flask(__name__)

TICKERS = {
    "BHP (ASX)": "BHP.AX",
    "CBA (ASX)": "CBA.AX",
    "RIO (ASX)": "RIO.AX",
    "Apple (US)": "AAPL",
    "Tesla (US)": "TSLA",
    "Microsoft (US)": "MSFT"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Dashboard</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background-color: #f4f6f8; }
        h1 { text-align: center; color: #2c3e50; }
        form { text-align: center; margin-bottom: 30px; }
        input[type="text"], select {
            padding: 10px; font-size: 16px; margin: 0 10px; border-radius: 6px; border: 1px solid #ccc;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .tile {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease;
            border-left: 6px solid #ccc;
        }
        .tile:hover { transform: translateY(-4px); }
        .asx { border-left-color: #3498db; }
        .us { border-left-color: #2ecc71; }
        .title { font-size: 18px; color: #333333; margin-bottom: 8px; }
        .symbol { font-size: 14px; color: #7f8c8d; }
        .price { font-size: 22px; font-weight: bold; margin-top: 10px; }
        .up { color: #27ae60; }
        .down { color: #e74c3c; }
        .same { color: #888888; }
        .percent { font-size: 14px; margin-left: 6px; }

        .price .percent { font-weight: normal; }
    </style>
    <script>
    function fetchData() {
        const query = document.querySelector('[name="q"]').value || "";
        const filter = document.querySelector('[name="filter"]').value || "all";

        fetch(`/data?q=${query}&filter=${filter}`)
            .then(res => res.json())
            .then(data => {
                for (const name in data) {
                    const stock = data[name];
                    const tile = document.querySelector(`[data-stock="${stock.symbol}"]`);
                    if (tile) {
                        const priceEl = tile.querySelector(".price");
                        priceEl.innerHTML = `$${stock.price} <span class="percent">(${stock.percent})</span>`;
                        priceEl.className = `price ${stock.trend}`;
                    }
                }
            });
    }
    setInterval(fetchData, 30000);
    </script>
</head>
<body>
    <h1>Real-Time Stock Prices (Delayed)</h1>
    <form method="get">
        <input type="text" name="q" placeholder="Search stocks..." value="{{ query }}">
        <select name="filter">
            <option value="all" {% if active_filter == 'all' %}selected{% endif %}>All</option>
            <option value="asx" {% if active_filter == 'asx' %}selected{% endif %}>ASX Only</option>
            <option value="us" {% if active_filter == 'us' %}selected{% endif %}>US Only</option>
        </select>
        <input type="submit" value="Filter">
    </form>

    <div class="container">
        {% for name, info in prices.items() %}
        <div class="tile {{ info.region }}" data-stock="{{ info.symbol }}">
            <div class="title">{{ name }}</div>
            <div class="symbol">{{ info.symbol }}</div>
            <div class="price {{ info.trend }}">
                ${{ info.price }} <span class="percent">({{ info.percent }})</span>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

def get_prices(query=None, region_filter='all'):
    results = {}
    for name, symbol in TICKERS.items():
        region = "asx" if ".AX" in symbol else "us"

        if region_filter != 'all' and region != region_filter:
            continue

        if query:
            if query.lower() not in name.lower() and query.lower() not in symbol.lower():
                continue

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            hist = ticker.history(period="2d")

            if not data.empty:
                current_price = round(data['Close'].iloc[-1], 2)
            else:
                current_price = "N/A"

            if not hist.empty:
                previous_close = round(hist['Close'].iloc[-2], 2)
            else:
                previous_close = None

            if previous_close and isinstance(current_price, float):
                diff = current_price - previous_close
                percent = (diff / previous_close) * 100
                percent_str = f"{percent:+.2f}%"
                trend = "up" if diff > 0 else "down" if diff < 0 else "same"
            else:
                percent_str = "N/A"
                trend = "same"
        except:
            current_price = "Error"
            percent_str = "N/A"
            trend = "same"

        results[name] = {
            "symbol": symbol,
            "price": current_price,
            "trend": trend,
            "region": region,
            "percent": percent_str
        }

    return results

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    region_filter = request.args.get("filter", "all")
    prices = get_prices(query, region_filter)
    return render_template_string(HTML_TEMPLATE, prices=prices, query=query, active_filter=region_filter)

@app.route("/data")
def data():
    query = request.args.get("q", "").strip()
    region_filter = request.args.get("filter", "all")
    prices = get_prices(query, region_filter)
    return jsonify(prices)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
