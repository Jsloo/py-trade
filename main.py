# main.py
import time
import config
from data_provider.binance_loader import BinanceLoader
from execution.order_executor import OrderExecutor
from strategies.ma_crossover import MACrossoverStrategy
import requests

from strategies.order_flow_strategy import OrderFlowStrategy


def main():
    msg = "🤖 *量化系统已启动*\n" + f"交易对: {config.SYMBOL}\n策略: MA Crossover"
    send_telegram_msg(msg)
    print("🚀 量化系统初始化中...")

    # 1. 实例化各个模块
    data_loader = BinanceLoader()
    executor = OrderExecutor()
    strategy = OrderFlowStrategy()

    # 简单的状态标记 (实际项目中建议通过 executor.get_balance 动态判断持仓)
    is_holding = False

    print(f"当前策略: {strategy.name}")
    print(f"交易目标: {config.SYMBOL} (测试网: {config.SANDBOX_MODE})")

    while True:
        # Step 1: 获取数据
        df = data_loader.get_ohlcv()
        adv_data = data_loader.get_advanced_data(config.SYMBOL)  # 获取高级数据

        if df is not None and adv_data:
            # Step 2: 策略分析
            signal = strategy.analyze(df, adv_data)
            current_price = df['close'].iloc[-1]
            print(f"[{df['timestamp'].iloc[-1]}] 价格: {current_price} | 信号: {signal}")

            # Step 3: 执行交易
            if signal == 'BUY' and not is_holding:
                usdt_balance = executor.get_balance('USDT')
                # 检查可用余额是否足够
                if usdt_balance >= config.MARGIN_AMOUNT:
                    # 传入金额，并指定 amount_is_usdt=True
                    order = executor.place_order_with_tp_sl(config.SYMBOL, 'buy', config.MARGIN_AMOUNT, config.LEVERAGE)
                    if order:
                        is_holding = True
                        # 记录下单时的成交数量，方便以后平仓
                        holding_quantity = order['filled']
                        send_telegram_msg(
                            f"🚀 *【多单入场】*\n"
                            f"价格: `{order['average']}`\n"
                            f"本金: `{config.MARGIN_AMOUNT}U` (杠杆: {config.LEVERAGE}x)\n"
                            f"数量: `{holding_quantity} BTC`"
                        )
                else:
                    print(f"资金不足: 余额 {usdt_balance}U < 需求 {config.MARGIN_AMOUNT}U")

            elif signal == 'SELL' and is_holding:
                # 平仓建议：直接平掉之前记录的成交数量
                if holding_quantity > 0:
                    order = executor.place_order_with_tp_sl(config.SYMBOL, 'sell', holding_quantity, config.LEVERAGE)
                    if order:
                        send_telegram_msg(
                            f"🔻 *【多单平仓】*\n"
                            f"卖出价格: `{order['average']}`\n"
                            f"释放数量: `{holding_quantity}`"
                        )
                        is_holding = False
                        holding_quantity = 0

        # 休息一下
        time.sleep(10)


def send_telegram_msg(message):
    """发送消息到 Telegram（带代理与超时保护）"""
    token = config.TELEGRAM_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 【关键】请确保此端口与你代理软件显示的端口 100% 一致
    proxy_port = "7890"
    proxies = {
        'http': f'http://127.0.0.1:{proxy_port}',
        'https': f'http://127.0.0.1:{proxy_port}'
    }

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, json=payload, proxies=proxies, timeout=5)
        # 检查是否发送成功
        response.raise_for_status()
    except Exception as e:
        # 只打印错误，不让程序崩溃
        print(f"⚠️ Telegram 发送失败: {e}")

if __name__ == "__main__":
    main()