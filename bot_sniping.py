import os
import time
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialiser le client Binance
client = Client(API_KEY, API_SECRET)

# Paramètres
TRADING_PAIR = "REDUSDT"
BUDGET_USDT = 500
MAX_RED_QTY = 5000  # Limite de quantité de RED achetable
SLEEP_INTERVAL = 0.001  # Pause minimale entre chaque tentative

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def is_symbol_listed(symbol):
    """Vérifie si la paire de trading est listée sur Binance."""
    try:
        info = client.get_symbol_info(symbol)
        if info and "filters" in info:
            logger.info(f"La paire {symbol} est listée.")
            return True
        else:
            logger.warning(f"La paire {symbol} n'est pas encore listée.")
            return False
    except BinanceAPIException as e:
        logger.error(f"Erreur API Binance: {e}")
        return False

def get_market_rules():
    """Récupère les règles du marché (stepSize, minQty) pour ajuster la quantité d'achat."""
    try:
        info = client.get_symbol_info(TRADING_PAIR)
        lot_size_filter = next(f for f in info["filters"] if f["filterType"] == "LOT_SIZE")
        min_qty = float(lot_size_filter["minQty"])
        step_size = float(lot_size_filter["stepSize"])
        return min_qty, step_size
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des règles du marché : {e}")
        return 0.01, 0.01  # Valeurs par défaut en cas d'échec

def round_quantity(qty, step_size):
    """Ajuste la quantité au step_size de Binance (floor pour éviter les erreurs)."""
    return (qty // step_size) * step_size

def get_price():
    """Récupère le dernier prix du marché."""
    try:
        ticker = client.get_symbol_ticker(symbol=TRADING_PAIR)
        return float(ticker["price"])
    except BinanceAPIException as e:
        logger.error(f"Erreur API Binance: {e}")
        return None

def is_order_filled(order_id):
    """Vérifie si l'ordre a été rempli."""
    try:
        order = client.get_order(symbol=TRADING_PAIR, orderId=order_id)
        return order['status'] == 'FILLED'
    except BinanceAPIException as e:
        logger.error(f"Erreur lors de la vérification de l'ordre : {e}")
        return False

def buy_red():
    """Tente d'acheter du RED en boucle jusqu'à réussite."""
    min_qty, step_size = get_market_rules()

    while True:  # La boucle continue jusqu'à ce que l'achat réussisse
        try:
            price = get_price()
            if price is None:
                time.sleep(SLEEP_INTERVAL)
                continue  # Réessayer si le prix n'est pas disponible

            qty = BUDGET_USDT / price  # Calcul initial de la quantité
            qty = round_quantity(qty, step_size)  # Ajustement au step_size

            # Appliquer la limite de 5000 RED max
            if qty > MAX_RED_QTY:
                qty = MAX_RED_QTY

            # Vérifier si la quantité ajustée est au-dessus du minimum requis
            if qty < min_qty:
                logger.warning(f"Quantité ajustée ({qty}) trop basse. Impossible d'acheter.")
                continue

            # Passer l'ordre d'achat
            order = client.order_market_buy(symbol=TRADING_PAIR, quantity=qty)
            order_id = order['orderId']
            logger.info(f"✅ Tentative d'achat : {qty} RED pour {BUDGET_USDT:.2f} USDT (prix: {price} USDT)")

            # Vérifier si l'ordre a bien été exécuté
            if is_order_filled(order_id):
                logger.info(f"✅ Achat confirmé : {qty} RED à {price} USDT")
                return qty, price
            else:
                logger.warning("⚠️ L'ordre n'a pas été exécuté. Nouvelle tentative...")

        except BinanceAPIException as e:
            logger.error(f"⚠️ Erreur API Binance lors de l'achat : {e}")
        except Exception as e:
            logger.error(f"⚠️ Erreur inattendue : {e}")

        # Pause minimale avant la prochaine tentative
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    logger.info("⏳ En attente de l'achat de RED...")
    qty, buy_price = buy_red()

    if qty and buy_price:
        logger.info(f"💰 Achat réussi : {qty} RED à {buy_price} USDT")
    else:
        logger.error("❌ Échec de l'achat après plusieurs tentatives.")
