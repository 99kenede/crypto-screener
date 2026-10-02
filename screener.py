import ccxt
import pandas as pd
import ta
import requests
import os
import json
from datetime import datetime, timezone

# Configurações
TIMEFRAME = '1h'
CCI_PERIOD = 100
CCI_THRESHOLD = 0

# Lista oficial da BreakoutProp (71 cryptos únicas, extraídas do seu arquivo)
SYMBOLS = [
    '1000BONK/USDT', '1000FLOKI/USDT', '1000PEPE/USDT', '1000SHIB/USDT',
    'AAVE/USDT', 'ADA/USDT', 'AIXBT/USDT', 'ALGO/USDT', 'APT/USDT',
    'ARB/USDT', 'ASTER/USDT', 'ATOM/USDT', 'AVAX/USDT', 'BCH/USDT',
    'BNB/USDT', 'BONK/USDT', 'BTC/USDT', 'CRV/USDT', 'DOGE/USDT',
    'DOT/USDT', 'ENA/USDT', 'ETC/USDT', 'ETH/USDT', 'ETHFI/USDT',
    'FARTCOIN/USDT', 'FIL/USDT', 'FLOKI/USDT', 'GRASS/USDT', 'HBAR/USDT',
    'HYPE/USDT', 'ICP/USDT', 'INJ/USDT', 'JTO/USDT', 'JUP/USDT',
    'KAITO/USDT', 'LDO/USDT', 'LINK/USDT', 'LIT/USDT', 'LTC/USDT',
    'MON/USDT', 'MOODENG/USDT', 'NEAR/USDT', 'ONDO/USDT', 'OP/USDT',
    'ORDI/USDT', 'PENDLE/USDT', 'PENGU/USDT', 'PEPE/USDT', 'PNUT/USDT',
    'POL/USDT', 'POPCAT/USDT', 'PUMP/USDT', 'RENDER/USDT', 'S/USDT',
    'SHIB/USDT', 'SOL/USDT', 'STX/USDT', 'SUI/USDT', 'TAO/USDT',
    'TIA/USDT', 'TRUMP/USDT', 'TRX/USDT', 'UNI/USDT', 'VIRTUAL/USDT',
    'WIF/USDT', 'WLD/USDT', 'XLM/USDT', 'XPL/USDT', 'XRP/USDT',
    'ZEC/USDT', 'ZRO/USDT'
]

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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

def get_tradingview_link(symbol, timeframe):
    """Gera link do TradingView para a crypto (Usando OKX Perpetual)"""
    tv_symbol = symbol.replace('/', '')
    return f'https://www.tradingview.com/chart/?symbol=OKX:{tv_symbol}.P&interval={timeframe}'

def calculate_cci(high, low, close, period):
    return ta.trend.cci(high, low, close, window=period)

def main():
    print(f"🚀 Iniciando screener - Timeframe: {TIMEFRAME}, CCI({CCI_PERIOD})")
    
    # Usando OKX (que não bloqueia o GitHub Actions)
    exchange = ccxt.okx()
    above_zero = []
    below_zero = []
    
    for symbol in SYMBOLS:
        try:
            # Busca candles suficientes para calcular CCI
            bars = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=CCI_PERIOD + 50)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calcula CCI
            df['cci'] = calculate_cci(df['high'], df['low'], df['close'], CCI_PERIOD)
            
            last_cci = df['cci'].iloc[-1]
            last_price = df['close'].iloc[-1]
            tv_link = get_tradingview_link(symbol, TIMEFRAME)
            
            crypto_data = {
                'symbol': symbol,
                'price': last_price,
                'cci': round(last_cci, 2),
                'tv_link': tv_link
            }
            
            if last_cci > CCI_THRESHOLD:
                above_zero.append(crypto_data)
                print(f"✅ {symbol}: CCI={last_cci:.2f}, Preço=${last_price:.2f}")
            else:
                below_zero.append(crypto_data)
                
        except Exception as e:
            print(f"❌ Erro em {symbol}: {e}")
    
    # Ordena por CCI (maior para menor)
    above_zero.sort(key=lambda x: x['cci'], reverse=True)
    below_zero.sort(key=lambda x: x['cci'], reverse=True)
    
    # Monta dados para o site (JSON)
    output_data = {
        'last_update': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC'),
        'timeframe': TIMEFRAME,
        'cci_period': CCI_PERIOD,
        'above_zero': above_zero,
        'below_zero': below_zero,
        'total_above': len(above_zero),
        'total_below': len(below_zero)
    }
    
    # Salva JSON para o site
    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("\n💾 results.json salvo com sucesso!")
    
    # Debug: Verifica se o arquivo foi criado no servidor do GitHub
    print(f"\n📁 Arquivos no diretório: {os.listdir('.')}")
    print(f"✅ results.json existe? {os.path.exists('results.json')}")
    
    # Monta mensagem para Telegram
    if above_zero:
        message = f"🚀 <b>CRYPTOS CCI({CCI_PERIOD}) > 0</b>\n"
        message += f"📊 Timeframe: {TIMEFRAME}\n"
        message += f"📅 {output_data['last_update']}\n\n"
        message += f"✅ <b>{len(above_zero)} acima de 0</b>\n"
        message += f"⏭️ <b>{len(below_zero)} abaixo de 0</b>\n\n"
        message += "<b>TOP 5 ACIMA:</b>\n"
        for r in above_zero[:5]:
            message += f"🔗 <a href='{r['tv_link']}'>{r['symbol']}</a> | CCI: {r['cci']} | ${r['price']:.2f}\n"
        
        send_telegram_message(message)
    else:
        message = f"⚠️ Nenhuma cripto com CCI({CCI_PERIOD}) > 0 no momento."
        send_telegram_message(message)
    
    print(f"\n✅ {len(above_zero)} acima de 0 | {len(below_zero)} abaixo de 0")

if __name__ == '__main__':
    main()
