#!/usr/bin/env python3
"""
Bot d'arbitrage SIMPLE basé sur le spread brut
Version simplifiée et fiabilisée - Sans subprocess, code direct
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from logger import setup_logger
from arbitrage_strategy_simple import ArbitrageStrategySimple, StrategyParamsSimple
from trade_executor_simple import execute_arbitrage_trade
from position_manager_simple import get_all_positions, close_all_positions

logger = setup_logger("arbitrage_bot_simple")


async def get_prices(token: str):
    """Récupère les prix bid/ask des deux exchanges"""
    from arbitrage_bot_config import get_lighter_price_direct, get_paradex_price_direct
    
    lighter_bid, lighter_ask, paradex_bid, paradex_ask = await asyncio.gather(
        get_lighter_price_direct(token, "sell"),  # bid
        get_lighter_price_direct(token, "buy"),   # ask
        get_paradex_price_direct(token, "sell"),  # bid
        get_paradex_price_direct(token, "buy")    # ask
    )
    
    return lighter_bid, lighter_ask, paradex_bid, paradex_ask


async def check_trading_conditions(token: str) -> tuple[bool, str]:
    """
    Vérifie si on peut trader (pas de position ouverte)
    
    Returns:
        (can_trade, reason)
    """
    positions = await get_all_positions(token)
    
    lighter_pos = positions["lighter"]
    paradex_pos = positions["paradex"]
    
    if lighter_pos and abs(lighter_pos["size"]) > 0.00001:
        return False, f"Position Lighter déjà ouverte ({lighter_pos['direction']})"
    
    if paradex_pos and abs(paradex_pos["size"]) > 0.00001:
        return False, f"Position Paradex déjà ouverte ({paradex_pos['direction']})"
    
    return True, "OK"


async def run_strategy_loop(token: str, margin: float, leverage: int,
                           entry_spread: float, exit_spread: float,
                           min_hold_time: int, min_duration_s: int = 4):
    """
    Boucle principale de la stratégie
    
    Args:
        token: Token à trader
        margin: Marge par position
        leverage: Levier
        entry_spread: Spread d'entrée minimum
        exit_spread: Spread de sortie maximum
        min_hold_time: Temps de détention minimum (secondes)
        min_duration_s: Durée de validation du signal (secondes)
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🤖 BOT D'ARBITRAGE STRATÉGIE SIMPLE")
    logger.info("=" * 80)
    logger.info(f"   Token: {token}")
    logger.info(f"   Marge: ${margin}, Levier: {leverage}x")
    logger.info(f"   Spread entrée: ${entry_spread}")
    logger.info(f"   Spread sortie: ${exit_spread}")
    logger.info(f"   Hold time min: {min_hold_time}s")
    logger.info(f"   Durée validation: {min_duration_s}s")
    logger.info("=" * 80)
    logger.info("")
    
    # Créer la stratégie
    params = StrategyParamsSimple(
        entry_spread=entry_spread,
        exit_spread=exit_spread,
        min_hold_time=min_hold_time,
        min_duration_s=min_duration_s
    )
    strategy = ArbitrageStrategySimple(params)
    
    tick_count = 0
    
    while True:
        try:
            tick_count += 1
            
            # 1. Récupérer les prix
            lighter_bid, lighter_ask, paradex_bid, paradex_ask = await get_prices(token)
            
            if not all([lighter_bid, lighter_ask, paradex_bid, paradex_ask]):
                logger.warning("⚠️ Prix non disponibles, attente...")
                await asyncio.sleep(1)
                continue
            
            # 2. Calculer les spreads
            spread_sell_lighter = lighter_bid - paradex_ask  # Vendre Lighter, acheter Paradex
            spread_sell_paradex = paradex_bid - lighter_ask  # Vendre Paradex, acheter Lighter
            
            # Le spread max est celui qu'on surveille
            if abs(spread_sell_lighter) > abs(spread_sell_paradex):
                spread_max = spread_sell_lighter
                direction = 'sell_lighter'
            else:
                spread_max = spread_sell_paradex
                direction = 'sell_paradex'
            
            current_time = datetime.now()
            
            # 3. Passer les données à la stratégie
            strategy.process_tick(spread_max, direction, current_time)
            
            # Logs périodiques
            if tick_count % 10 == 0:
                logger.info(f"⏱️  Tick {tick_count} | Spread: ${spread_max:.2f} ({direction}) | Lighter: ${(lighter_bid+lighter_ask)/2:.2f} | Paradex: ${(paradex_bid+paradex_ask)/2:.2f}")
            
            # 4. Gérer l'entrée en position
            if strategy.current_position and strategy.current_position.status == 'open':
                # Position virtuelle créée, vérifier si on peut trader
                can_trade, reason = await check_trading_conditions(token)
                
                if can_trade:
                    logger.info("")
                    logger.info("🎯 SIGNAL D'ENTRÉE VALIDÉ - EXÉCUTION")
                    
                    # Exécuter le trade
                    result = await execute_arbitrage_trade(
                        direction=strategy.current_position.direction,
                        token=token,
                        margin=margin,
                        leverage=leverage,
                        lighter_bid=lighter_bid,
                        lighter_ask=lighter_ask,
                        paradex_bid=paradex_bid,
                        paradex_ask=paradex_ask
                    )
                    
                    if result.get("success"):
                        logger.info("✅ POSITION OUVERTE AVEC SUCCÈS")
                        # La position reste ouverte dans la stratégie
                    else:
                        logger.error("❌ ÉCHEC DU TRADE - Annulation de la position virtuelle")
                        strategy.current_position = None
                        strategy.position_open_time = None
                else:
                    logger.warning(f"⚠️ CONDITIONS NON REMPLIES: {reason}")
                    logger.warning("⚠️ Annulation de la position virtuelle")
                    strategy.current_position = None
                    strategy.position_open_time = None
            
            # 5. Gérer la sortie de position
            # Si la stratégie a fermé la position virtuelle, fermer la position réelle
            if len(strategy.trades) > 0:
                last_trade = strategy.trades[-1]
                if last_trade.status == 'closed' and last_trade.exit_time:
                    # Vérifier si on n'a pas déjà fermé cette position
                    if not hasattr(last_trade, '_real_position_closed'):
                        logger.info("")
                        logger.info(f"📉 SIGNAL DE SORTIE VALIDÉ - FERMETURE (raison: {last_trade.exit_reason})")
                        
                        # Fermer les positions réelles
                        close_result = await close_all_positions(
                            token=token,
                            lighter_bid=lighter_bid,
                            lighter_ask=lighter_ask,
                            paradex_bid=paradex_bid,
                            paradex_ask=paradex_ask,
                            leverage=leverage
                        )
                        
                        if close_result.get("success"):
                            logger.info(f"✅ POSITION FERMÉE - PnL: ${last_trade.pnl:.2f} ({last_trade.pnl_percent:.2f}%)")
                        else:
                            logger.error("❌ ÉCHEC FERMETURE DE POSITION")
                        
                        # Marquer comme fermée pour ne pas réessayer
                        last_trade._real_position_closed = True
            
            # Attendre 1 seconde
            await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt demandé par l'utilisateur")
            break
        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await asyncio.sleep(1)
    
    # Statistiques finales
    stats = strategy.get_performance_stats()
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 STATISTIQUES FINALES")
    logger.info("=" * 80)
    logger.info(f"   Trades totaux: {stats['total_trades']}")
    logger.info(f"   Trades gagnants: {stats['winning_trades']}")
    logger.info(f"   Trades perdants: {stats['losing_trades']}")
    logger.info(f"   PnL total: ${stats['total_pnl']:.2f}")
    logger.info(f"   Win rate: {stats['win_rate']:.1f}%")
    if stats['avg_pnl']:
        logger.info(f"   PnL moyen: ${stats['avg_pnl']:.2f}")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Bot d\'arbitrage simple')
    parser.add_argument('--token', type=str, default='BTC', help='Token à trader')
    parser.add_argument('--margin', type=float, default=18, help='Marge par position')
    parser.add_argument('--leverage', type=int, default=50, help='Levier')
    parser.add_argument('--entry-spread', type=float, default=15, help='Spread d\'entrée minimum')
    parser.add_argument('--exit-spread', type=float, default=5, help='Spread de sortie maximum')
    parser.add_argument('--min-hold-time', type=int, default=10, help='Temps de détention minimum (secondes)')
    
    args = parser.parse_args()
    
    asyncio.run(run_strategy_loop(
        token=args.token,
        margin=args.margin,
        leverage=args.leverage,
        entry_spread=args.entry_spread,
        exit_spread=args.exit_spread,
        min_hold_time=args.min_hold_time
    ))


if __name__ == "__main__":
    main()
