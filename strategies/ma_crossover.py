# strategies/ma_crossover.py
from .base_strategy import BaseStrategy


class MACrossoverStrategy(BaseStrategy):
    def __init__(self, short_window=20, long_window=50):
        self.name = f"MA Crossover ({short_window}/{long_window})"
        self.short_window = short_window
        self.long_window = long_window

    def analyze(self, df):
        # 1. 计算指标 (只在这个策略内部计算，不影响别人)
        df['sma_short'] = df['close'].rolling(window=self.short_window).mean()
        df['sma_long'] = df['close'].rolling(window=self.long_window).mean()

        if len(df) < self.long_window:
            return 'BUY'

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. 生成信号
        # 金叉：短期上穿长期
        if prev['sma_short'] < prev['sma_long'] and curr['sma_short'] > curr['sma_long']:
            return 'BUY'

        # 死叉：短期下穿长期
        elif prev['sma_short'] > prev['sma_long'] and curr['sma_short'] < curr['sma_long']:
            return 'SELL'

        return 'BUY'