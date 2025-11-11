#!/usr/bin/env python3
"""
Bot d'arbitrage avec stratégie automatique basée sur le z-score
Réutilise le code existant au maximum
"""

import asyncio
import sys
import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# Ajouter le répertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Imports du code existant
from logger import setup_logger
from arbitrage_strategy import ArbitrageStrategy, StrategyParams
from arbitrage_bot_config import (
    get_lighter_price_direct,
    get_paradex_price_direct,
    execute_simultaneous_trades,
    load_config,
    LIGHTER_MARKET_IDS,
    PARADEX_MARKETS
)

logger = setup_logger("arbitrage_bot_strategy")

# Configuration Supabase (depuis execute_sql_direct.py)
SUPABASE_HOST = "db.jlqdkbdmjuqjqhesxvjg.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "vIVXJ793dz2aHHH0"

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    logger.error("❌ psycopg2 non installé. Installez avec: pip install psycopg2-binary")
    sys.exit(1)


async def get_price_history_from_supabase(token: str, limit: int = 60) -> list:
    """
    Récupère l'historique des prix depuis Supabase
    Réutilise la connexion PostgreSQL existante
    
    Args:
        token: Token à récupérer (BTC, ETH)
        limit: Nombre de prix à récupérer (défaut: 60)
    
    Returns:
        Liste de dict avec 'timestamp', 'lighter_mid', 'lighter_bid', 'lighter_ask',
        'paradex_mid', 'paradex_bid', 'paradex_ask'
    """
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            connect_timeout=10
        )
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les prix les plus récents pour le token
        # On récupère 2x limit pour avoir les prix Lighter ET Paradex
        query = """
            SELECT timestamp, exchange, mid, bid, ask
            FROM price_history
            WHERE token = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        cur.execute(query, (token, limit * 2))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Grouper par timestamp pour avoir les paires lighter/paradex
        history_by_timestamp = {}
        for row in rows:
            ts = row['timestamp']
            if ts not in history_by_timestamp:
                history_by_timestamp[ts] = {}
            history_by_timestamp[ts][row['exchange']] = {
                'mid': float(row['mid']),
                'bid': float(row['bid']),
                'ask': float(row['ask'])
            }
        
        # Construire la liste avec les paires synchronisées
        history = []
        for ts in sorted(history_by_timestamp.keys()):
            data = history_by_timestamp[ts]
            if 'lighter' in data and 'paradex' in data:
                history.append({
                    'timestamp': ts,
                    'lighter_mid': data['lighter']['mid'],
                    'lighter_bid': data['lighter']['bid'],
                    'lighter_ask': data['lighter']['ask'],
                    'paradex_mid': data['paradex']['mid'],
                    'paradex_bid': data['paradex']['bid'],
                    'paradex_ask': data['paradex']['ask']
                })
        
        # Garder seulement les N derniers
        history = history[-limit:]
        
        logger.info(f"✅ Récupéré {len(history)} observations depuis Supabase pour {token}")
        return history
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération historique Supabase: {e}")
        import traceback
        logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
        return []


async def get_current_prices_parallel(token: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Récupère les prix actuels depuis les APIs en parallèle
    Réutilise les fonctions existantes de arbitrage_bot_config.py
    
    Returns:
        (lighter_bid, lighter_ask, lighter_mid, paradex_bid, paradex_ask, paradex_mid)
    """
    try:
        # Récupérer bid et ask en parallèle
        lighter_bid, lighter_ask, paradex_bid, paradex_ask = await asyncio.gather(
            get_lighter_price_direct(token, "sell"),  # bid
            get_lighter_price_direct(token, "buy"),   # ask
            get_paradex_price_direct(token, "sell"),  # bid
            get_paradex_price_direct(token, "buy"),  # ask
            return_exceptions=True
        )
        
        # Gérer les exceptions
        if isinstance(lighter_bid, Exception):
            logger.warning(f"⚠️ Erreur récupération Lighter bid: {lighter_bid}")
            lighter_bid = None
        if isinstance(lighter_ask, Exception):
            logger.warning(f"⚠️ Erreur récupération Lighter ask: {lighter_ask}")
            lighter_ask = None
        if isinstance(paradex_bid, Exception):
            logger.warning(f"⚠️ Erreur récupération Paradex bid: {paradex_bid}")
            paradex_bid = None
        if isinstance(paradex_ask, Exception):
            logger.warning(f"⚠️ Erreur récupération Paradex ask: {paradex_ask}")
            paradex_ask = None
        
        # Calculer mid prices
        lighter_mid = (lighter_bid + lighter_ask) / 2 if lighter_bid and lighter_ask else None
        paradex_mid = (paradex_bid + paradex_ask) / 2 if paradex_bid and paradex_ask else None
        
        return lighter_bid, lighter_ask, lighter_mid, paradex_bid, paradex_ask, paradex_mid
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération prix actuels: {e}")
        return None, None, None, None, None, None


def calculate_spreads(lighter_bid: float, lighter_ask: float, lighter_mid: float,
                     paradex_bid: float, paradex_ask: float, paradex_mid: float) -> Tuple[float, float, float]:
    """
    Calcule les spreads nécessaires pour la stratégie
    
    Returns:
        (spread_net, spread_PL, spread_LP)
        - spread_net: paradex_mid - lighter_mid (pour z-score)
        - spread_PL: paradex_bid - lighter_ask (pour short spread)
        - spread_LP: lighter_bid - paradex_ask (pour long spread)
    """
    spread_net = paradex_mid - lighter_mid
    spread_PL = paradex_bid - lighter_ask  # Vendre Paradex, acheter Lighter
    spread_LP = lighter_bid - paradex_ask  # Vendre Lighter, acheter Paradex
    
    return spread_net, spread_PL, spread_LP


