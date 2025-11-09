#!/usr/bin/env python3
"""
Script de test pour récupérer les informations complètes du compte Lighter
Teste spécifiquement: total_equity, available_margin, used_margin
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import setup_logger
from trade_verification import TradeVerification

logger = setup_logger("test_lighter_account_info")

async def test_lighter_account_info():
    """Test complet de récupération des informations du compte Lighter"""
    logger.info("=" * 80)
    logger.info("🧪 TEST RÉCUPÉRATION INFORMATIONS COMPTE LIGHTER")
    logger.info("=" * 80)
    logger.info(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        verifier = TradeVerification()
        account_state = await verifier._get_lighter_account_state()
        
        if not account_state:
            logger.error("❌ Aucun état de compte récupéré")
            return
        
        logger.info("✅ État du compte récupéré")
        logger.info("")
        
        # Afficher toutes les clés disponibles
        logger.info("📋 Clés disponibles dans account_state:")
        for key in account_state.keys():
            logger.info(f"   - {key}: {account_state[key]}")
        logger.info("")
        
        # Tester total_equity
        total_equity = account_state.get("total_equity")
        logger.info(f"💰 Total Equity:")
        logger.info(f"   Type: {type(total_equity)}")
        logger.info(f"   Valeur: {total_equity}")
        if total_equity is None:
            logger.warning("   ⚠️ total_equity est None")
        logger.info("")
        
        # Tester available_margin
        available_margin = account_state.get("available_margin")
        logger.info(f"💵 Available Margin:")
        logger.info(f"   Type: {type(available_margin)}")
        logger.info(f"   Valeur: {available_margin}")
        if available_margin is None:
            logger.warning("   ⚠️ available_margin est None")
        logger.info("")
        
        # Tester used_margin
        used_margin = account_state.get("used_margin")
        logger.info(f"📊 Used Margin:")
        logger.info(f"   Type: {type(used_margin)}")
        logger.info(f"   Valeur: {used_margin}")
        if used_margin is None:
            logger.warning("   ⚠️ used_margin est None")
        logger.info("")
        
        # Tester les positions
        positions = account_state.get("positions", [])
        logger.info(f"📈 Positions: {len(positions)}")
        for i, pos in enumerate(positions):
            logger.info(f"   Position {i+1}:")
            for key, value in pos.items():
                logger.info(f"      {key}: {value}")
        logger.info("")
        
        # Test direct avec AccountApi pour voir la structure complète
        logger.info("=" * 80)
        logger.info("🔍 TEST DIRECT AVEC AccountApi (structure brute)")
        logger.info("=" * 80)
        
        try:
            from lighter.api.account_api import AccountApi
            from lighter.api_client import ApiClient
            import aiohttp
            from trade_verification import LIGHTER_BASE_URL, LIGHTER_ACCOUNT_INDEX
            
            api_client = ApiClient()
            api_client.configuration.host = LIGHTER_BASE_URL
            api_client.configuration.ssl_ca_cert = False
            
            connector = aiohttp.TCPConnector(ssl=False)
            api_client.rest_client.pool_manager._connector = connector
            
            account_api = AccountApi(api_client)
            accounts_response = await account_api.account(by="index", value=str(LIGHTER_ACCOUNT_INDEX))
            
            # Extraire le compte
            account = None
            if hasattr(accounts_response, 'accounts') and accounts_response.accounts:
                account = accounts_response.accounts[0]
            elif hasattr(accounts_response, 'account'):
                account = accounts_response.account
            else:
                account = accounts_response
            
            if account:
                logger.info("✅ Compte récupéré directement")
                logger.info(f"📋 Type: {type(account)}")
                logger.info("")
                logger.info("📋 Tous les attributs de l'objet account:")
                for attr in dir(account):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(account, attr)
                            if not callable(value):
                                logger.info(f"   {attr}: {value} (type: {type(value)})")
                        except Exception as e:
                            logger.info(f"   {attr}: <erreur: {e}>")
                
                # Chercher spécifiquement les attributs de marge
                logger.info("")
                logger.info("🔍 Recherche spécifique des attributs de marge:")
                margin_attrs = [
                    'total_equity', 'totalEquity', 'equity', 'Equity',
                    'available_margin', 'availableMargin', 'available_margin_usd', 'availableMarginUsd',
                    'used_margin', 'usedMargin', 'used_margin_usd', 'usedMarginUsd',
                    'margin_stats', 'marginStats', 'margin', 'Margin',
                    'balance', 'Balance', 'total_balance', 'totalBalance'
                ]
                
                for attr_name in margin_attrs:
                    if hasattr(account, attr_name):
                        try:
                            value = getattr(account, attr_name)
                            logger.info(f"   ✅ {attr_name}: {value} (type: {type(value)})")
                            
                            # Si c'est un objet, explorer ses attributs
                            if not isinstance(value, (str, int, float, bool, type(None))):
                                logger.info(f"      (objet complexe, attributs: {[a for a in dir(value) if not a.startswith('_')]})")
                        except Exception as e:
                            logger.info(f"   ⚠️ {attr_name}: <erreur: {e}>")
                    else:
                        logger.info(f"   ❌ {attr_name}: non trouvé")
                
                await api_client.close()
            else:
                logger.error("❌ Impossible de récupérer le compte directement")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test direct: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ TEST TERMINÉ")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_lighter_account_info())

