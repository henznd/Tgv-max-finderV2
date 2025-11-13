#!/usr/bin/env python3
"""
Bot d'arbitrage SIMPLE basé sur le spread brut
Sans Z-score, juste comparer le spread à un seuil

Usage:
    python arbitrage_bot_simple.py --token BTC --margin 18 --leverage 50 \\
        --entry-spread 15 --exit-spread 5 --min-hold-time 10
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from typing import Optional

# Ajouter le répertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Imports
from logger import setup_logger
from arbitrage_strategy_simple import ArbitrageStrategySimple, StrategyParamsSimple
from arbitrage_bot_config import (
    get_lighter_price_direct,
    get_paradex_price_direct,
    load_config,
    LIGHTER_MARKET_IDS,
    PARADEX_MARKETS
)
from trade_verification import TradeVerification

logger = setup_logger("arbitrage_bot_simple")


async def check_trading_conditions(config: dict, token: str) -> tuple[bool, str]:
    """
    Vérifie les conditions de trading (pas de positions ouvertes, marge suffisante)
    Réutilise la logique de trade_verification.py
    
    Returns:
        (can_trade, reason)
    """
    verifier = TradeVerification()
    
    # Vérifier position Lighter
    lighter_state = await verifier._get_lighter_account_state()
    if lighter_state:
        positions = lighter_state.get("positions", [])
        market_index = LIGHTER_MARKET_IDS.get(token)
        if market_index is not None:
            for pos in positions:
                pos_market = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                if pos_market == market_index:
                    pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or 0)
                    if abs(pos_size) > 0.00001:  # Position significative
                        return False, f"Position Lighter déjà ouverte: {pos_size} {token}"
    
    # Vérifier position Paradex
    try:
        from paradex_py import Paradex
        sys.path.append(os.path.join(os.path.dirname(__file__), 'paradex'))
        from paradex.paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS, TOKEN_MARKET
        
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        
        positions = paradex.api_client.fetch_positions()
        market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
        
        if positions and 'results' in positions:
            for pos in positions['results']:
                if pos.get('market') == market and pos.get('status') == 'OPEN':
                    pos_size = float(pos.get('size', 0) or 0)
                    if abs(pos_size) > 0.00001:
                        return False, f"Position Paradex déjà ouverte: {pos_size} {token}"
    except Exception as e:
        logger.warning(f"⚠️ Impossible de vérifier position Paradex: {e}")
    
    return True, "OK"


async def close_positions_simple(token: str, config_base: dict, margin: float, leverage: int) -> dict:
    """
    Ferme les positions ouvertes en passant des ordres opposés
    Version simplifiée pour la stratégie simple
    """
    from arbitrage_bot_strategy import close_positions
    
    # Récupérer les prix actuels
    lighter_prices = await get_lighter_price_direct(token)
    paradex_prices = await get_paradex_price_direct(token)
    
    if not lighter_prices or not paradex_prices:
        logger.error("❌ Impossible de récupérer les prix pour fermer les positions")
        return {"success": False, "error": "Prix non disponibles"}
    
    # Appeler la fonction de fermeture existante
    return await close_positions(
        token=token,
        config_base=config_base,
        lighter_bid=lighter_prices['bid'],
        lighter_ask=lighter_prices['ask'],
        lighter_mid=lighter_prices['mid'],
        paradex_bid=paradex_prices['bid'],
        paradex_ask=paradex_prices['ask'],
        paradex_mid=paradex_prices['mid'],
        leverage=leverage
    )


async def execute_trade_simple(direction: str, token: str, margin: float, leverage: int,
                              lighter_bid: float, lighter_ask: float,
                              paradex_bid: float, paradex_ask: float) -> dict:
    """
    Exécute un trade simple en utilisant execute_simultaneous_trades
    
    Args:
        direction: 'sell_lighter' ou 'sell_paradex'
        token: Token à trader
        margin: Marge par position (en $)
        leverage: Levier
        lighter_bid, lighter_ask: Prix Lighter
        paradex_bid, paradex_ask: Prix Paradex
    
    Returns:
        Résultat de l'exécution
    """
    from arbitrage_bot_config import execute_simultaneous_trades
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎯 SIGNAL D'ENTRÉE DÉTECTÉ - STRATÉGIE SIMPLE")
    logger.info("=" * 80)
    logger.info(f"   Direction: {direction}")
    logger.info(f"   Token: {token}")
    logger.info(f"   Marge: ${margin}, Levier: {leverage}x")
    logger.info(f"   Lighter bid/ask: ${lighter_bid:.2f} / ${lighter_ask:.2f}")
    logger.info(f"   Paradex bid/ask: ${paradex_bid:.2f} / ${paradex_ask:.2f}")
    
    # Calculer le spread
    if direction == 'sell_lighter':
        spread = lighter_bid - paradex_ask
        lighter_order_type = "sell"
        paradex_order_type = "buy"
        lighter_price = lighter_bid  # Vendre au bid
        paradex_price = paradex_ask  # Acheter à l'ask
        logger.info(f"   📊 Spread: ${spread:.2f} (Lighter bid ${lighter_bid:.2f} - Paradex ask ${paradex_ask:.2f})")
    else:  # sell_paradex
        spread = paradex_bid - lighter_ask
        lighter_order_type = "buy"
        paradex_order_type = "sell"
        lighter_price = lighter_ask  # Acheter à l'ask
        paradex_price = paradex_bid  # Vendre au bid
        logger.info(f"   📊 Spread: ${spread:.2f} (Paradex bid ${paradex_bid:.2f} - Lighter ask ${lighter_ask:.2f})")
    
    logger.info("=" * 80)
    logger.info("")
    
    # Créer la configuration pour les trades
    config = load_config()
    
    # Calculer les montants
    position_value = margin * leverage
    lighter_mid = (lighter_bid + lighter_ask) / 2
    paradex_mid = (paradex_bid + paradex_ask) / 2
    
    lighter_amount = position_value / lighter_mid
    paradex_amount = position_value / paradex_mid
    
    # Configurer les trades
    config['lighter'] = {
        "token": token,
        "amount": lighter_amount,
        "leverage": leverage,
        "order_type": lighter_order_type,
        "bid": lighter_bid,
        "ask": lighter_ask
    }
    
    config['paradex'] = {
        "token": token,
        "amount": paradex_amount,
        "leverage": leverage,
        "order_type": paradex_order_type,
        "bid": paradex_bid,
        "ask": paradex_ask
    }
    
    # Exécuter les trades
    result = await execute_simultaneous_trades(config)
    
    if result.get("success"):
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ TRADES EXÉCUTÉS AVEC SUCCÈS - STRATÉGIE SIMPLE")
        logger.info("=" * 80)
        logger.info("")
    else:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ ÉCHEC DES TRADES - STRATÉGIE SIMPLE")
        logger.error("=" * 80)
        logger.error("")
    
    return result


async def run_strategy_loop(token: str, margin: float, leverage: int,
                           entry_spread: float, exit_spread: float,
                           min_hold_time: int, min_duration_s: int = 4):
    """
    Boucle principale de la stratégie simple
    
    Args:
        token: Token à trader
        margin: Marge par position (en $)
        leverage: Levier
        entry_spread: Spread minimum pour entrer (en $)
        exit_spread: Spread maximum pour sortir (en $)
        min_hold_time: Durée minimale de détention (en secondes)
        min_duration_s: Durée minimale de confirmation du signal (secondes)
    """
    logger.info("=" * 80)
    logger.info("🤖 BOT D'ARBITRAGE STRATÉGIE SIMPLE")
    logger.info("=" * 80)
    logger.info(f"🪙 Token: {token}")
    logger.info(f"💰 Marge: ${margin}, Levier: {leverage}x")
    logger.info(f"📊 Paramètres stratégie:")
    logger.info(f"   Entry spread: ${entry_spread}")
    logger.info(f"   Exit spread: ${exit_spread}")
    logger.info(f"   Min hold time: {min_hold_time}s")
    logger.info(f"   Min duration: {min_duration_s}s")
    logger.info("=" * 80)
    
    # Initialiser la stratégie
    params = StrategyParamsSimple(
        entry_spread=entry_spread,
        exit_spread=exit_spread,
        min_duration_s=min_duration_s,
        min_hold_time=min_hold_time,
        max_hold=240  # 4 minutes max
    )
    
    strategy = ArbitrageStrategySimple(params)
    
    # Configuration de base
    config_base = load_config()
    
    # Compteur de ticks
    tick_count = 0
    
    logger.info("")
    logger.info("🚀 Démarrage de la surveillance...")
    logger.info("")
    
    while True:
        try:
            tick_count += 1
            current_time = datetime.now()
            
            # 1. Récupérer les prix en temps réel
            lighter_prices_task = asyncio.create_task(get_lighter_price_direct(token))
            paradex_prices_task = asyncio.create_task(get_paradex_price_direct(token))
            
            lighter_prices, paradex_prices = await asyncio.gather(lighter_prices_task, paradex_prices_task)
            
            if not lighter_prices or not paradex_prices:
                logger.warning(f"⚠️ Prix non disponibles, attente 3 secondes...")
                await asyncio.sleep(3)
                continue
            
            # 2. Traiter le tick avec la stratégie
            strategy.process_tick(
                lighter_bid=lighter_prices['bid'],
                lighter_ask=lighter_prices['ask'],
                paradex_bid=paradex_prices['bid'],
                paradex_ask=paradex_prices['ask'],
                timestamp=current_time
            )
            
            # 3. Calculer le spread actuel pour l'affichage
            spread_sell_lighter = lighter_prices['bid'] - paradex_prices['ask']
            spread_sell_paradex = paradex_prices['bid'] - lighter_prices['ask']
            spread_max = max(spread_sell_lighter, spread_sell_paradex)
            direction = 'sell_lighter' if spread_sell_lighter > spread_sell_paradex else 'sell_paradex'
            
            # 4. Log périodique
            logger.info(f"⏱️  Tick {tick_count} | Spread: ${spread_max:.2f} ({direction}) | Lighter: ${lighter_prices['mid']:.2f} | Paradex: ${paradex_prices['mid']:.2f}")
            
            # 5. Gérer l'entrée en position
            if strategy.current_position and strategy.current_position.status == 'open':
                # On a une position virtuelle ouverte, vérifier si elle existe réellement
                can_trade, reason = await check_trading_conditions(config_base, token)
                
                if can_trade:
                    # La position réelle n'existe pas, on a besoin de la créer
                    logger.warning("⚠️ Position virtuelle détectée mais pas de position réelle")
                    logger.warning("⚠️ Création de la position réelle...")
                    
                    # Exécuter le trade
                    result = await execute_trade_simple(
                        direction=strategy.current_position.direction,
                        token=token,
                        margin=margin,
                        leverage=leverage,
                        lighter_bid=lighter_prices['bid'],
                        lighter_ask=lighter_prices['ask'],
                        paradex_bid=paradex_prices['bid'],
                        paradex_ask=paradex_prices['ask']
                    )
                    
                    if not result.get("success"):
                        logger.error("❌ Échec de la création de la position réelle")
                        logger.error("❌ Réinitialisation de la position virtuelle")
                        strategy.current_position = None
                        strategy.position_open_time = None
                else:
                    # La position réelle existe, surveiller la sortie
                    if tick_count % 10 == 0:
                        logger.info(f"👁️  Surveillance position: direction={strategy.current_position.direction}, spread=${spread_max:.2f}")
            else:
                # Pas de position, vérifier les conditions d'entrée
                if strategy.signal_start_time is not None:
                    # Un signal est en cours de validation
                    pass  # Le log est déjà fait par la stratégie
                
                # Si un nouveau trade vient d'être créé (position virtuelle)
                if strategy.current_position and strategy.current_position.status == 'open':
                    # Vérifier les conditions de trading
                    can_trade, reason = await check_trading_conditions(config_base, token)
                    
                    if can_trade:
                        # Exécuter le trade
                        result = await execute_trade_simple(
                            direction=strategy.current_position.direction,
                            token=token,
                            margin=margin,
                            leverage=leverage,
                            lighter_bid=lighter_prices['bid'],
                            lighter_ask=lighter_prices['ask'],
                            paradex_bid=paradex_prices['bid'],
                            paradex_ask=paradex_prices['ask']
                        )
                        
                        if not result.get("success"):
                            logger.error("❌ Échec du trade, réinitialisation de la position")
                            strategy.current_position = None
                            strategy.position_open_time = None
                    else:
                        logger.warning(f"⚠️ CONDITIONS NON REMPLIES: {reason}")
                        logger.warning("⚠️ Réinitialisation de la position virtuelle")
                        strategy.current_position = None
                        strategy.position_open_time = None
            
            # 6. Gérer la sortie de position
            # Si la stratégie a fermé la position virtuelle, fermer la position réelle
            if strategy.current_position is None:
                # Vérifier si une position réelle existe
                can_trade, reason = await check_trading_conditions(config_base, token)
                
                if not can_trade:
                    # Une position réelle existe mais pas de position virtuelle
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info("🔄 SIGNAL DE SORTIE DÉTECTÉ - Fermeture des positions")
                    logger.info("=" * 80)
                    logger.info("")
                    
                    # Fermer les positions
                    close_result = await close_positions_simple(token, config_base, margin, leverage)
                    
                    if close_result.get("success"):
                        logger.info("")
                        logger.info("=" * 80)
                        logger.info("✅ POSITIONS FERMÉES AVEC SUCCÈS")
                        logger.info("=" * 80)
                        logger.info("")
                    else:
                        logger.error("")
                        logger.error("=" * 80)
                        logger.error("❌ ÉCHEC DE LA FERMETURE DES POSITIONS")
                        logger.error("=" * 80)
                        logger.error("")
            
            # Attendre 1 seconde avant le prochain tick
            await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 80)
            logger.info("🛑 ARRÊT DU BOT (Ctrl+C)")
            logger.info("=" * 80)
            
            # Afficher les stats
            stats = strategy.get_performance_stats()
            logger.info("")
            logger.info("📊 STATISTIQUES FINALES:")
            logger.info(f"   Trades totaux: {stats['total_trades']}")
            logger.info(f"   Trades gagnants: {stats['winning_trades']}")
            logger.info(f"   Trades perdants: {stats['losing_trades']}")
            logger.info(f"   Win rate: {stats['win_rate']:.2f}%")
            logger.info(f"   PnL total: ${stats['total_pnl']:.2f}")
            logger.info(f"   PnL moyen: ${stats['avg_pnl']:.2f}")
            logger.info(f"   Durée moyenne: {stats['avg_duration_s']}s")
            logger.info("")
            
            break
        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle principale: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Bot d'arbitrage stratégie simple")
    parser.add_argument('--token', type=str, default='BTC', help='Token à trader (BTC, ETH)')
    parser.add_argument('--margin', type=float, default=18, help='Marge par position (en $)')
    parser.add_argument('--leverage', type=int, default=50, help='Levier à utiliser')
    parser.add_argument('--entry-spread', type=float, default=15.0, help='Spread minimum pour entrer (en $)')
    parser.add_argument('--exit-spread', type=float, default=5.0, help='Spread maximum pour sortir (en $)')
    parser.add_argument('--min-hold-time', type=int, default=10, help='Durée minimale de détention (secondes)')
    parser.add_argument('--min-duration', type=int, default=4, help='Durée minimale de confirmation (secondes)')
    
    args = parser.parse_args()
    
    # Lancer la boucle
    asyncio.run(run_strategy_loop(
        token=args.token,
        margin=args.margin,
        leverage=args.leverage,
        entry_spread=args.entry_spread,
        exit_spread=args.exit_spread,
        min_hold_time=args.min_hold_time,
        min_duration_s=args.min_duration
    ))


if __name__ == "__main__":
    main()

