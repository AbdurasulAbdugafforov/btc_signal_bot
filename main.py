import os
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import telegram

# 🔐 API kalitlarni yuklash
load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📡 Binance va Telegram sozlash
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

symbol = "BTCUSDT"
interval = "1m"

def get_klines(symbol, interval="1m", limit=200):
    candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(candles, columns=[
        'timestamp','open','high','low','close','volume',
        'close_time','qav','trades','tb_base','tb_quote','ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

def generate_features(df):
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
    df['ema_20'] = EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema_50'] = EMAIndicator(df['close'], window=50).ema_indicator()
    df['signal'] = np.where(df['ema_20'] > df['ema_50'], 1, -1)
    return df

def run_signal():
    df = get_klines(symbol)
    df = generate_features(df)

    latest = df.iloc[-1]
    signal = latest['signal']
    rsi = latest['rsi']

    if rsi < 30 and signal == 1:
        msg = "🚀 BUY signal: BTC/USDT \nRSI: {:.2f}".format(rsi)
    elif rsi > 70 and signal == -1:
        msg = "🔻 SELL signal: BTC/USDT \nRSI: {:.2f}".format(rsi)
    else:
        msg = "⏸ No clear signal. RSI: {:.2f}".format(rsi)

    bot.send_message(chat_id=CHAT_ID, text=msg)
    print(msg)

if __name__ == "__main__":
    while True:
        try:
            run_signal()
            time.sleep(60)
        except Exception as e:
            print("Xatolik:", e)
            time.sleep(60)
