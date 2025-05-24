from pybit.unified_trading import HTTP
from decimal import Decimal
import os
import time

class BybitTrader:
    def __init__(self, deposit):
        self.deposit = deposit
        self.open_trades = []
        self.session = HTTP(
            api_key=os.getenv("BYBIT_API_KEY"),
            api_secret=os.getenv("BYBIT_API_SECRET"),
            testnet=False
        )
        self.category = "linear"

    def get_symbol_info(self, symbol):
        try:
            res = self.session.get_instruments_info(category=self.category, symbol=symbol)
            return res['result']['list'][0] if res['result']['list'] else {}
        except Exception as e:
            print(f"❌ Ошибка получения информации по символу {symbol}: {e}")
            return {}

    def floor(self, value, decimals):
        factor = Decimal('1') / (Decimal('10') ** decimals)
        return (Decimal(str(value)) // factor) * factor

    def round_qty(self, symbol, qty):
        info = self.get_symbol_info(symbol)
        step_qty = Decimal(info.get('lotSizeFilter', {}).get('qtyStep', '0.001'))
        qty_decimals = abs(step_qty.as_tuple().exponent)
        adjusted_qty = self.floor(qty, qty_decimals)
        return f"{adjusted_qty:.{qty_decimals}f}"

    def round_price(self, symbol, price):
        info = self.get_symbol_info(symbol)
        tick_size = Decimal(info.get('priceFilter', {}).get('tickSize', '0.0001'))
        price_decimals = abs(tick_size.as_tuple().exponent)
        adjusted_price = self.floor(price, price_decimals)
        return f"{adjusted_price:.{price_decimals}f}"

    def get_price(self, symbol):
        try:
            res = self.session.get_tickers(category=self.category, symbol=symbol)
            return float(res['result']['list'][0]['ask1Price'])
        except Exception as e:
            print(f"❌ Ошибка получения цены {symbol}: {e}")
            return None

    def place_market_order_by_base(self, symbol, qty, side):
        args = dict(
            category=self.category,
            symbol=symbol,
            side=side.capitalize(),
            orderType="Market",
            qty=self.round_qty(symbol, qty),
            orderLinkId=f"AzzraelCode_{symbol}_{time.time()}"
        )
        print("args", args)
        r = self.session.place_order(**args)
        print("result", r)
        return r

    def place_market_order_by_quote(self, symbol, quote: float = 5.0, side: str = "Sell"):
        curr_price = self.get_price(symbol)
        if not curr_price:
            print(f"❌ Невозможно получить цену для {symbol}")
            return None
        qty = Decimal(quote) / Decimal(curr_price)
        return self.place_market_order_by_base(symbol, qty, side)

    def place_limit_order(self, symbol, side, qty, price):
        trade_side = "Buy" if side.lower() == "buy" else "Sell"
        try:
            formatted_qty = self.round_qty(symbol, qty)
            formatted_price = self.round_price(symbol, price)
            response = self.session.place_order(
                category=self.category,
                symbol=symbol,
                side=trade_side,
                order_type="Limit",
                qty=formatted_qty,
                price=formatted_price,
                time_in_force="GoodTillCancel",
                reduce_only=True,
                is_leverage=True,
                order_link_id=f"limit_{symbol}_{int(time.time())}"
            )
            print("📦 Limit ордер размещён:", response)
            return response
        except Exception as e:
            print(f"[BYBIT ERROR] ❌ Ошибка при Limit ордере: {e}")
            return None

    def get_account_balance(self):
        try:
            result = self.session.get_wallet_balance(accountType="UNIFIED")
            coins = result["result"]["list"][0]["coin"]
            usdt = next((c for c in coins if c["coin"] == "USDT"), None)
            if not usdt:
                print("❌ USDT не найден среди монет аккаунта.")
                return 0, 0
            balance = float(usdt.get("walletBalance") or 0)
            available = float(usdt.get("availableToWithdraw") or 0)
            print(f"💰 Баланс USDT: {balance} (доступно: {available})")
            return balance, available
        except Exception as e:
            print(f"❌ Ошибка получения баланса: {e}")
            return 0, 0

    def activate_trailing_stop(self, symbol, trailing_percent):
        try:
            response = self.session.set_trading_stop(
                category=self.category,
                symbol=symbol.replace("_", ""),
                trailingStop=trailing_percent
            )
            print(f"🔁 Трейлинг-стоп установлен: {response}")
            return response
        except Exception as e:
            print(f"❌ Ошибка установки трейлинг-стопа: {e}")
            return None

    def get_open_trades(self):
        return self.open_trades

    def open_trade(self, symbol, side, entry_price, amount, leverage, tp_levels, tp_percents, sl_percent, trailing_stop, trailing_percent):
        try:
            notional = amount * leverage
            qty = notional / entry_price

            try:
                leverage_response = self.session.set_leverage(
                    category=self.category,
                    symbol=symbol.replace("_", ""),
                    buyLeverage=leverage,
                    sellLeverage=leverage
                )
                print(f"✅ Установлено плечо {leverage}x: {leverage_response}")
            except Exception as e:
                print(f"❌ Ошибка установки плеча: {e}")

            response = self.place_market_order_by_base(symbol.replace("_", ""), qty, side)
            if not response:
                print(f"❌ Сделка по {symbol} не открыта — ошибка ордера.")
                return None

            result = response.get("result", {})
            entry_price_actual = float(result.get("avgFillPrice", entry_price))

            if side.lower() == "buy":
                tp_prices = [entry_price_actual * (1 + level / 100) for level in tp_levels]
                sl_price = entry_price_actual * (1 - sl_percent / 100)
            else:
                tp_prices = [entry_price_actual * (1 - level / 100) for level in tp_levels]
                sl_price = entry_price_actual * (1 + sl_percent / 100)

            print(f"✅ Открыта позиция по {symbol} @ {entry_price_actual:.4f}")
            print(f"🎯 TP1: {tp_prices[0]:.4f}, TP2: {tp_prices[1]:.4f}, TP3: {tp_prices[2]:.4f}, SL: {sl_price:.4f}")

            try:
                stop_response = self.session.set_trading_stop(
                    category=self.category,
                    symbol=symbol.replace("_", ""),
                    stopLoss=sl_price
                )
                print(f"📌 TP/SL установлены на бирже: {stop_response}")
            except Exception as e:
                print(f"⚠️ Ошибка установки TP/SL через set_trading_stop: {e}")

            for i, level in enumerate(tp_levels):
                percent = tp_percents[i]
                if level > 0 and percent > 0:
                    tp_price = tp_prices[i]
                    tp_qty = amount * (percent / 100)
                    try:
                        tp_response = self.session.place_order(
                            category=self.category,
                            symbol=symbol.replace("_", ""),
                            side="Sell" if side.lower() == "buy" else "Buy",
                            order_type="Limit",
                            qty=self.round_qty(symbol, tp_qty),
                            price=self.round_price(symbol, tp_price),
                            reduce_only=True,
                            order_link_id=f"tp{i+1}_{symbol}_{int(time.time())}"
                        )
                        print(f"🎯 TP{i+1} размещён: цена {tp_price:.4f}, объём {tp_qty}")
                    except Exception as e:
                        print(f"⚠️ Ошибка размещения TP{i+1}: {e}")

            trade = {
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price_actual,
                "amount": amount,
                "remaining_amount": amount,
                "leverage": leverage,
                "tp_levels": tp_levels,
                "tp_percents": tp_percents,
                "tp_prices": tp_prices,
                "tp_triggered": [False, False, False],
                "sl_price": sl_price,
                "sl_percent": sl_percent,
                "trailing_stop": trailing_stop,
                "trailing_percent": trailing_percent,
                "trailing_level": None,
                "opened_at": time.time(),
                "status": "open",
                "ts_activated": False
            }

            self.open_trades.append(trade)
            return trade

        except Exception as e:
            print(f"❌ Ошибка при открытии сделки по {symbol}: {e}")
            return None
