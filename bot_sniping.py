from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import os
import time
import logging

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = Client(API_KEY, API_SECRET)

TRADING_PAIR = "NILUSDC"
BUDGET_USDC = 500
MAX_RETRIES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def buy_nil():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            ticker = client.get_symbol_ticker(symbol=TRADING_PAIR)
            price = float(ticker["price"])
            qty = BUDGET_USDC / price
            qty = round(qty, 6)

            order = client.order_market_buy(symbol=TRADING_PAIR, quantity=qty)
            logger.info(f"✅ Achat réussi : {qty} NIL à {price} USDC")
            return
        except BinanceAPIException as e:
            logger.error(f"⚠️ Erreur API Binance : {e}")
        except Exception as e:
            logger.error(f"⚠️ Erreur inattendue : {e}")
        
        retries += 1
        time.sleep(1)

def handle_message(msg):
    if msg['e'] == '24hrTicker':
        if float(msg['a']) > 0:
            logger.info("📡 NIL détecté sur Binance ! Tentative d'achat immédiate...")
            buy_nil()

if __name__ == "__main__":
    logger.info("⏳ En attente de l'ouverture du marché NIL...")
    bsm = BinanceSocketManager(client)
    conn_key = bsm.start_symbol_ticker_socket(TRADING_PAIR, handle_message)
    bsm.start()

