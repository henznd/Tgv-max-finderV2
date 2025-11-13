#!/usr/bin/env python3
"""
Exécuteur de trades simplifié pour l'arbitrage
Version propre sans subprocess, directe et fiable
"""

import asyncio
import sys
import os
from typing import Optional, Dict, Tuple
from datetime import datetime

# Ajouter les chemins nécessaires
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'lighter'))
sys.path.insert(0, os.path.join(current_dir, 'paradex'))

from logger import setup_logger

logger = setup_logger("trade_executor")


async def execute_lighter_trade(token: str, amount: float, leverage: int, 
                                order_type: str, bid: float, ask: float) -> Dict:
    """
    Exécute un trade Lighter directement (sans subprocess)
    
    Args:
        token: Token à trader (BTC, ETH)
        amount: Montant en token
        leverage: Levier
        order_type: "buy" ou "sell"
        bid: Prix bid actuel
        ask: Prix ask actuel
    
    Returns:
        Dict avec success, tx_hash, etc.
    """
    try:
        # Import du SDK Lighter
        from lighter.v2_client import SignerClient as LighterSignerClient
        from lighter.lighter_trader_config import (
            BASE_URL, PRIVATE_KEY, ACCOUNT_INDEX, API_KEY_INDEX, LIGHTER_MARKET_IDS
        )
        
        logger.info(f"⚡ LIGHTER - {order_type.upper()} {amount:.8f} {token}")
        logger.info(f"   Prix bid/ask: ${bid:.2f} / ${ask:.2f}")
        logger.info(f"   Levier: {leverage}x")
        
        # Créer le client
        client = LighterSignerClient(
            base_url=BASE_URL,
            api_auth=PRIVATE_KEY,
            api_key_index=API_KEY_INDEX,
            account_index=ACCOUNT_INDEX
        )
        
        # Récupérer le market_id
        market_id = LIGHTER_MARKET_IDS.get(token)
        if market_id is None:
            raise ValueError(f"Token {token} non supporté par Lighter")
        
        # Déterminer is_ask
        is_ask = (order_type.lower() == 'sell')
        
        # Calculer avg_execution_price (CAP)
        # Pour contrôler le slippage, on calcule le cap depuis le prix médian avec une tolérance
        mid_price = (bid + ask) / 2
        SLIPPAGE_TOLERANCE = 0.005  # 0.5% de slippage toléré
        
        if is_ask:
            # Ordre de VENTE: cap MINIMUM (le prix moyen ne doit pas descendre en dessous)
            market_price = mid_price * (1 - SLIPPAGE_TOLERANCE)
        else:
            # Ordre d'ACHAT: cap MAXIMUM (le prix moyen ne doit pas dépasser)
            market_price = mid_price * (1 + SLIPPAGE_TOLERANCE)
        
        # CORRECTION FACTEUR 10: Lighter attend le prix multiplié par 10
        avg_execution_price = int(float(market_price) * 10)
        
        logger.info(f"   💲 Prix cap: ${market_price:.2f} = {avg_execution_price} (prix * 10)")
        
        # Calculer order_size_units
        if token == "BTC":
            order_size_units = int(amount * 1e5)  # 1 BTC = 100,000 unités
            logger.info(f"   📏 Taille: {amount} BTC = {order_size_units} unités (1e5)")
        else:
            order_size_units = int(amount * 1e4)  # 1 ETH = 10,000 unités
            logger.info(f"   📏 Taille: {amount} {token} = {order_size_units} unités (1e4)")
        
        # Générer client_order_index unique
        client_order_index = int(datetime.now().timestamp() * 1000) % (2**32)
        
        # Créer l'ordre
        logger.info(f"   🚀 Envoi de l'ordre...")
        
        order_data = client.create_market_order(
            market_id=market_id,
            order_size_units=order_size_units,
            avg_execution_price=avg_execution_price,
            is_ask=is_ask,
            client_order_index=client_order_index
        )
        
        if order_data:
            tx_hash = order_data.get('orderData', {}).get('tx_hash') or order_data.get('tx_hash')
            logger.info(f"   ✅ Ordre Lighter exécuté: {tx_hash}")
            
            # Fermer le client
            try:
                client.close()
            except:
                pass
            
            return {
                "success": True,
                "exchange": "lighter",
                "tx_hash": tx_hash,
                "order_type": order_type,
                "amount": amount,
                "token": token
            }
        else:
            logger.error(f"   ❌ Ordre Lighter échoué: pas de réponse")
            try:
                client.close()
            except:
                pass
            return {"success": False, "error": "Pas de réponse de Lighter"}
            
    except Exception as e:
        logger.error(f"   ❌ Erreur Lighter: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


async def execute_paradex_trade(token: str, amount: float, leverage: int,
                                order_type: str, bid: float, ask: float) -> Dict:
    """
    Exécute un trade Paradex directement (sans subprocess)
    
    Args:
        token: Token à trader (BTC, ETH)
        amount: Montant en token
        leverage: Levier
        order_type: "buy" ou "sell"
        bid: Prix bid actuel
        ask: Prix ask actuel
    
    Returns:
        Dict avec success, order_id, etc.
    """
    try:
        # Import du SDK Paradex
        from paradex_py import Paradex
        from paradex.paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS, TOKEN_MARKET
        from decimal import Decimal, ROUND_HALF_UP
        
        logger.info(f"🎯 PARADEX - {order_type.upper()} {amount:.8f} {token}")
        logger.info(f"   Prix bid/ask: ${bid:.2f} / ${ask:.2f}")
        logger.info(f"   Levier: {leverage}x")
        
        # Créer le client
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        
        # Récupérer le market
        market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
        
        # Arrondir le montant
        if token == "BTC":
            tick_size = Decimal('0.00001')  # 5 décimales pour BTC
        else:
            tick_size = Decimal('0.0001')   # 4 décimales pour autres
        
        amount_decimal = Decimal(str(amount))
        amount_rounded = (amount_decimal / tick_size).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * tick_size
        amount_str = str(amount_rounded)
        
        logger.info(f"   📏 Montant arrondi: {amount_str} {token}")
        
        # Déterminer side
        side = "SELL" if order_type.lower() == "sell" else "BUY"
        
        # Créer l'ordre market
        logger.info(f"   🚀 Envoi de l'ordre...")
        
        order_response = paradex.api_client.create_order(
            market=market,
            order_type="MARKET",
            side=side,
            size=amount_str
        )
        
        if order_response and order_response.get('id'):
            order_id = order_response['id']
            logger.info(f"   ✅ Ordre Paradex exécuté: {order_id}")
            
            return {
                "success": True,
                "exchange": "paradex",
                "order_id": order_id,
                "order_type": order_type,
                "amount": amount,
                "token": token
            }
        else:
            logger.error(f"   ❌ Ordre Paradex échoué: {order_response}")
            return {"success": False, "error": "Pas de réponse de Paradex"}
            
    except Exception as e:
        logger.error(f"   ❌ Erreur Paradex: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


async def execute_arbitrage_trade(direction: str, token: str, margin: float, leverage: int,
                                  lighter_bid: float, lighter_ask: float,
                                  paradex_bid: float, paradex_ask: float) -> Dict:
    """
    Exécute un trade d'arbitrage complet (les deux côtés simultanément)
    
    Args:
        direction: 'sell_lighter' ou 'sell_paradex'
        token: Token à trader
        margin: Marge par position
        leverage: Levier
        lighter_bid, lighter_ask: Prix Lighter
        paradex_bid, paradex_ask: Prix Paradex
    
    Returns:
        Dict avec success, lighter_result, paradex_result
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"🚀 EXÉCUTION ARBITRAGE - {direction.upper()}")
    logger.info("=" * 80)
    logger.info(f"   Token: {token}")
    logger.info(f"   Marge: ${margin}, Levier: {leverage}x")
    logger.info(f"   Lighter bid/ask: ${lighter_bid:.2f} / ${lighter_ask:.2f}")
    logger.info(f"   Paradex bid/ask: ${paradex_bid:.2f} / ${paradex_ask:.2f}")
    
    # Calculer le spread
    if direction == 'sell_lighter':
        spread = lighter_bid - paradex_ask
        lighter_order_type = "sell"
        paradex_order_type = "buy"
        logger.info(f"   📊 Spread: ${spread:.2f} (Lighter SELL, Paradex BUY)")
    else:  # sell_paradex
        spread = paradex_bid - lighter_ask
        lighter_order_type = "buy"
        paradex_order_type = "sell"
        logger.info(f"   📊 Spread: ${spread:.2f} (Lighter BUY, Paradex SELL)")
    
    # Calculer les montants
    position_value = margin * leverage
    lighter_mid = (lighter_bid + lighter_ask) / 2
    paradex_mid = (paradex_bid + paradex_ask) / 2
    
    lighter_amount = position_value / lighter_mid
    paradex_amount = position_value / paradex_mid
    
    logger.info(f"   💰 Position totale: ${position_value:.2f}")
    logger.info(f"   ⚡ Lighter: {lighter_order_type.upper()} {lighter_amount:.8f} {token}")
    logger.info(f"   🎯 Paradex: {paradex_order_type.upper()} {paradex_amount:.8f} {token}")
    logger.info("=" * 80)
    logger.info("")
    
    # Exécuter les deux trades en parallèle (atomicité maximale)
    start_time = datetime.now()
    
    lighter_result, paradex_result = await asyncio.gather(
        execute_lighter_trade(token, lighter_amount, leverage, lighter_order_type, lighter_bid, lighter_ask),
        execute_paradex_trade(token, paradex_amount, leverage, paradex_order_type, paradex_bid, paradex_ask),
        return_exceptions=True
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Gérer les exceptions
    if isinstance(lighter_result, Exception):
        lighter_result = {"success": False, "error": str(lighter_result)}
    if isinstance(paradex_result, Exception):
        paradex_result = {"success": False, "error": str(paradex_result)}
    
    # Résultats
    logger.info("")
    logger.info("=" * 80)
    if lighter_result.get("success") and paradex_result.get("success"):
        logger.info("✅ ARBITRAGE RÉUSSI")
        logger.info("=" * 80)
        logger.info(f"   ⏱️  Durée: {duration:.2f}s")
        logger.info(f"   ⚡ Lighter: {lighter_result.get('tx_hash', 'N/A')}")
        logger.info(f"   🎯 Paradex: {paradex_result.get('order_id', 'N/A')}")
        success = True
    else:
        logger.error("❌ ARBITRAGE ÉCHOUÉ")
        logger.error("=" * 80)
        logger.error(f"   ⏱️  Durée: {duration:.2f}s")
        if not lighter_result.get("success"):
            logger.error(f"   ⚡ Lighter: {lighter_result.get('error', 'Erreur inconnue')}")
        if not paradex_result.get("success"):
            logger.error(f"   🎯 Paradex: {paradex_result.get('error', 'Erreur inconnue')}")
        success = False
    
    logger.info("=" * 80)
    logger.info("")
    
    return {
        "success": success,
        "duration": duration,
        "lighter": lighter_result,
        "paradex": paradex_result,
        "spread": spread
    }

