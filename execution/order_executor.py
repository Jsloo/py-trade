# execution/order_executor.py
import ccxt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class OrderExecutor:
    def __init__(self):
        # 1. 代理
        import os
        os.environ['http_proxy'] = 'http://127.0.0.1:7890'
        os.environ['https_proxy'] = 'http://127.0.0.1:7890'

        # 2. 实例化 binanceusdm
        self.exchange = ccxt.binanceusdm({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
            }
        })

        # 3. 核心配置：只开启这个，不要再手动改 urls 字典
        self.exchange.set_sandbox_mode(False)  # 确保不走老测试网
        self.exchange.enable_demo_trading(True)  # 开启新模拟盘

        try:
            balance = self.get_balance()
            print(f"✅ 验证成功！当前模拟账户余额: {balance} USDT")
        except Exception as e:
            print(f"❌ 验证仍失败: {e}")

    def get_balance(self, currency='USDT'):
        try:
            # 使用 fetch_balance 而不是直接调用 getAccount
            # CCXT 内部会自动处理 demo 模式下的路径拼接（/fapi/v1/...）
            balance = self.exchange.fetch_balance()

            # 在模拟盘中，数据结构可能在 'info' 里
            if currency in balance['total']:
                return balance['total'][currency]

            # 兜底方案：如果 fetch_balance 拿不到，再尝试原始调用
            # 注意这里不带 /fapi，因为 enable_demo_trading 会自动处理
            res = self.exchange.fapiPrivateGetAccount()
            for asset in res['assets']:
                if asset['asset'] == currency:
                    return float(asset['availableBalance'])
            return 0.0
        except Exception as e:
            print(f"❌ 最终余额查询失败: {e}")
            return 0.0

    def set_leverage(self, symbol, leverage):
        try:
            # 只有当杠杆确实需要修改时才调用，或者直接捕获异常不打印
            market = self.exchange.market(symbol)
            # 币安某些接口要求 market['id']，即 BTCUSDT，而不是 BTC/USDT
            res = self.exchange.set_leverage(int(leverage), market['id'])
            print(f"⚙️ [CONFIG] 杠杆确认: {leverage}x")
            return res
        except Exception as e:
            # 如果是已经设置过相同的杠杆，忽略这个错误
            if "already" in str(e).lower() or "-1000" in str(e):
                return None
            print(f"⚠️ 杠杆设置提示: {e}")

    def place_market_order(self, symbol, side, margin_amount, leverage):
        """
        :param margin_amount: 你要下的本金（如 150）
        :param leverage: 杠杆倍数（如 10）
        """
        try:
            # 1. 先设置杠杆
            self.set_leverage(symbol, leverage)

            # 2. 计算总名义价值 (Notional Value)
            total_notional_usdt = margin_amount * leverage

            # 3. 获取价格并换算数量
            self.exchange.load_markets()
            market = self.exchange.market(symbol)
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            # 计算 BTC 数量
            raw_qty = total_notional_usdt / current_price

            # 精度处理：向上取整以确保不低于 100U 限制
            step_size = market['limits']['amount']['min']
            import math
            final_qty = math.ceil(raw_qty / step_size) * step_size
            final_qty_str = self.exchange.amount_to_precision(symbol, final_qty)

            print(f"💰 [BET] 本金: {margin_amount}U | 杠杆: {leverage}x | 总头寸: {total_notional_usdt}U")
            print(f"📝 [API] 发送数量: {final_qty_str} BTC")

            # 4. 下单
            order = self.exchange.create_market_order(symbol, side, final_qty_str)
            print(f"✅ 下单成功! 均价: {order['average']} | 实际仓位价值: {order['cost']} USDT")
            return order

        except Exception as e:
            print(f"❌ 下单失败: {e}")
            return None

    def place_order_with_tp_sl(self, symbol, side, margin_amount, leverage, tp_percent=0.02, sl_percent=0.01):
        """
        下单并附带止盈止损
        :param tp_percent: 2% 止盈
        :param sl_percent: 1% 止损
        """
        try:
            # 1. 先开主仓位 (市价单)
            main_order = self.place_market_order(symbol, side, margin_amount, leverage)
            if not main_order: return None

            avg_price = float(main_order['average'])
            quantity = float(main_order['filled'])

            # 2. 计算止盈止损价格
            if side == 'buy':
                tp_price = avg_price * (1 + tp_percent)
                sl_price = avg_price * (1 - sl_percent)
                close_side = 'sell'
            else:
                tp_price = avg_price * (1 - tp_percent)
                sl_price = avg_price * (1 + sl_percent)
                close_side = 'buy'

            # 3. 提交止损单 (STOP_MARKET)
            self.exchange.create_order(
                symbol=symbol,
                type='STOP_MARKET',
                side=close_side,
                amount=quantity,
                params={'stopPrice': self.exchange.price_to_precision(symbol, sl_price)}
            )

            # 4. 提交止盈单 (TAKE_PROFIT_MARKET)
            self.exchange.create_order(
                symbol=symbol,
                type='TAKE_PROFIT_MARKET',
                side=close_side,
                amount=quantity,
                params={'stopPrice': self.exchange.price_to_precision(symbol, tp_price)}
            )

            print(f"🎯 止盈已设: {tp_price}, 止损已设: {sl_price}")
            return main_order

        except Exception as e:
            print(f"止盈止损设置失败: {e}")