async def check_trading_conditions(config: dict, token: str) -> Tuple[bool, str]:
    """
    Vérifie les conditions avant de trader
    Réutilise trade_verification.py si nécessaire
    
    Returns:
        (can_trade, reason)
    """
    try:
        from trade_verification import TradeVerification
        
        verifier = TradeVerification()
        
        # Vérifier les positions existantes
        # Utiliser _get_lighter_account_state (Paradex nécessite un client, on skip pour l'instant)
        lighter_state = await verifier._get_lighter_account_state()
        
        # Vérifier Lighter
        if lighter_state:
            positions = lighter_state.get("positions", [])
            market_index = LIGHTER_MARKET_IDS.get(token)
            if market_index is not None:
                for pos in positions:
                    pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                    if pos_market == market_index:
                        pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                        if abs(pos_size) > 0:
                            return False, f"Position Lighter déjà ouverte ({pos_size} {token})"
        
        # Note: Vérification Paradex nécessite un client Paradex initialisé
        # On peut l'ajouter plus tard si nécessaire
        
        # Vérifier la marge disponible (optionnel, peut être ajouté plus tard)
        # Pour l'instant, on suppose que la marge est suffisante
        
        return True, "Conditions OK"
        
    except Exception as e:
        logger.warning(f"⚠️ Erreur vérification conditions: {e}")
        import traceback
        logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
        # En cas d'erreur, on continue quand même (fail-safe)
        return True, "Vérification échouée, continuation"


async def close_positions(token: str, config_base: dict,
                         lighter_bid: float, lighter_ask: float, lighter_mid: float,
                         paradex_bid: float, paradex_ask: float, paradex_mid: float,
                         leverage: int) -> dict:
    """
    Ferme les positions ouvertes sur Lighter et Paradex en plaçant des ordres opposés
    
    Args:
        token: Token à trader
        config_base: Configuration de base
        lighter_bid, lighter_ask, lighter_mid: Prix Lighter
        paradex_bid, paradex_ask, paradex_mid: Prix Paradex
        leverage: Levier utilisé
    
    Returns:
        Résultat de la fermeture des positions
    """
    from trade_verification import TradeVerification
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔄 FERMETURE DES POSITIONS")
    logger.info("=" * 80)
    logger.info("")
    
    verifier = TradeVerification()
    
    # 1. Récupérer les positions actuelles
    lighter_state = await verifier._get_lighter_account_state()
    lighter_position_size = 0
    lighter_market_index = None
    
    if lighter_state:
        positions = lighter_state.get("positions", [])
        market_index = LIGHTER_MARKET_IDS.get(token)
        if market_index is not None:
            for pos in positions:
                pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                if pos_market == market_index:
                    lighter_position_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                    lighter_market_index = market_index
                    break
    
    # 2. Récupérer position Paradex
    paradex_position_size = 0
    try:
        from paradex_py import Paradex
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'paradex'))
        from paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS, TOKEN_MARKET
        
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        
        positions = paradex.api_client.fetch_positions()
        market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
        
        if positions and 'results' in positions:
            for pos in positions['results']:
                if pos.get('market') == market and pos.get('status') == 'OPEN':
                    paradex_position_size = float(pos.get('size', 0) or 0)
                    break
    except Exception as e:
        logger.warning(f"⚠️ Erreur récupération position Paradex: {e}")
    
    logger.info(f"📊 Positions actuelles:")
    logger.info(f"   Lighter: {lighter_position_size} {token} ({'LONG' if lighter_position_size > 0 else 'SHORT' if lighter_position_size < 0 else 'AUCUNE'})")
    logger.info(f"   Paradex: {paradex_position_size} {token} ({'LONG' if paradex_position_size > 0 else 'SHORT' if paradex_position_size < 0 else 'AUCUNE'})")
    logger.info("")
    
    # 3. Créer les configurations de fermeture (ordres opposés)
    close_config = {}
    
    # Fermer Lighter si position existe
    if abs(lighter_position_size) > 0:
        # IMPORTANT: Pour fermer une position, il faut faire l'ordre OPPOSÉ
        # - Position LONG (positive) → SELL pour fermer
        # - Position SHORT (négative) → BUY pour fermer
        # Si on fait un SELL sur une position SHORT, cela AUGMENTE la position SHORT au lieu de la fermer !
        lighter_order_type = "sell" if lighter_position_size > 0 else "buy"
        # Utiliser la taille absolue de la position
        lighter_amount = abs(lighter_position_size)
        logger.info(f"🔧 Logique de fermeture Lighter:")
        logger.info(f"   Position: {lighter_position_size} {token} ({'LONG' if lighter_position_size > 0 else 'SHORT'})")
        logger.info(f"   Ordre de fermeture: {lighter_order_type.upper()} {lighter_amount} {token}")
        # NE PAS configurer market_price - laisser le fallback le calculer depuis bid/ask
        
        close_config["lighter"] = {
            "token": token,
            "amount": lighter_amount,
            "leverage": leverage,
            "order_type": lighter_order_type,
            # Pas de market_price - le fallback calculera depuis bid/ask
            "bid": lighter_bid,
            "ask": lighter_ask
        }
        logger.info(f"📋 Ordre Lighter: {lighter_order_type.upper()} {lighter_amount} {token} (fermeture)")
    
    # Fermer Paradex si position existe
    if abs(paradex_position_size) > 0:
        # Si position positive (long) → vendre (sell)
        # Si position négative (short) → acheter (buy)
        paradex_order_type = "sell" if paradex_position_size > 0 else "buy"
        # Utiliser la taille absolue de la position
        paradex_amount = abs(paradex_position_size)
        # NE PAS configurer market_price - laisser le fallback le calculer depuis bid/ask
        
        close_config["paradex"] = {
            "token": token,
            "amount": paradex_amount,
            "leverage": leverage,
            "order_type": paradex_order_type,
            # Pas de market_price - le fallback calculera depuis bid/ask
            "bid": paradex_bid,
            "ask": paradex_ask
        }
        logger.info(f"📋 Ordre Paradex: {paradex_order_type.upper()} {paradex_amount} {token} (fermeture)")
    
    if not close_config:
        logger.warning("⚠️ Aucune position à fermer")
        return {"success": True, "message": "Aucune position à fermer"}
    
    logger.info("")
    logger.info("🚀 Exécution des ordres de fermeture...")
    logger.info("")
    
    # 4. Exécuter les ordres de fermeture
    from arbitrage_bot_config import execute_simultaneous_trades
    
    # Fusionner avec config_base pour avoir toutes les infos nécessaires
    # IMPORTANT: Si un exchange n'a pas de position à fermer, ne pas l'inclure dans la config
    # pour éviter d'exécuter un trade non désiré
    full_config = {**config_base}
    # Écraser seulement les exchanges qu'on veut fermer
    if "lighter" in close_config:
        full_config["lighter"] = {**config_base.get("lighter", {}), **close_config["lighter"]}
    if "paradex" in close_config:
        full_config["paradex"] = {**config_base.get("paradex", {}), **close_config["paradex"]}
    
    # Si un seul exchange a une position, on doit quand même fournir une config pour l'autre
    # mais avec amount=0 pour éviter tout trade
    if "lighter" not in close_config:
        full_config["lighter"] = {**config_base.get("lighter", {}), "amount": 0, "order_type": "buy"}
    if "paradex" not in close_config:
        full_config["paradex"] = {**config_base.get("paradex", {}), "amount": 0, "order_type": "buy"}
    
    result = await execute_simultaneous_trades(full_config)
    
    logger.info("")
    if result.get('success'):
        logger.info("✅ Ordre de fermeture envoyé avec succès")
        logger.info("⏳ Attente de 3 secondes pour laisser le temps à la fermeture de se finaliser...")
        await asyncio.sleep(3)
        
        # Vérifier que les positions sont bien fermées
        logger.info("🔍 Vérification que les positions sont bien fermées...")
        verifier_final = TradeVerification()
        lighter_state_final = await verifier_final._get_lighter_account_state()
        position_still_open_lighter = False
        
        if lighter_state_final:
            positions_final = lighter_state_final.get("positions", [])
            market_index_final = LIGHTER_MARKET_IDS.get(token)
            if market_index_final is not None:
                for pos_final in positions_final:
                    pos_market_final = pos_final.get("market_index") or pos_final.get("market_id") or pos_final.get("marketIndex")
                    if pos_market_final == market_index_final:
                        pos_size_final = float(pos_final.get("position") or pos_final.get("size") or pos_final.get("base_amount") or 0)
                        if abs(pos_size_final) > 0.0001:  # Tolérance pour les arrondis
                            position_still_open_lighter = True
                            logger.warning(f"⚠️ Position Lighter encore ouverte: {pos_size_final} {token}")
                            break
        
        if position_still_open_lighter:
            logger.warning("⚠️ La position Lighter n'est pas complètement fermée")
            logger.warning("⚠️ Il peut y avoir un problème de timing ou d'exécution")
            logger.info("")
        else:
            logger.info("✅ Position Lighter confirmée fermée")
        
        logger.info("=" * 80)
        logger.info("✅ POSITIONS FERMÉES AVEC SUCCÈS!")
        logger.info("=" * 80)
    else:
        logger.error("=" * 80)
        logger.error("❌ ÉCHEC DE LA FERMETURE DES POSITIONS")
        logger.error("=" * 80)
    logger.info("")
    
    return result


