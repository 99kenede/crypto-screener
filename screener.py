import ccxt
import pandas as pd
import ta
import requests
import os
import sys

# Configurações
TIMEFRAME = '1h'
CCI_PERIOD = 100
CCI_THRESHOLD = 0

# Lista de cryptos (ajuste conforme necessário)
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
    'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT',
    'LINK/USDT', 'MATIC/USDT', 'LTC/USDT', 'BNB/USDT',
    'ARB/USDT', 'OP/USDT', 'SUI/USDT', 'APT/USDT',
    'NEAR/USDT', 'ATOM/USDT', 'UNI/USDT', 'FIL/USDT',
    'ICP/USDT', 'ETC/USDT', 'XLM/USDT', 'TRX/USDT',
    'ALGO/USDT', 'VET/USDT', 'FTM/USDT', 'SAND/USDT',
    'MANA/USDT', 'AXS/USDT', 'AAVE/USDT', 'GRT/USDT',
]

# Telegram config (vem do GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Envia mensagem para o Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado. Apenas logando no console.")
        print(message)
        return
    
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Alerta enviado para Telegram")
        else:
            print(f"❌ Erro ao enviar Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")

def calculate_cci(high, low, close, period):
    """Calcula CCI usando ta-lib"""
    return ta.trend.cci(high, low, close, window=period)

def main():
    print(f"🚀 Iniciando screener - Timeframe: {TIMEFRAME}, CCI({CCI_PERIOD}) > {CCI_THRESHOLD}")
    
    exchange = exchange = ccxt.bybit()
    results = []
    
    for symbol in SYMBOLS:
        try:
            # Busca candles suficientes para calcular CCI
            bars = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=CCI_PERIOD + 50)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calcula CCI
            df['cci'] = calculate_cci(df['high'], df['low'], df['close'], CCI_PERIOD)
            
            last_cci = df['cci'].iloc[-1]
            last_price = df['close'].iloc[-1]
            
            if last_cci > CCI_THRESHOLD:
                results.append({
                    'symbol': symbol,
                    'price': last_price,
                    'cci': round(last_cci, 2)
                })
                print(f"✅ {symbol}: CCI={last_cci:.2f}, Preço=${last_price:.2f}")
            else:
                print(f"⏭️ {symbol}: CCI={last_cci:.2f} (abaixo do threshold)")
                
        except Exception as e:
            print(f"❌ Erro em {symbol}: {e}")
    
    # Monta mensagem para Telegram
    if results:
        message = "🚀 <b>CRYPTOS COM CCI(100) > 0</b>\n\n"
        message += f"📊 Timeframe: {TIMEFRAME}\n"
        message += f"📅 {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M UTC')}\n\n"
        
        for r in sorted(results, key=lambda x: x['cci'], reverse=True):
            message += f"<b>{r['symbol']}</b>\n"
            message += f"💰 Preço: ${r['price']:.2f}\n"
            message += f"📈 CCI: {r['cci']}\n\n"
        
        send_telegram_message(message)
        print(f"\n✅ {len(results)} cryptos encontradas com CCI > {CCI_THRESHOLD}")
    else:
        message = "⚠️ Nenhuma cripto com CCI(100) > 0 no momento."
        send_telegram_message(message)
        print("\n⚠️ Nenhuma cripto encontrada")

if __name__ == '__main__':
    main()
