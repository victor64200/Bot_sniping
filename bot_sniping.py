from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import os
import time
import logging

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialiser le client Binance
client = Client(API_KEY, API_SECRET)

# Paramètres
TRADING_PAIR = "NILUSDC"  # Ton trading pair
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
            qty = BUDGET_USDC / price
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
        time.sleep(0,1)  # Pause avant nouvelle tentative

def check_market():
    """Vérifie régulièrement si la crypto est disponible."""
    while True:
        try:
            ticker = client.get_symbol_ticker(symbol=TRADING_PAIR)
            price = float(ticker["price"])

            if price > 0:
                logger.info("📡 NIL détecté sur Binance ! Tentative d'achat immédiate...")
                buy_nil()
                break  # Sortir de la boucle après avoir acheté
        except BinanceAPIException as e:
            logger.error(f"⚠️ Erreur API Binance : {e}")
        except Exception as e:
            logger.error(f"⚠️ Erreur inattendue : {e}")
        
        time.sleep(1)  # Vérifie toutes les secondes

if __name__ == "__main__":
    logger.info("⏳ En attente de l'ouverture du marché NIL...")
    check_market()  # Démarre la vérification du marché
