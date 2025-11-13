#!/usr/bin/env python3
"""
Gestionnaire de positions simplifié
Récupère les positions ouvertes et permet de les fermer
"""

import asyncio
import sys
import os
from typing import Dict, List, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'lighter'))
sys.path.insert(0, os.path.join(current_dir, 'paradex'))

from logger import setup_logger

logger = setup_logger("position_manager")

LIGHTER_MARKET_IDS = {
    "BTC": 0,
    "ETH": 1
}


async def get_lighter_position(token: str) -> Optional[Dict]:
    """Récupère la position Lighter pour un token"""
    try:
        from lighter.v2_client import SignerClient as LighterSignerClient
        from lighter.lighter_trader_config import BASE_URL, PRIVATE_KEY, ACCOUNT_INDEX, API_KEY_INDEX
        
        client = LighterSignerClient(
            base_url=BASE_URL,
            api_auth=PRIVATE_KEY,
            api_key_index=API_KEY_INDEX,
            account_index=ACCOUNT_INDEX
        )
        
        # Récupérer l'état du compte
        account = client.get_account()
        
        if not account:
            client.close()
            return None
        
        # Extraire les positions
        market_id = LIGHTER_MARKET_IDS.get(token)
        if market_id is None:
            client.close()
            return None
        
        positions = getattr(account, 'positions', []) or []
        
        for pos in positions:
            pos_market = getattr(pos, 'market_id', None) or getattr(pos, 'market_index', None)
            if pos_market == market_id:
                size = float(getattr(pos, 'size', 0) or getattr(pos, 'base_amount', 0) or 0)
                entry_price = float(getattr(pos, 'entry_price', 0) or 0)
                liq_price = float(getattr(pos, 'liquidation_price', 0) or 0)
                
                # Déterminer LONG/SHORT selon liquidation_price
                if abs(size) > 0.00001:
                    is_short = liq_price > entry_price if (liq_price > 0 and entry_price > 0) else False
                    if is_short:
                        size = -abs(size)
                    
                    client.close()
                    return {
                        "token": token,
                        "size": size,
                        "entry_price": entry_price,
                        "liquidation_price": liq_price,
                        "direction": "SHORT" if size < 0 else "LONG"
                    }
        
        client.close()
        return None
        
    except Exception as e:
        logger.error(f"Erreur Lighter position: {e}")
        return None


async def get_paradex_position(token: str) -> Optional[Dict]:
    """Récupère la position Paradex pour un token"""
    try:
        from paradex_py import Paradex
        from paradex.paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS, TOKEN_MARKET
        
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        
        market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
        positions = paradex.api_client.fetch_positions()
        
        if positions and 'results' in positions:
            for pos in positions['results']:
                if pos.get('market') == market and pos.get('status') == 'OPEN':
                    size = float(pos.get('size', 0) or 0)
                    if abs(size) > 0.00001:
                        return {
                            "token": token,
                            "size": size,
                            "entry_price": float(pos.get('avg_entry_price', 0) or 0),
                            "liquidation_price": float(pos.get('liquidation_price', 0) or 0),
                            "direction": "SHORT" if size < 0 else "LONG"
                        }
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur Paradex position: {e}")
        return None


async def get_all_positions(token: str) -> Dict:
    """Récupère toutes les positions pour un token"""
    lighter_pos, paradex_pos = await asyncio.gather(
        get_lighter_position(token),
        get_paradex_position(token),
        return_exceptions=True
    )
    
    if isinstance(lighter_pos, Exception):
        lighter_pos = None
    if isinstance(paradex_pos, Exception):
        paradex_pos = None
    
    return {
        "lighter": lighter_pos,
        "paradex": paradex_pos
    }


async def close_all_positions(token: str, lighter_bid: float, lighter_ask: float,
                              paradex_bid: float, paradex_ask: float, leverage: int = 50) -> Dict:
    """
    Ferme toutes les positions ouvertes
    
    Args:
        token: Token à fermer
        lighter_bid, lighter_ask: Prix Lighter actuels
        paradex_bid, paradex_ask: Prix Paradex actuels
        leverage: Levier utilisé
    
    Returns:
        Dict avec les résultats
    """
    from trade_executor_simple import execute_lighter_trade, execute_paradex_trade
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔄 FERMETURE DES POSITIONS")
    logger.info("=" * 80)
    
    # Récupérer les positions
    positions = await get_all_positions(token)
    lighter_pos = positions["lighter"]
    paradex_pos = positions["paradex"]
    
    logger.info(f"   ⚡ Lighter: {lighter_pos['direction'] if lighter_pos else 'AUCUNE'}")
    logger.info(f"   🎯 Paradex: {paradex_pos['direction'] if paradex_pos else 'AUCUNE'}")
    logger.info("=" * 80)
    logger.info("")
    
    tasks = []
    
    # Fermer Lighter si position existe
    if lighter_pos and abs(lighter_pos["size"]) > 0.00001:
        # Position LONG → SELL pour fermer
        # Position SHORT → BUY pour fermer
        order_type = "sell" if lighter_pos["size"] > 0 else "buy"
        amount = abs(lighter_pos["size"])
        
        logger.info(f"   ⚡ Fermeture Lighter: {order_type.upper()} {amount:.8f} {token}")
        tasks.append(execute_lighter_trade(token, amount, leverage, order_type, lighter_bid, lighter_ask))
    
    # Fermer Paradex si position existe
    if paradex_pos and abs(paradex_pos["size"]) > 0.00001:
        order_type = "sell" if paradex_pos["size"] > 0 else "buy"
        amount = abs(paradex_pos["size"])
        
        logger.info(f"   🎯 Fermeture Paradex: {order_type.upper()} {amount:.8f} {token}")
        tasks.append(execute_paradex_trade(token, amount, leverage, order_type, paradex_bid, paradex_ask))
    
    if not tasks:
        logger.info("   ✅ Aucune position à fermer")
        return {"success": True, "message": "Aucune position"}
    
    # Exécuter les fermetures en parallèle
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Vérifier les résultats
    all_success = all(
        r.get("success") if isinstance(r, dict) else False 
        for r in results
    )
    
    if all_success:
        logger.info("")
        logger.info("✅ POSITIONS FERMÉES AVEC SUCCÈS")
    else:
        logger.error("")
        logger.error("❌ ÉCHEC FERMETURE DE CERTAINES POSITIONS")
    
    return {
        "success": all_success,
        "results": results
    }

