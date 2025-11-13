#!/usr/bin/env python3
"""
Script de test pour démontrer le nouveau système de logs simplifié
"""

import asyncio
import time
from simple_logger import setup_simple_logger

async def demo_logs():
    """Démonstration des logs simplifiés avec couleurs"""
    
    logger = setup_simple_logger("demo")
    
    print("\n" + "="*80)
    print("DÉMONSTRATION DES LOGS SIMPLIFIÉS AVEC COULEURS")
    print("="*80 + "\n")
    
    # 1. Bot lancé
    logger.bot_started(token="BTC", margin=20, leverage=50)
    await asyncio.sleep(2)
    
    # 2. Trade ouvert - LONG
    logger.trade_opened(
        direction="long_spread",
        token="BTC",
        amount=0.001,
        entry_price=98500.50,
        entry_z=2.5
    )
    await asyncio.sleep(3)
    
    # 3. Trade fermé avec PNL positif
    logger.trade_closed(
        direction="long_spread",
        token="BTC",
        exit_price=98650.25,
        exit_z=0.8,
        pnl=15.50,
        pnl_percent=2.3
    )
    await asyncio.sleep(2)
    
    # 4. Trade ouvert - SHORT
    logger.trade_opened(
        direction="short_spread",
        token="ETH",
        amount=0.05,
        entry_price=3250.75,
        entry_z=3.1
    )
    await asyncio.sleep(3)
    
    # 5. Trade fermé avec PNL négatif
    logger.trade_closed(
        direction="short_spread",
        token="ETH",
        exit_price=3265.50,
        exit_z=0.5,
        pnl=-8.25,
        pnl_percent=-1.2
    )
    await asyncio.sleep(2)
    
    # 6. Warning
    logger.warning("Historique insuffisant - Attente de données...")
    await asyncio.sleep(2)
    
    # 7. Erreur
    logger.error("Échec de la connexion à l'exchange")
    await asyncio.sleep(2)
    
    print("\n" + "="*80)
    print("FIN DE LA DÉMONSTRATION")
    print("="*80 + "\n")
    
    print("📝 Note:")
    print("  - Les logs en COULEUR apparaissent en console")
    print("  - Les logs DÉTAILLÉS sont aussi sauvegardés dans les fichiers logs/")
    print("  - En production, seuls les événements importants seront affichés en console")
    print("  - Les informations techniques complètes restent dans les fichiers logs\n")

if __name__ == "__main__":
    asyncio.run(demo_logs())

