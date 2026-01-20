# strategies/base_strategy.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self):
        self.name = "Base Strategy"

    @abstractmethod
    def analyze(self, df):
        """
        所有子策略必须实现这个方法。
        输入: K线数据 DataFrame
        输出: 'BUY', 'SELL', or 'HOLD'
        """
        pass