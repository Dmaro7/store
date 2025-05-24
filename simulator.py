import time

class TradeSimulator:
    def __init__(self, deposit):
        self.deposit = deposit
        self.open_trades = []
        self.stats = {
            "total_trades": 0,
            "open_trades": 0,
            "tp1_count": 0,
            "tp2_count": 0,
            "tp3_count": 0,
            "ts_count": 0,
            "sl_count": 0,
            "rev_count": 0,
            "tp1_profit": 0.0,
            "tp2_profit": 0.0,
            "tp3_profit": 0.0,
            "ts_profit": 0.0,
            "sl_loss": 0.0,
            "rev_profit": 0.0
        }

    def open_trade(self, symbol, side, entry_price, amount, leverage, tp_levels, tp_percents, sl_percent, trailing_stop, trailing_percent):
        trade = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "amount": amount,
            "remaining_amount": amount,
            "leverage": leverage,
            "tp_levels": tp_levels,
            "tp_percents": tp_percents,
            "tp_triggered": [False] * len(tp_levels),
            "sl_percent": sl_percent,
            "trailing_stop": trailing_stop,
            "trailing_percent": trailing_percent,
            "trailing_level": None,
            "status": "open",
            "opened_at": time.time(),
            "highest_price": entry_price,
            "lowest_price": entry_price,
            "closed_percent": 0,
            "close_reason": "вручную",
            "open_message_id": None,
            "balance_at_open": self.deposit,
            "price_change_time": 0,
            "ts_activated": False
        }
        self.open_trades.append(trade)
        self.stats["total_trades"] += 1
        self.stats["open_trades"] = len(self.open_trades)
        return trade

    def get_open_trades(self):
        return self.open_trades

    def should_close_trade(self, trade, current_price):
        if trade["status"] == "closed":
            return False

        entry_price = trade["entry_price"]
        side = trade["side"].lower()
        sl_percent = trade["sl_percent"]
        tp_levels = trade["tp_levels"]

        change_percent = ((current_price - entry_price) / entry_price) * 100 if side == "buy" else ((entry_price - current_price) / entry_price) * 100

        for idx, tp in enumerate(tp_levels):
            if not trade["tp_triggered"][idx] and change_percent >= tp:
                percent_to_close = trade["tp_percents"][idx]
                if percent_to_close > 0 and trade["remaining_amount"] > 0:
                    trade["tp_triggered"][idx] = True
                    trade["close_reason"] = f"TP{idx + 1}"
                    trade["closed_percent"] += percent_to_close
                    trade["remaining_amount"] -= trade["amount"] * (percent_to_close / 100)

                    if idx == 0 and trade["trailing_stop"]:
                        trade["ts_activated"] = True
                        if side == "buy":
                            trade["trailing_level"] = current_price * (1 - trade["trailing_percent"] / 100)
                        else:
                            trade["trailing_level"] = current_price * (1 + trade["trailing_percent"] / 100)
                    return True

        if change_percent <= -sl_percent:
            trade["close_reason"] = "SL"
            trade["closed_percent"] = 100
            trade["remaining_amount"] = 0
            return True

        if trade["trailing_stop"] and trade.get("trailing_level"):
            if side == "buy":
                if current_price > trade["highest_price"]:
                    trade["highest_price"] = current_price
                    trade["trailing_level"] = current_price * (1 - trade["trailing_percent"] / 100)
                if current_price <= trade["trailing_level"]:
                    trade["close_reason"] = "TS"
                    trade["closed_percent"] = 100
                    trade["remaining_amount"] = 0
                    return True
            else:
                if current_price < trade["lowest_price"]:
                    trade["lowest_price"] = current_price
                    trade["trailing_level"] = current_price * (1 + trade["trailing_percent"] / 100)
                if current_price >= trade["trailing_level"]:
                    trade["close_reason"] = "TS"
                    trade["closed_percent"] = 100
                    trade["remaining_amount"] = 0
                    return True

        return False

    def close_trade(self, trade, exit_price):
        if trade["status"] == "closed":
            return 0, self.deposit

        entry_price = trade["entry_price"]
        side = trade["side"].lower()

        if trade.get("close_reason") == "REV":
            amount_to_close = trade["amount"]
        else:
            amount_to_close = trade["amount"] * (trade["closed_percent"] / 100)

        if side == "buy":
            profit_percent = ((exit_price - entry_price) / entry_price) * 100
        else:
            profit_percent = ((entry_price - exit_price) / entry_price) * 100

        profit = amount_to_close * (profit_percent / 100) * trade["leverage"]
        self.deposit += profit

        trade["remaining_amount"] -= amount_to_close
        trade["exit_price"] = exit_price
        trade["closed_at"] = time.time()

        if not trade.get("close_reason"):
            trade["close_reason"] = "вручную"

        if trade["remaining_amount"] <= 0 or trade["closed_percent"] >= 100 or trade["close_reason"] == "REV":
            trade["status"] = "closed"
            if trade in self.open_trades:
                self.open_trades.remove(trade)

        reason = trade.get("close_reason", "manual")
        if reason == "SL":
            self.stats["sl_count"] += 1
            self.stats["sl_loss"] += abs(profit)
        elif reason == "TS":
            self.stats["ts_count"] += 1
            self.stats["ts_profit"] += profit
        elif "TP" in reason:
            level = int(reason.replace("TP", ""))
            if level == 1:
                self.stats["tp1_count"] += 1
                self.stats["tp1_profit"] += profit
            elif level == 2:
                self.stats["tp2_count"] += 1
                self.stats["tp2_profit"] += profit
            elif level == 3:
                self.stats["tp3_count"] += 1
                self.stats["tp3_profit"] += profit
        elif reason == "REV":
            self.stats["rev_count"] += 1
            self.stats["rev_profit"] += profit

        self.stats["open_trades"] = len(self.open_trades)
        return round(profit, 2), round(self.deposit, 2)

    def get_stats(self):
        return self.stats
