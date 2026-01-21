# config.py
import os

# ================= 交易所配置 =================
# 优先从环境变量读取，如果没有则使用默认字符串 (但在生产环境切记不要硬编码!)
API_KEY = os.getenv('BINANCE_API_KEY', 'Onm80zFe61ke8NLUhkSxda33rK8hdVebXJZojVYnHH0dSRw89zsEvGCjh3albSTz')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '69V9986ew7So6Ug5JAU8BsolwzbvGVPiUnPD8IT8dboxbiLlvH0hes2NHj7IP2fI')

# 是否使用测试网 (True = 测试网, False = 实盘)
SANDBOX_MODE = False

# ================= 交易目标 =================
SYMBOL = 'BTC/USDT:USDT'     # 交易对
TIMEFRAME = '1m'        # K线周期
LIMIT = 100             # 每次获取多少根K线
DEFAULT_TYPE = 'future'  # <--- 必须明确指定为 future
LEVERAGE = 10
# ================= 风险控制 =================
QUANTITY = 0.001        # 每次交易数量 (BTC)
MARGIN_AMOUNT = 150.0  # 每次下单投入 150 USDT
MAX_SLIPPAGE = 0.01     # 允许最大滑点 1% (进阶功能预留)
TELEGRAM_TOKEN = '8077648998:AAGDEfU1NIsQCO1L8uLAIGoChOsPvKmebGE'
TELEGRAM_CHAT_ID = '8077648998'