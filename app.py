from flask import Flask, render_template_string
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
    <title>Stock Prices</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
            background-color: #f4f6f8;
        }
        h1 {
            text-align: center;
            color: #2c3e50;
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
        .tile:hover {
            transform: translateY(-4px);
        }
        .asx { border-left-color: #3498db; }
        .us { border-left-color: #2ecc71; }
        .title {
            font-size: 18px;
            color: #333333;
            margin-bottom: 8px;
        }
        .symbol {
            font-size: 14px;
            color: #7f8c8d;
        }
        .price {
            font-size: 22px;
            font-weight: bold;
            margin-top: 10px;
        }
        .up { color: #27ae60; }
        .down { color: #e74c3c; }
        .same { color: #888888; }
        .percent {
            font-size: 14px;
            margin-left: 6px;
        }
    </style>
</head>
<body>
    <h1>Real-Time Stock Prices (Delayed)</h1>
    <div class="container">
        {% for name, info in prices.items() %}
        <div class="tile {{ info.region }}">
            <div class="title">{{ name }}</div>
            <div class="symbol">{{ info.symbol }}</div>
            <div class="price {{ info.trend }}">
                ${{ info.price }}
                <span class="percent">({{ info.percent }})</span>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

def get_prices():
    prices = {}
    for name, symbol in TICKERS.items():
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
                if diff > 0:
                    trend = "up"
                elif diff < 0:
                    trend = "down"
                else:
                    trend = "same"
            else:
                percent_str = "N/A"
                trend = "same"

        except:
            current_price = "Error"
            percent_str = "N/A"
            trend = "same"

        region = "asx" if ".AX" in symbol else "us"
        prices[name] = {
            "symbol": symbol,
            "price": current_price,
            "trend": trend,
            "region": region,
            "percent": percent_str
        }

    return prices

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, prices=get_prices())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
