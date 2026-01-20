# main.py
import time
import config
from data_provider.binance_loader import BinanceLoader
from execution.order_executor import OrderExecutor
from strategies.ma_crossover import MACrossoverStrategy


def main():
    print("🚀 量化系统初始化中...")

    # 1. 实例化各个模块
    data_loader = BinanceLoader()
    executor = OrderExecutor()
    strategy = MACrossoverStrategy(short_window=3, long_window=5)

    # 简单的状态标记 (实际项目中建议通过 executor.get_balance 动态判断持仓)
    is_holding = False

    print(f"当前策略: {strategy.name}")
    print(f"交易目标: {config.SYMBOL} (测试网: {config.SANDBOX_MODE})")

    while True:
        # Step 1: 获取数据
        df = data_loader.get_ohlcv()

        if df is not None:
            # Step 2: 策略分析
            signal = strategy.analyze(df)
            current_price = df['close'].iloc[-1]
            print(f"[{df['timestamp'].iloc[-1]}] 价格: {current_price} | 信号: {signal}")

            # Step 3: 执行交易
            if signal == 'BUY' and not is_holding:
                usdt_balance = executor.get_balance('USDT')
                # 检查可用余额是否足够
                if usdt_balance >= config.MARGIN_AMOUNT:
                    # 传入金额，并指定 amount_is_usdt=True
                    order = executor.place_market_order(config.SYMBOL, 'buy', config.MARGIN_AMOUNT, config.LEVERAGE)
                    if order:
                        is_holding = True
                        # 记录下单时的成交数量，方便以后平仓
                        holding_quantity = order['filled']
                else:
                    print(f"资金不足: 余额 {usdt_balance}U < 需求 {config.MARGIN_AMOUNT}U")

            elif signal == 'SELL' and is_holding:
                # 平仓建议：直接平掉之前记录的成交数量
                if holding_quantity > 0:
                    order = executor.place_market_order(config.SYMBOL, 'sell', holding_quantity, config.LEVERAGE)
                    if order:
                        is_holding = False
                        holding_quantity = 0

        # 休息一下
        time.sleep(10)


if __name__ == "__main__":
    main()