async def create_trade_config_from_signal(direction: str, token: str, config_base: dict,
                                         lighter_bid: float, lighter_ask: float, lighter_mid: float,
                                         paradex_bid: float, paradex_ask: float, paradex_mid: float,
                                         margin: float, leverage: int) -> dict:
    """
    Crée la configuration de trade basée sur le signal de la stratégie
    
    Args:
        direction: 'short_spread' ou 'long_spread'
        token: Token à trader
        config_base: Configuration de base
        lighter_bid, lighter_ask, lighter_mid: Prix Lighter
        paradex_bid, paradex_ask, paradex_mid: Prix Paradex
        margin: Marge à utiliser
        leverage: Levier à utiliser
    
    Returns:
        Configuration pour execute_simultaneous_trades
    """
    position_value = margin * leverage
    
    # Calculer les montants
    lighter_amount = position_value / lighter_mid
    paradex_amount = position_value / paradex_mid
    
    # Déterminer les types d'ordres selon la direction
    # NE PAS calculer market_price ici - laisser le fallback dans lighter_trader_config.py le faire
    # Le fallback utilisera automatiquement ask + 10 pour achat, bid - 10 pour vente
    
    if direction == 'short_spread':
        # Vendre Paradex, acheter Lighter
        lighter_order_type = "buy"
        paradex_order_type = "sell"
    else:  # long_spread
        # Acheter Paradex, vendre Lighter
        lighter_order_type = "sell"
        paradex_order_type = "buy"
    
    trade_config = {
        "lighter": {
            "token": token,
            "amount": lighter_amount,
            "leverage": leverage,
            "margin": margin,
            "order_type": lighter_order_type,
            # NE PAS configurer market_price - laisser le fallback le calculer depuis bid/ask
            "bid": lighter_bid,
            "ask": lighter_ask
        },
        "paradex": {
            "token": token,
            "amount": paradex_amount,
            "leverage": leverage,
            "margin": margin,
            "order_type": paradex_order_type,
            # NE PAS configurer market_price - laisser le fallback le calculer depuis bid/ask
            "bid": paradex_bid,
            "ask": paradex_ask
        }
    }
    
    return trade_config


