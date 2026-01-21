# strategies/ma_crossover.py
from .base_strategy import BaseStrategy


# strategies/order_flow_strategy.py

class OrderFlowStrategy:
    def __init__(self, short_window=20, long_window=50):
        self.name = f"OrderFlowStrategy ({short_window}/{long_window})"
        self.short_window = short_window
        self.long_window = long_window

    def analyze(self, df, adv_data):
        if not adv_data: return 'WAIT'

        curr_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]

        oi = adv_data['oi']
        delta = adv_data['delta']

        # 逻辑示例：价格在涨，且持仓量在猛增，且主动买入远大于主动卖出
        if curr_price > prev_price and delta > 0:
            # 进一步判断 OI 是否增加（需要你自己记录上一秒的 OI 进行对比）
            return 'BUY'
        elif curr_price < prev_price and delta < 0:
            return 'SELL'

        return 'WAIT'