import os
import ccxt
import config

# 1. 强制代理
proxy_url = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = proxy_url
os.environ['https_proxy'] = proxy_url

# 2. 实例化
exchange = ccxt.binance({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    }
})

# --- 【关键：手动指向 Demo Trading 专用网关】 ---
# 不要调用 set_sandbox_mode(True)，否则会被 CCXT 拦截
# 直接强行修改以下两个 URL
exchange.urls['api']['public'] = 'https://testnet.binancefuture.com/fapi'
exchange.urls['api']['private'] = 'https://testnet.binancefuture.com/fapi'

try:
    print(f"正在尝试连接 Demo Trading 专用网关...")

    # 验证时间
    st = exchange.fapiPublicGetTime()
    print(f"✅ 网关连接成功！")

    # 获取余额
    print("正在验证 API Key...")
    account = exchange.fapiPrivateGetAccount()

    print(f"✅ API 验证成功！")
    print(f"模拟账户 USDT 总余额: {account['totalWalletBalance']} USDT")

except Exception as e:
    print(f"\n❌ 出错详情:")
    print(e)