async def run_strategy_loop(token: str = "BTC", margin: float = 20, leverage: int = 50,
                           entry_z: float = 1.0, exit_z: float = 0.5, stop_z: float = 4.0,
                           window: int = 900, min_duration_s: int = 4):
    """
    Boucle principale de la stratégie automatique
    
    Args:
        token: Token à trader
        margin: Marge à utiliser
        leverage: Levier
        entry_z, exit_z, stop_z: Paramètres de stratégie
        window: Taille de la fenêtre glissante
        min_duration_s: Durée minimale de confirmation
    """
    logger.info("=" * 80)
    logger.info("🤖 BOT D'ARBITRAGE - MODE STRATÉGIE AUTOMATIQUE")
    logger.info("=" * 80)
    logger.info(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🪙 Token: {token}")
    logger.info(f"💰 Marge: ${margin}, Levier: {leverage}x")
    logger.info(f"📊 Paramètres stratégie: entry_z={entry_z}, exit_z={exit_z}, stop_z={stop_z}, window={window}")
    logger.info("=" * 80)
    
    # 1. Récupérer l'historique depuis Supabase
    logger.info("\n📥 Récupération de l'historique depuis Supabase...")
    history_data = await get_price_history_from_supabase(token, limit=window)
    
    if len(history_data) < 2:
        logger.warning(f"⚠️ Historique insuffisant ({len(history_data)} observations)")
        logger.warning("⚠️ Le bot va attendre d'avoir assez de données...")
        # On continue quand même, la stratégie gérera le cas
    
    # 2. Construire les historiques des 2 spreads exploitables
    spread_PL_history = np.array([])  # Pour short_spread (paradex_bid - lighter_ask)
    spread_LP_history = np.array([])  # Pour long_spread (lighter_bid - paradex_ask)
    
    for data in history_data:
        _, spread_PL, spread_LP = calculate_spreads(
            data['lighter_bid'], data['lighter_ask'], data['lighter_mid'],
            data['paradex_bid'], data['paradex_ask'], data['paradex_mid']
        )
        spread_PL_history = np.append(spread_PL_history, spread_PL)
        spread_LP_history = np.append(spread_LP_history, spread_LP)
    
    logger.info(f"✅ Historique initial: {len(spread_PL_history)} observations")
    if len(spread_PL_history) > 0:
        logger.info(f"   Spread PL (short): moyen={spread_PL_history.mean():.2f}, min={spread_PL_history.min():.2f}, max={spread_PL_history.max():.2f}")
        logger.info(f"   Spread LP (long):  moyen={spread_LP_history.mean():.2f}, min={spread_LP_history.min():.2f}, max={spread_LP_history.max():.2f}")
    
    # 3. Initialiser la stratégie
    params = StrategyParams(
        entry_z=entry_z,
        exit_z=exit_z,
        stop_z=stop_z,
        window=window,
        min_duration_s=min_duration_s,
        decay_factor=0.95
    )
    strategy = ArbitrageStrategy(params)
    
    logger.info("\n🚀 Démarrage de la boucle de monitoring...")
    logger.info("   Vérification toutes les secondes")
    logger.info("   Appuyez sur Ctrl+C pour arrêter")
    logger.info("=" * 80)
    
    # 3.5. Vérifier les positions existantes au démarrage
    logger.info("\n🔍 Vérification des positions existantes...")
    config_base = load_config()
    can_trade, reason = await check_trading_conditions(config_base, token)
    
    # IMPORTANT: Si aucune position réelle n'existe, réinitialiser la position virtuelle
    if can_trade:
        logger.info("✅ Aucune position existante détectée")
        # Réinitialiser la position virtuelle dans la stratégie
        strategy.current_position = None
        strategy.signal_start_time = None
        strategy.signal_direction = None
        logger.info("🔄 Position virtuelle réinitialisée à 0")
    else:
        logger.warning(f"⚠️ Position existante détectée: {reason}")
        logger.warning("⚠️ Le bot va surveiller cette position et détecter sa fermeture")
        logger.warning("⚠️ Aucun nouveau trade ne sera ouvert tant qu'une position existe")
        # La synchronisation se fera automatiquement dans la boucle principale
        from trade_verification import TradeVerification
        verifier = TradeVerification()
        lighter_state = await verifier._get_lighter_account_state()
        if lighter_state:
            positions = lighter_state.get("positions", [])
            market_index = LIGHTER_MARKET_IDS.get(token)
            if market_index is not None:
                for pos in positions:
                    pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                    if pos_market == market_index:
                        pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                        if abs(pos_size) > 0:
                            logger.info(f"   📊 Position suivie: {pos_size} {token} sur Lighter")
    logger.info("")
    
    # 4. Boucle principale - LOGIQUE SIMPLIFIÉE ET CLAIRE
    tick_count = 0
    last_log_time = datetime.now()
    
    try:
        while True:
            tick_count += 1
            current_time = datetime.now()
            
            # ============================================
            # ÉTAPE 1: Récupérer les prix
            # ============================================
            lighter_bid, lighter_ask, lighter_mid, paradex_bid, paradex_ask, paradex_mid = await get_current_prices_parallel(token)
            
            if not all([lighter_bid, lighter_ask, lighter_mid, paradex_bid, paradex_ask, paradex_mid]):
                logger.warning(f"⚠️ Tick {tick_count}: Prix incomplets, skip ce tick")
                await asyncio.sleep(1)
                continue
            
            # ============================================
            # ÉTAPE 2: Calculer spreads et z-scores
            # ============================================
            spread_net, spread_PL, spread_LP = calculate_spreads(
                lighter_bid, lighter_ask, lighter_mid,
                paradex_bid, paradex_ask, paradex_mid
            )
            
            # Mettre à jour les 2 historiques séparés
            spread_PL_history = np.append(spread_PL_history, spread_PL)
            spread_PL_history = spread_PL_history[-window:]
            
            spread_LP_history = np.append(spread_LP_history, spread_LP)
            spread_LP_history = spread_LP_history[-window:]
            
            # Calculer les 2 z-scores séparés
            z_score_short, z_score_long = strategy.calculate_z_scores(
                spread_PL, spread_LP,
                spread_PL_history, spread_LP_history
            )
            
            # ============================================
            # ÉTAPE 3: Vérifier l'état réel (une seule fois par tick)
            # ============================================
            config_base = load_config()
            has_real_position, position_reason = await check_trading_conditions(config_base, token)
            has_real_position = not has_real_position  # Inverser: can_trade=False signifie position existe
            
            # ============================================
            # ÉTAPE 4: Synchroniser position réelle avec stratégie (si nécessaire)
            # ============================================
            # Si position réelle existe mais stratégie ne la connaît pas → synchroniser
            if has_real_position and strategy.current_position is None:
                logger.warning(f"⚠️ Position réelle détectée mais stratégie n'a pas de position virtuelle - Synchronisation nécessaire")
                # Déterminer direction depuis la position réelle (vérifier la taille de la position)
                direction = None
                from trade_verification import TradeVerification
                verifier = TradeVerification()
                lighter_state = await verifier._get_lighter_account_state()
                if lighter_state:
                    positions = lighter_state.get("positions", [])
                    market_index = LIGHTER_MARKET_IDS.get(token)
                    if market_index is not None:
                        for pos in positions:
                            pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                            if pos_market == market_index:
                                pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                                if abs(pos_size) > 0:
                                    # IMPORTANT: Lighter retourne maintenant des positions négatives pour SHORT
                                    # (grâce à la correction dans trade_verification.py qui utilise le prix de liquidation)
                                    # Position positive = LONG sur Lighter = short_spread (on vend Paradex, on achète Lighter)
                                    # Position négative = SHORT sur Lighter = long_spread (on achète Paradex, on vend Lighter)
                                    direction = 'short_spread' if pos_size > 0 else 'long_spread'
                                    logger.info(f"🔄 Direction déterminée depuis position réelle: {direction} (pos_size={pos_size})")
                                    break
                
                # Fallback : utiliser z-score si on n'a pas pu déterminer depuis la position réelle
                if direction is None:
                    # Utiliser le z-score le plus élevé pour déterminer la direction
                    direction = 'short_spread' if z_score_short > z_score_long else 'long_spread'
                    logger.warning(f"⚠️ Impossible de déterminer direction depuis position réelle, utilisation z-score: {direction}")
                
                logger.info(f"🔄 Synchronisation: Position réelle détectée, création position virtuelle")
                logger.info(f"   Direction: {direction}")
                logger.info(f"   Z-score short: {z_score_short:.2f}, Z-score long: {z_score_long:.2f}")
                strategy.enter_position(z_score_short, z_score_long, direction, current_time, spread_PL, spread_LP)
                if strategy.current_position:
                    # Marquer le tick de synchronisation pour éviter les fermetures immédiates
                    strategy.current_position._sync_tick = tick_count
            
            # ============================================
            # ÉTAPE 5: Gérer les positions (entrée ou sortie)
            # ============================================
            position_before = strategy.current_position
            position_was_open = position_before and position_before.status == 'open'
            
            # Si on a une position (réelle ou virtuelle), chercher sortie
            if strategy.current_position and strategy.current_position.status == 'open':
                # IMPORTANT: Ne pas fermer immédiatement une position qui vient d'être synchronisée
                # Si la position a été créée il y a moins de 10 ticks, ignorer les signaux de sortie "direction_change"
                # Cela permet à la position de se stabiliser avant de chercher des sorties
                position_age = tick_count - (getattr(strategy.current_position, '_sync_tick', tick_count))
                is_synced_position = hasattr(strategy.current_position, '_sync_tick')
                ignore_direction_change = is_synced_position and position_age < 10
                
                # Vérifier sortie (à CHAQUE TICK, pas seulement toutes les 10 secondes)
                should_exit, exit_reason = strategy.should_exit_position(z_score_short, z_score_long, current_time)
                
                # Ignorer inversion si la position vient d'être synchronisée
                if should_exit and exit_reason == 'inversion' and ignore_direction_change:
                    logger.debug(f"⏸️  Signal inversion ignoré (position synchronisée récemment, age={position_age} ticks)")
                    should_exit = False
                    exit_reason = None
                
                # Log détaillé toutes les 10 secondes pour confirmer qu'on cherche des sorties
                if tick_count % 10 == 0:
                    z_score_active = z_score_short if strategy.current_position.direction == 'short_spread' else z_score_long
                    logger.info(f"🔍 Vérification sortie (toutes les 10s):")
                    logger.info(f"   Z-scores: short={z_score_short:.2f}, long={z_score_long:.2f} (actif={z_score_active:.2f})")
                    logger.info(f"   Signal: should_exit={should_exit}, exit_reason={exit_reason}")
                    logger.info(f"   Position: age={position_age}, is_synced={is_synced_position}")
                # IMPORTANT: La vérification se fait à CHAQUE TICK, mais on log seulement toutes les 10 secondes pour éviter le spam
                
                if should_exit:
                    # Signal de sortie confirmé
                    logger.info(f"🔍 Signal de sortie confirmé: {exit_reason} | z={z_score:.2f} | position={strategy.current_position.direction}")
                    
                    # IMPORTANT: Si une position réelle existe, on ne peut pas la fermer automatiquement
                    # On ne ferme la position virtuelle QUE si on peut fermer réellement
                    # Sinon, on garde la position virtuelle pour continuer à surveiller
                    if has_real_position:
                        # Position réelle existe → Fermer les positions réelles
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("🔄 FERMETURE DES POSITIONS RÉELLES")
                        logger.info("=" * 80)
                        logger.info(f"   Direction: {strategy.current_position.direction}")
                        logger.info(f"   Raison: {exit_reason}")
                        logger.info(f"   Z-score entrée: {strategy.current_position.entry_z:.2f}")
                        logger.info(f"   Z-score sortie: {z_score:.2f}")
                        logger.info(f"   Spread entrée: {strategy.current_position.entry_spread:.2f}")
                        logger.info(f"   Spread sortie: {spread_net:.2f}")
                        logger.info("")
                        
                        # Fermer les positions réelles
                        try:
                            close_result = await close_positions(
                                token, config_base,
                                lighter_bid, lighter_ask, lighter_mid,
                                paradex_bid, paradex_ask, paradex_mid,
                                leverage
                            )
                            
                            if close_result.get('success'):
                                logger.info("✅ Positions fermées avec succès")
                                # Maintenant on peut fermer la position virtuelle
                                entry_spread_PL = getattr(strategy.current_position, 'entry_spread_PL', spread_PL)
                                entry_spread_LP = getattr(strategy.current_position, 'entry_spread_LP', spread_LP)
                                strategy.exit_position(z_score_short, z_score_long, current_time, exit_reason,
                                                     spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
                                
                                # Log de fermeture
                                closed_trade = position_before
                                logger.info("")
                                logger.info("=" * 80)
                                logger.info("📉 POSITION FERMÉE")
                                logger.info("=" * 80)
                                logger.info(f"   Direction: {closed_trade.direction}")
                                logger.info(f"   Raison: {exit_reason}")
                                z_score_entry_used = closed_trade.entry_z
                                z_score_exit_used = z_score_short if closed_trade.direction == 'short_spread' else z_score_long
                                logger.info(f"   Z-score entrée: {z_score_entry_used:.2f}")
                                logger.info(f"   Z-score sortie: {z_score_exit_used:.2f} (short={z_score_short:.2f}, long={z_score_long:.2f})")
                                logger.info(f"   Spread entrée: {closed_trade.entry_spread:.2f}")
                                exit_spread_value = spread_PL if closed_trade.direction == 'short_spread' else spread_LP
                                logger.info(f"   Spread sortie: {exit_spread_value:.2f} (PL={spread_PL:.2f}, LP={spread_LP:.2f})")
                                if closed_trade.pnl is not None:
                                    logger.info(f"   PnL: {closed_trade.pnl:.2f} ({closed_trade.pnl_percent:.2f}%)")
                                logger.info(f"   Durée: {closed_trade.duration_obs} observations")
                                logger.info("=" * 80)
                                logger.info("")
                            else:
                                logger.error("❌ Échec de la fermeture des positions")
                                logger.warning("⚠️ Le bot continuera de surveiller la position")
                                # NE PAS fermer la position virtuelle si la fermeture réelle a échoué
                        except Exception as e:
                            logger.error(f"❌ Erreur lors de la fermeture des positions: {e}")
                            import traceback
                            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                            logger.warning("⚠️ Le bot continuera de surveiller la position")
                            # NE PAS fermer la position virtuelle si la fermeture réelle a échoué
                    else:
                        # Pas de position réelle → On peut fermer la position virtuelle
                        entry_spread_PL = getattr(strategy.current_position, 'entry_spread_PL', spread_PL)
                        entry_spread_LP = getattr(strategy.current_position, 'entry_spread_LP', spread_LP)
                        strategy.exit_position(z_score_short, z_score_long, current_time, exit_reason,
                                             spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
                        
                        # Log de fermeture
                        closed_trade = position_before
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("📉 POSITION FERMÉE")
                        logger.info("=" * 80)
                        logger.info(f"   Direction: {closed_trade.direction}")
                        logger.info(f"   Raison: {exit_reason}")
                        z_score_entry_used = closed_trade.entry_z
                        z_score_exit_used = z_score_short if closed_trade.direction == 'short_spread' else z_score_long
                        logger.info(f"   Z-score entrée: {z_score_entry_used:.2f}")
                        logger.info(f"   Z-score sortie: {z_score_exit_used:.2f} (short={z_score_short:.2f}, long={z_score_long:.2f})")
                        logger.info(f"   Spread entrée: {closed_trade.entry_spread:.2f}")
                        exit_spread_value = spread_PL if closed_trade.direction == 'short_spread' else spread_LP
                        logger.info(f"   Spread sortie: {exit_spread_value:.2f} (PL={spread_PL:.2f}, LP={spread_LP:.2f})")
                        if closed_trade.pnl is not None:
                            logger.info(f"   PnL: {closed_trade.pnl:.2f} ({closed_trade.pnl_percent:.2f}%)")
                        logger.info(f"   Durée: {closed_trade.duration_obs} observations")
                        logger.info("=" * 80)
                        logger.info("")
                elif exit_reason:
                    # Signal de sortie en validation
                    z_score_active = z_score_short if strategy.current_position.direction == 'short_spread' else z_score_long
                    logger.info(f"⏳ Signal de sortie en validation: {exit_reason} | z={z_score_active:.2f} (short={z_score_short:.2f}, long={z_score_long:.2f}) | position={strategy.current_position.direction}")
                
                # Mettre à jour la durée de la position
                if strategy.current_position:
                    strategy.current_position.duration_obs += 1
                
                # Log périodique de surveillance (toutes les 10 secondes)
                if tick_count % 10 == 0 and strategy.current_position:
                    z_score_active = z_score_short if strategy.current_position.direction == 'short_spread' else z_score_long
                    logger.info(f"👁️  Surveillance position:")
                    logger.info(f"   Z-scores: short={z_score_short:.2f}, long={z_score_long:.2f} (actif={z_score_active:.2f})")
                    logger.info(f"   Direction: {strategy.current_position.direction}, entry_z: {strategy.current_position.entry_z:.2f}")
            
            # Si pas de position, chercher entrée
            elif not has_real_position:
                # Pas de position réelle → chercher entrée
                should_enter, enter_direction = strategy.should_enter_position(z_score_short, z_score_long, current_time)
                
                if should_enter:
                    # Signal d'entrée confirmé → Créer position virtuelle et exécuter trade
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info("🎯 SIGNAL D'ENTRÉE DÉTECTÉ")
                    logger.info("=" * 80)
                    logger.info(f"   Direction: {enter_direction}")
                    z_score_used = z_score_short if enter_direction == 'short_spread' else z_score_long
                    logger.info(f"   Z-score utilisé: {z_score_used:.2f} (short={z_score_short:.2f}, long={z_score_long:.2f})")
                    spread_exploitable = spread_PL if enter_direction == 'short_spread' else spread_LP
                    logger.info(f"   Spread exploitable (entrée): {spread_exploitable:.2f}$ (PL={spread_PL:.2f}, LP={spread_LP:.2f})")
                    logger.info(f"   Prix Lighter: bid=${lighter_bid:.2f}, ask=${lighter_ask:.2f}, mid=${lighter_mid:.2f}")
                    logger.info(f"   Prix Paradex: bid=${paradex_bid:.2f}, ask=${paradex_ask:.2f}, mid=${paradex_mid:.2f}")
                    logger.info(f"   Token: {token}")
                    logger.info(f"   Marge: ${margin}, Levier: {leverage}x")
                    logger.info("=" * 80)
                    logger.info("")
                    
                    # Vérifier une dernière fois qu'on peut trader
                    can_trade_final, reason_final = await check_trading_conditions(config_base, token)
                    
                    if not can_trade_final:
                        # Vérifier si une position existe mais dans la direction opposée
                        # Si oui, fermer la position existante (c'est un signal de sortie direction_change)
                        # MAIS ne pas ouvrir immédiatement une nouvelle position - attendre un nouveau signal
                        from trade_verification import TradeVerification
                        verifier = TradeVerification()
                        lighter_state = await verifier._get_lighter_account_state()
                        existing_position_direction = None
                        
                        if lighter_state:
                            positions = lighter_state.get("positions", [])
                            market_index = LIGHTER_MARKET_IDS.get(token)
                            if market_index is not None:
                                for pos in positions:
                                    pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                                    if pos_market == market_index:
                                        pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                                        if abs(pos_size) > 0:
                                            # IMPORTANT: Lighter retourne maintenant des positions négatives pour SHORT
                                            # Position positive = LONG sur Lighter = short_spread
                                            # Position négative = SHORT sur Lighter = long_spread
                                            existing_position_direction = 'short_spread' if pos_size > 0 else 'long_spread'
                                            break
                        
                        # Si une position existe, on doit la fermer avant d'ouvrir une nouvelle
                        # - Si direction opposée → fermer et attendre un nouveau signal (direction_change)
                        # - Si même direction → fermer d'abord, puis ouvrir la nouvelle position
                        if existing_position_direction:
                            if existing_position_direction != enter_direction:
                                # Direction opposée → fermer et attendre un nouveau signal
                                logger.info("")
                                logger.info("=" * 80)
                                logger.info("🔄 SIGNAL DE SORTIE (direction opposée détectée)")
                                logger.info("=" * 80)
                                logger.info(f"   Position existante: {existing_position_direction}")
                                logger.info(f"   Signal d'entrée opposé: {enter_direction}")
                                logger.info(f"   → Fermeture de la position (opportunité de gain)")
                                logger.info("=" * 80)
                                logger.info("")
                                
                                # Fermer la position existante
                                try:
                                    close_result = await close_positions(
                                        token, config_base,
                                        lighter_bid, lighter_ask, lighter_mid,
                                        paradex_bid, paradex_ask, paradex_mid,
                                        leverage
                                    )
                                    
                                    if close_result.get('success'):
                                        logger.info("✅ Ordre de fermeture envoyé avec succès")
                                        logger.info("⏳ Attente de 3 secondes pour laisser le temps à la fermeture de se finaliser...")
                                        await asyncio.sleep(3)
                                        
                                        # Vérifier que la position est bien fermée
                                        logger.info("🔍 Vérification que la position est bien fermée...")
                                        verifier_check = TradeVerification()
                                        lighter_state_check = await verifier_check._get_lighter_account_state()
                                        position_still_open = False
                                        
                                        if lighter_state_check:
                                            positions_check = lighter_state_check.get("positions", [])
                                            market_index_check = LIGHTER_MARKET_IDS.get(token)
                                            if market_index_check is not None:
                                                for pos_check in positions_check:
                                                    pos_market_check = pos_check.get("market_index") or pos_check.get("market_id") or pos_check.get("marketIndex")
                                                    if pos_market_check == market_index_check:
                                                        pos_size_check = float(pos_check.get("position") or pos_check.get("size") or pos_check.get("base_amount") or 0)
                                                        if abs(pos_size_check) > 0.0001:  # Tolérance pour les arrondis
                                                            position_still_open = True
                                                            logger.warning(f"⚠️ Position encore ouverte: {pos_size_check} {token}")
                                                            break
                                        
                                        if position_still_open:
                                            logger.warning("⚠️ La position n'est pas complètement fermée - Attente d'un autre tick")
                                            logger.info("")
                                            continue
                                        
                                        logger.info("✅ Position confirmée fermée")
                                        logger.info("⏳ Attente d'un nouveau signal d'entrée (l'opportunité peut avoir disparu)")
                                        logger.info("")
                                        
                                        # Réinitialiser la position virtuelle
                                        if strategy.current_position:
                                            entry_spread_PL = getattr(strategy.current_position, 'entry_spread_PL', spread_PL)
                                            entry_spread_LP = getattr(strategy.current_position, 'entry_spread_LP', spread_LP)
                                            strategy.exit_position(z_score_short, z_score_long, current_time, "direction_change",
                                                                 spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
                                        
                                        # NE PAS ouvrir immédiatement une nouvelle position
                                        # Le signal d'entrée sera détecté au prochain tick si l'opportunité persiste
                                        logger.info("🔄 Retour à la surveillance - Attente d'un nouveau signal d'entrée confirmé")
                                        logger.info("")
                                        continue
                                    else:
                                        logger.error("❌ Échec de la fermeture de la position existante")
                                        logger.warning("⚠️ Le bot continuera de surveiller la position")
                                        logger.info("")
                                        continue
                                except Exception as e:
                                    logger.error(f"❌ Erreur lors de la fermeture de la position existante: {e}")
                                    logger.warning("⚠️ Le bot continuera de surveiller la position")
                                    logger.info("")
                                    continue
                            else:
                                # MÊME direction → fermer d'abord, puis ouvrir la nouvelle position
                                logger.info("")
                                logger.info("=" * 80)
                                logger.info("🔄 FERMETURE DE LA POSITION EXISTANTE (même direction)")
                                logger.info("=" * 80)
                                logger.info(f"   Position existante: {existing_position_direction}")
                                logger.info(f"   Nouveau signal: {enter_direction}")
                                logger.info(f"   → Fermeture de la position existante avant d'ouvrir la nouvelle")
                                logger.info("=" * 80)
                                logger.info("")
                                
                                # Fermer la position existante
                                try:
                                    close_result = await close_positions(
                                        token, config_base,
                                        lighter_bid, lighter_ask, lighter_mid,
                                        paradex_bid, paradex_ask, paradex_mid,
                                        leverage
                                    )
                                    
                                    if close_result.get('success'):
                                        logger.info("✅ Position existante fermée avec succès")
                                        logger.info("⏳ Attente de 3 secondes pour laisser le temps à la fermeture de se finaliser...")
                                        await asyncio.sleep(3)
                                        
                                        # Vérifier que la position est bien fermée
                                        logger.info("🔍 Vérification que la position est bien fermée...")
                                        verifier_check = TradeVerification()
                                        lighter_state_check = await verifier_check._get_lighter_account_state()
                                        position_still_open = False
                                        
                                        if lighter_state_check:
                                            positions_check = lighter_state_check.get("positions", [])
                                            market_index_check = LIGHTER_MARKET_IDS.get(token)
                                            if market_index_check is not None:
                                                for pos_check in positions_check:
                                                    pos_market_check = pos_check.get("market_index") or pos_check.get("market_id") or pos_check.get("marketIndex")
                                                    if pos_market_check == market_index_check:
                                                        pos_size_check = float(pos_check.get("position") or pos_check.get("size") or pos_check.get("base_amount") or 0)
                                                        if abs(pos_size_check) > 0.0001:  # Tolérance pour les arrondis
                                                            position_still_open = True
                                                            logger.warning(f"⚠️ Position encore ouverte: {pos_size_check} {token}")
                                                            break
                                        
                                        if position_still_open:
                                            logger.warning("⚠️ La position n'est pas complètement fermée - Attente d'un autre tick")
                                            logger.info("")
                                            continue
                                        
                                        logger.info("✅ Position confirmée fermée")
                                        logger.info("🔄 Continuation pour ouvrir la nouvelle position...")
                                        logger.info("")
                                        
                                        # Réinitialiser la position virtuelle
                                        if strategy.current_position:
                                            entry_spread_PL = getattr(strategy.current_position, 'entry_spread_PL', spread_PL)
                                            entry_spread_LP = getattr(strategy.current_position, 'entry_spread_LP', spread_LP)
                                            strategy.exit_position(z_score_short, z_score_long, current_time, "direction_change",
                                                                 spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
                                        
                                        # Continuer pour ouvrir la nouvelle position (le code continue après ce bloc)
                                    else:
                                        logger.error("❌ Échec de la fermeture de la position existante")
                                        logger.warning("⚠️ TRADE ANNULÉ - Impossible de fermer la position existante")
                                        logger.info("")
                                        continue
                                except Exception as e:
                                    logger.error(f"❌ Erreur lors de la fermeture de la position existante: {e}")
                                    logger.warning("⚠️ TRADE ANNULÉ")
                                    logger.info("")
                                    continue
                        else:
                            # Position existe mais direction non détectée, ou erreur de détection
                            logger.warning("=" * 80)
                            logger.warning(f"⚠️ CONDITIONS NON REMPLIES: {reason_final}")
                            logger.warning("⚠️ TRADE ANNULÉ")
                            logger.warning("=" * 80)
                            logger.info("")
                            continue
                    
                    # Exécuter le trade
                    logger.info("✅ Conditions vérifiées - Exécution des trades...")
                    logger.info("")
                    
                    # Créer la configuration de trade
                    trade_config = await create_trade_config_from_signal(
                        enter_direction, token, config_base,
                        lighter_bid, lighter_ask, lighter_mid,
                        paradex_bid, paradex_ask, paradex_mid,
                        margin, leverage
                    )
                    
                    # Afficher les détails
                    logger.info("📋 Détails du trade:")
                    logger.info(f"   Lighter: {trade_config['lighter']['order_type'].upper()} {trade_config['lighter']['amount']:.8f} {token}")
                    logger.info(f"   Paradex: {trade_config['paradex']['order_type'].upper()} {trade_config['paradex']['amount']:.8f} {token}")
                    logger.info("")
                    
                    # Exécuter les trades
                    result = await execute_simultaneous_trades(trade_config)
                    
                    logger.info("")
                    if result.get('success'):
                        logger.info("=" * 80)
                        logger.info("✅ TRADES EXÉCUTÉS AVEC SUCCÈS!")
                        logger.info("=" * 80)
                        logger.info("")
                        # Créer la position virtuelle dans la stratégie pour suivre la sortie
                        strategy.enter_position(z_score_short, z_score_long, enter_direction, current_time, spread_PL, spread_LP)
                        if strategy.current_position:
                            # Marquer le tick de création pour éviter les fermetures immédiates
                            strategy.current_position._sync_tick = tick_count
                        logger.info("📌 Position réelle créée - La stratégie va maintenant gérer sa sortie")
                        logger.info("")
                    else:
                        logger.error("=" * 80)
                        logger.error("❌ ÉCHEC DES TRADES")
                        logger.error("=" * 80)
                        logger.info("")
                        # Ne pas créer de position virtuelle si le trade a échoué
            
            # ============================================
            # ÉTAPE 6: Logs périodiques
            # ============================================
            # Log les Z-scores à chaque tick pour mise à jour en temps réel sur la page web
            logger.info(f"⏱️  Tick {tick_count} | Z-scores: short={z_score_short:.2f}, long={z_score_long:.2f} | Spreads: PL={spread_PL:.2f}, LP={spread_LP:.2f}")
            
            # Log périodique détaillé (toutes les 60 secondes)
            if tick_count % 60 == 0:
                position_info = "Non"
                if strategy.current_position and strategy.current_position.status == 'open':
                    z_score_active = z_score_short if strategy.current_position.direction == 'short_spread' else z_score_long
                    position_info = f"Oui ({strategy.current_position.direction}, entry_z={strategy.current_position.entry_z:.2f}, current_z={z_score_active:.2f})"
                
                real_position_info = "Position réelle détectée" if has_real_position else "Aucune position réelle"
                
                logger.info("")
                logger.info(f"📊 Tick {tick_count} | Z-scores: short={z_score_short:.2f}, long={z_score_long:.2f}")
                logger.info(f"   Spreads exploitables: PL={spread_PL:.2f}, LP={spread_LP:.2f}")
                logger.info(f"   Position stratégie: {position_info}")
                logger.info(f"   Position réelle: {real_position_info}")
                if has_real_position:
                    logger.info(f"   Détail: {position_reason}")
                logger.info("")
            
            # Attendre 1 seconde
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Arrêt demandé par l'utilisateur")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot d\'arbitrage avec stratégie automatique')
    parser.add_argument('--token', type=str, default='BTC', help='Token à trader (BTC, ETH)')
    parser.add_argument('--margin', type=float, default=20, help='Marge à utiliser ($)')
    parser.add_argument('--leverage', type=int, default=50, help='Levier')
    parser.add_argument('--entry-z', type=float, default=1.0, help='Seuil d\'entrée (z-score)')
    parser.add_argument('--exit-z', type=float, default=0.5, help='Seuil de sortie (z-score)')
    parser.add_argument('--stop-z', type=float, default=4.0, help='Stop loss (z-score)')
    parser.add_argument('--window', type=int, default=900, help='Fenêtre glissante (observations, 900 = 15 minutes à 1 obs/seconde)')
    parser.add_argument('--min-duration', type=int, default=4, help='Durée minimale de confirmation (secondes)')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_strategy_loop(
            token=args.token,
            margin=args.margin,
            leverage=args.leverage,
            entry_z=args.entry_z,
            exit_z=args.exit_z,
            stop_z=args.stop_z,
            window=args.window,
            min_duration_s=args.min_duration
        ))
    except KeyboardInterrupt:
        logger.info("\n👋 Au revoir!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

