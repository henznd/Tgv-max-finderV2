#!/usr/bin/env python3
"""
Script de test pour récupérer les informations complètes du compte Paradex
Teste spécifiquement: total_equity, available_balance, margin_used
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import setup_logger

logger = setup_logger("test_paradex_account_info")

def test_paradex_account_info():
    """Test complet de récupération des informations du compte Paradex"""
    logger.info("=" * 80)
    logger.info("🧪 TEST RÉCUPÉRATION INFORMATIONS COMPTE PARADEX")
    logger.info("=" * 80)
    logger.info(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        from paradex_py import Paradex
        sys.path.append(os.path.join(os.path.dirname(__file__), 'paradex'))
        from paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS
        
        logger.info("📡 Connexion à Paradex...")
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        logger.info("✅ Connexion réussie")
        logger.info("")
        
        # Récupérer account_summary
        logger.info("📊 Récupération de account_summary...")
        account_summary = paradex.api_client.fetch_account_summary()
        logger.info(f"✅ account_summary récupéré")
        logger.info(f"   Type: {type(account_summary)}")
        logger.info("")
        
        # Afficher la structure complète
        if isinstance(account_summary, dict):
            logger.info("📋 account_summary est un dictionnaire:")
            for key, value in account_summary.items():
                logger.info(f"   {key}: {value} (type: {type(value)})")
        else:
            logger.info("📋 account_summary est un objet:")
            logger.info("   Attributs disponibles:")
            for attr in dir(account_summary):
                if not attr.startswith('_'):
                    try:
                        value = getattr(account_summary, attr)
                        if not callable(value):
                            logger.info(f"      {attr}: {value} (type: {type(value)})")
                    except Exception as e:
                        logger.info(f"      {attr}: <erreur: {e}>")
        logger.info("")
        
        # Tester total_equity
        logger.info("💰 Total Equity:")
        if isinstance(account_summary, dict):
            total_equity = account_summary.get("total_equity")
        else:
            total_equity = getattr(account_summary, 'total_equity', None)
        logger.info(f"   Type: {type(total_equity)}")
        logger.info(f"   Valeur: {total_equity}")
        if total_equity is None:
            logger.warning("   ⚠️ total_equity est None")
            # Chercher d'autres noms possibles
            if isinstance(account_summary, dict):
                for key in account_summary.keys():
                    if 'equity' in key.lower() or 'balance' in key.lower():
                        logger.info(f"   🔍 Alternative trouvée: {key} = {account_summary[key]}")
            else:
                for attr in dir(account_summary):
                    if not attr.startswith('_') and ('equity' in attr.lower() or 'balance' in attr.lower()):
                        try:
                            value = getattr(account_summary, attr)
                            if not callable(value):
                                logger.info(f"   🔍 Alternative trouvée: {attr} = {value}")
                        except:
                            pass
        logger.info("")
        
        # Tester available_balance
        logger.info("💵 Available Balance:")
        if isinstance(account_summary, dict):
            available_balance = account_summary.get("available_balance")
        else:
            available_balance = getattr(account_summary, 'available_balance', None)
        logger.info(f"   Type: {type(available_balance)}")
        logger.info(f"   Valeur: {available_balance}")
        if available_balance is None:
            logger.warning("   ⚠️ available_balance est None")
            # Chercher d'autres noms possibles
            if isinstance(account_summary, dict):
                for key in account_summary.keys():
                    if 'available' in key.lower() or 'free' in key.lower() or 'balance' in key.lower():
                        logger.info(f"   🔍 Alternative trouvée: {key} = {account_summary[key]}")
            else:
                for attr in dir(account_summary):
                    if not attr.startswith('_') and ('available' in attr.lower() or 'free' in attr.lower() or 'balance' in attr.lower()):
                        try:
                            value = getattr(account_summary, attr)
                            if not callable(value):
                                logger.info(f"   🔍 Alternative trouvée: {attr} = {value}")
                        except:
                            pass
        logger.info("")
        
        # Tester margin_used
        logger.info("📊 Margin Used:")
        if isinstance(account_summary, dict):
            margin_used = account_summary.get("margin_used")
        else:
            margin_used = getattr(account_summary, 'margin_used', None)
        logger.info(f"   Type: {type(margin_used)}")
        logger.info(f"   Valeur: {margin_used}")
        if margin_used is None:
            logger.warning("   ⚠️ margin_used est None")
            # Chercher d'autres noms possibles
            if isinstance(account_summary, dict):
                for key in account_summary.keys():
                    if 'margin' in key.lower() or 'used' in key.lower():
                        logger.info(f"   🔍 Alternative trouvée: {key} = {account_summary[key]}")
            else:
                for attr in dir(account_summary):
                    if not attr.startswith('_') and ('margin' in attr.lower() or 'used' in attr.lower()):
                        try:
                            value = getattr(account_summary, attr)
                            if not callable(value):
                                logger.info(f"   🔍 Alternative trouvée: {attr} = {value}")
                        except:
                            pass
        logger.info("")
        
        # Tester les positions
        logger.info("📈 Récupération des positions...")
        positions = paradex.api_client.fetch_positions()
        logger.info(f"✅ Positions récupérées")
        logger.info(f"   Type: {type(positions)}")
        if isinstance(positions, dict):
            logger.info(f"   Clés: {list(positions.keys())}")
            if 'results' in positions:
                logger.info(f"   Nombre de positions: {len(positions['results'])}")
                for i, pos in enumerate(positions['results'][:3]):  # Afficher les 3 premières
                    logger.info(f"   Position {i+1}: {pos}")
        logger.info("")
        
        logger.info("=" * 80)
        logger.info("✅ TEST TERMINÉ")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_paradex_account_info()

