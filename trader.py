import requests
import time
import hmac
import hashlib
import config

class RealTrader:
    def __init__(self, deposit):
        self.deposit = deposit
        self.open_trades = []

    def _sign_request(self, params):
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            config.API_SECRET.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _api_request(self, method, endpoint, params=None):
        if params is None:
            params = {}
        params["api_key"] = config.API_KEY
        params["req_time"] = int(time.time() * 1000)
        params["sign"] = self._sign_request(params)

        url = f"https://api.mexc.com{endpoint}"
        try:
            if method == "POST":
                response = requests.post(url, data=params)
            else:
                response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"API request error: {e}")
            return None

    def place_real_order(self, trade):
        params = {
            "symbol": trade["symbol"],
            "price": trade["entry_price"],
            "vol": trade["amount"],
            "side": 1 if trade["side"] == "buy" else 2,
            "type": 1,  # Limit Order; for Market Order, set to 2
            "open_type": 1,  # Isolated Margin
            "position_id": 0,
            "leverage": trade["leverage"]
        }
        response = self._api_request("POST", "/api/v1/private/order/submit", params)
        if response and response.get("success"):
            print(f"Order placed successfully: {response}")
        else:
            print(f"Failed to place order: {response}")

    def open_trade(self, *args, **kwargs):
        # Открытие сделки в памяти + возврат структуры trade
        trade = {
            "symbol": args[0],
            "side": args[1],
            "entry_price": args[2],
            "amount": args[3],
            "leverage": args[4],
            "tp_levels": args[5],
            "tp_percents": args[6],
            "sl_percent": args[7],
            "use_trailing_stop": args[8],
            "trailing_stop_percent": args[9],
            "opened_at": time.time()
        }
        self.open_trades.append(trade)
        return trade

    def should_close_trade(self, trade, current_price):
        # Добавь свою логику проверки TP, SL и TS
        return False

    def close_trade(self, trade, current_price):
        # Добавь логику закрытия через API, если нужно
        if trade in self.open_trades:
            self.open_trades.remove(trade)
        pnl = (current_price - trade["entry_price"]) * trade["amount"]
        self.deposit += pnl
        return pnl, self.deposit

    def get_open_trades(self):
        return self.open_trades

    def get_stats(self):
        return {
            "total_trades": len(self.open_trades),
            "balance": self.deposit
        }
