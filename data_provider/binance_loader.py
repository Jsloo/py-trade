# data_provider/binance_loader.py
import ccxt
import pandas as pd
import sys
import os

# 将上级目录加入路径，以便能导入 config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class BinanceLoader:
    def __init__(self):
        """初始化交易所连接（仅用于读取数据）"""
        # 1. 强制代理环境变量（确保数据拉取不被墙）
        os.environ['http_proxy'] = 'http://127.0.0.1:7890'
        os.environ['https_proxy'] = 'http://127.0.0.1:7890'

        self.exchange = ccxt.binanceusdm({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'timeout': 30000,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
            }
        })

        # --- 【关键修复点】 ---
        # 不要手动改 urls['api']['public']，直接启用官方 Demo 模式
        self.exchange.set_sandbox_mode(False)
        self.exchange.enable_demo_trading(True)

        # 禁用现货资产检测
        self.exchange.options['portfolioMargin'] = False

        print("📊 [LOADER] 数据加载器已切换至 Demo 模式")

    def get_ohlcv(self, symbol=config.SYMBOL, timeframe=config.TIMEFRAME, limit=config.LIMIT):
        """
        获取 K 线数据并清洗为 DataFrame
        """
        try:
            # fetch_ohlcv 返回的是列表: [timestamp, open, high, low, close, volume]
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            if not ohlcv:
                return None

            # 转换为 Pandas DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # 处理时间戳 (从毫秒转换为可读时间)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # 确保数据类型为浮点数 (有时候API返回字符串)
            cols = ['open', 'high', 'low', 'close', 'volume']
            df[cols] = df[cols].astype(float)

            return df

        except ccxt.NetworkError as e:
            print(f"[Data Error] 网络错误: {e}")
        except ccxt.ExchangeError as e:
            print(f"[Data Error] 交易所错误: {e}")
        except Exception as e:
            print(f"[Data Error] 未知错误: {e}")

        return None

    def get_advanced_data(self, symbol):
        """获取持仓量(OI)、资金费率、最近成交数据"""
        try:
            # 1. 获取当前持仓量 (Open Interest)
            # 格式：BTCUSDT
            market_id = self.exchange.market(symbol)['id']
            oi_data = self.exchange.fapiPublicGetOpenInterest({'symbol': market_id})
            oi = float(oi_data['openInterest'])

            # 2. 获取资金费率 (Funding Rate)
            funding_data = self.exchange.fetch_funding_rate(symbol)
            funding_rate = funding_data['fundingRate']

            # 3. 获取 CVD (Cumulative Volume Delta) 需要分析最近的 Ticks
            # 简化版逻辑：获取最近 500 笔成交，计算主动买入 vs 主动卖出
            trades = self.exchange.fetch_trades(symbol, limit=500)
            buy_vol = sum(float(t['amount']) for t in trades if t['side'] == 'buy')
            sell_vol = sum(float(t['amount']) for t in trades if t['side'] == 'sell')
            delta = buy_vol - sell_vol  # 这就是 Delta Bar 的核心

            return {
                'oi': oi,
                'funding_rate': funding_rate,
                'delta': delta,
                'cvd': buy_vol / sell_vol if sell_vol != 0 else 1
            }
        except Exception as e:
            print(f"数据获取失败: {e}")
            return None

    def get_current_price(self, symbol=config.SYMBOL):
        """获取当前最新成交价"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"[Price Error] 无法获取价格: {e}")
            return None