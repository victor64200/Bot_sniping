import os
import time
import logging
from binance.client import Client
from binance.streams import BinanceSocketManager
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialiser le client Binance
client = Client(API_KEY, API_SECRET)

# Paramètres
TRADING_PAIR = "NILUSDC"
BUDGET_USDC = 500  # Montant que tu veux investir
MAX_RETRIES = 3  # Nombre max de tentatives en cas d'échec

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def buy_nil():
    """Tente d'acheter du NIL dès qu'il devient achetable."""
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            # Récupérer le dernier prix
            ticker = client.get_symbol_ticker(symbol=TRADING_PAIR)
            price = float(ticker["price"])

            # Calculer la quantité d'achat pour 500 USDC
            qty = BUDGET_USDC / price  # Calcul de la quantité

            # Arrondir la quantité à 6 décimales maximum (par exemple pour un prix très précis)
            qty = round(qty, 6)

            # Passer l'ordre d'achat
            order = client.order_market_buy(symbol=TRADING_PAIR, quantity=qty)
            logger.info(f"✅ Achat réussi : {qty} NIL à {price} USDC")
            return
        except BinanceAPIException as e:
            logger.error(f"⚠️ Erreur API Binance : {e}")
        except Exception as e:
            logger.error(f"⚠️ Erreur inattendue : {e}")
        
        retries += 1
        time.sleep(0.01)  # Pause ultra courte avant nouvelle tentative

# Détection en temps réel avec WebSocket
def handle_message(msg):
    """Gère les messages WebSocket et tente d'acheter dès que la paire devient disponible."""
    if msg['e'] == '24hrTicker':
        if float(msg['a']) > 0:  # Si la paire est maintenant disponible (prix > 0)
            logger.info("📡 NIL détecté sur Binance ! Tentative d'achat immédiate...")
            buy_nil()
            exit()

if __name__ == "__main__":
    logger.info("⏳ En attente de l'ouverture du marché NIL...")
    bsm = BinanceSocketManager(client)
    conn_key = bsm.start_symbol_ticker_socket(TRADING_PAIR, handle_message)
    bsm.start()

