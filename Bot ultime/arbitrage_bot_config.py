#!/usr/bin/env python3
"""
Bot d'arbitrage configurable - Exécution simultanée atomique de Lighter et Paradex
Utilise des versions Python différentes pour chaque DEX (comme dans arbitrage_bot.py)
"""

import asyncio
import subprocess
import sys
import json
import os
from datetime import datetime
from typing import Optional

# Ajouter le répertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import logger
from logger import setup_logger

# Versions Python pour chaque DEX
PYTHON_LIGHTER = "/usr/bin/python3"  # Python 3.9 pour Lighter
PYTHON_PARADEX = "python3.11"       # Python 3.11 pour Paradex

# Mapping des tokens vers market_index (Lighter)
LIGHTER_MARKET_IDS = {
    "BTC": 1,
    "ETH": 0,
    "SOL": 2,
    "BNB": 25
}

# Mapping des tokens vers les marchés (Paradex)
PARADEX_MARKETS = {
    "BTC": "BTC-USD-PERP",
    "ETH": "ETH-USD-PERP",
    "SOL": "SOL-USD-PERP"
}

async def get_lighter_price_direct(token: str, order_type: str = "buy") -> Optional[float]:
    """
    Récupère le prix d'exécution réel depuis l'API Lighter
    
    Args:
        token: Token à trader
        order_type: "buy" ou "sell" - détermine quel prix utiliser
                   - "buy" -> utilise ASK (prix d'achat)
                   - "sell" -> utilise BID (prix de vente)
    
    Returns:
        Prix d'exécution réel (ASK pour buy, BID pour sell) ou None
    """
    try:
        import aiohttp
        market_id = LIGHTER_MARKET_IDS.get(token)
        if market_id is None:
            return None
        
        async with aiohttp.ClientSession() as session:
            url = f"https://mainnet.zklighter.elliot.ai/api/v1/orderBookOrders?market_id={market_id}&limit=1"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('asks') and data.get('bids') and len(data['asks']) > 0 and len(data['bids']) > 0:
                        ask = float(data['asks'][0]['price'])
                        bid = float(data['bids'][0]['price'])
                        
                        # Pour un BUY, utiliser ASK (prix auquel on peut acheter)
                        # Pour un SELL, utiliser BID (prix auquel on peut vendre)
                        if order_type.lower() == "buy":
                            return ask
                        else:
                            return bid
        return None
    except Exception:
        return None

async def get_paradex_price_direct(token: str, order_type: str = "buy") -> Optional[float]:
    """
    Récupère le prix d'exécution réel depuis l'API Paradex
    
    Args:
        token: Token à trader
        order_type: "buy" ou "sell" - détermine quel prix utiliser
                   - "buy" -> utilise ASK (prix d'achat)
                   - "sell" -> utilise BID (prix de vente)
    
    Returns:
        Prix d'exécution réel (ASK pour buy, BID pour sell) ou None
    """
    try:
        import aiohttp
        market = PARADEX_MARKETS.get(token, f"{token}-USD-PERP")
        market_symbol = f"{token}-USD-PERP"
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.prod.paradex.trade/v1/orderbook/{market_symbol}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('asks') and data.get('bids') and len(data['asks']) > 0 and len(data['bids']) > 0:
                        ask = float(data['asks'][0][0])  # Format: [[price, size], ...]
                        bid = float(data['bids'][0][0])
                        
                        # Pour un BUY, utiliser ASK (prix auquel on peut acheter)
                        # Pour un SELL, utiliser BID (prix auquel on peut vendre)
                        if order_type.lower() == "buy":
                            return ask
                        else:
                            return bid
                else:
                    # Log l'erreur pour debug
                    error_text = await response.text()
                    logger = setup_logger("arbitrage_bot")
                    logger.warning(f"⚠️ Paradex API error {response.status}: {error_text[:200]}")
        return None
    except Exception as e:
        # Log l'exception pour debug
        logger = setup_logger("arbitrage_bot")
        logger.warning(f"⚠️ Erreur récupération prix Paradex: {e}")
        import traceback
        logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
        return None

def load_config():
    """Charger la configuration depuis le fichier JSON"""
    config_file = os.path.join(os.path.dirname(__file__), "trading_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erreur lecture config: {e}")
    
    # Configuration par défaut
    return {
        "lighter": {
            "token": "BTC",
            "amount": 0.00001,
            "leverage": 10,
            "order_type": "buy"
        },
        "paradex": {
            "token": "ETH",
            "amount": 0.03,
            "leverage": 50,
            "order_type": "buy"
        }
    }

async def execute_simultaneous_trades(config):
    """
    Exécute les trades sur Lighter et Paradex simultanément de manière atomique
    
    Args:
        config: Configuration chargée depuis trading_config.json
    
    Returns:
        dict: Résultats des deux trades
    """
    logger = setup_logger("arbitrage_bot")
    
    logger.info("=" * 60)
    logger.info("🤖 BOT D'ARBITRAGE - EXECUTION SIMULTANÉE ATOMIQUE")
    logger.info("=" * 60)
    logger.info(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Vérifier que les deux DEX tradent le même token
    lighter_token = config.get('lighter', {}).get('token', 'BTC')
    paradex_token = config.get('paradex', {}).get('token', 'ETH')
    
    if lighter_token != paradex_token:
        logger.warning(f"⚠️ ATTENTION: Tokens différents! Lighter={lighter_token}, Paradex={paradex_token}")
        logger.warning("⚠️ Pour un arbitrage, les deux DEX doivent trader le même token")
    
    # Afficher la configuration
    logger.info("📋 Configuration actuelle:")
    lighter_config = config.get('lighter', {})
    paradex_config = config.get('paradex', {})
    
    logger.info(f"   ⚡ Lighter: {lighter_config.get('token')} - {lighter_config.get('amount')} - {lighter_config.get('leverage')}x - {lighter_config.get('order_type', 'buy').upper()}")
    logger.info(f"   🎯 Paradex: {paradex_config.get('token')} - {paradex_config.get('amount')} - {paradex_config.get('leverage')}x - {paradex_config.get('order_type', 'buy').upper()}")
    logger.info("=" * 60)
    
    # Vérifier que les paramètres sont identiques (pour l'objectif immédiat)
    if (lighter_config.get('token') == paradex_config.get('token') and
        lighter_config.get('amount') == paradex_config.get('amount') and
        lighter_config.get('leverage') == paradex_config.get('leverage')):
        logger.info("✅ Configuration validée: même token, même taille, même levier")
    else:
        logger.warning("⚠️ Les paramètres ne sont pas identiques entre les deux DEX")
    
    # Récupérer les prix en temps réel depuis les APIs AVANT de placer les ordres
    logger.info("\n📡 Récupération des prix en temps réel depuis les APIs...")
    token = lighter_config.get('token', 'ETH')
    
    lighter_price = None
    paradex_price = None
    
    try:
        # Récupérer les prix directement depuis les APIs
        # Utiliser le prix d'exécution réel selon le type d'ordre
        lighter_order_type = lighter_config.get('order_type', 'buy')
        paradex_order_type = paradex_config.get('order_type', 'buy')
        
        logger.info("   ⏳ Récupération des prix en cours...")
        lighter_price, paradex_price = await asyncio.gather(
            get_lighter_price_direct(token, lighter_order_type),
            get_paradex_price_direct(token, paradex_order_type)
        )
            
    except Exception as e:
        logger.error(f"   ❌ Erreur lors de la récupération des prix: {e}")
        import traceback
        logger.error(f"   🔍 Traceback: {traceback.format_exc()}")
        lighter_price = None
        paradex_price = None
    
    # VÉRIFICATION CRITIQUE: Les deux prix doivent être récupérés avec succès
    if not lighter_price or not paradex_price:
        logger.error("=" * 60)
        logger.error("❌ ÉCHEC: Impossible de récupérer les prix nécessaires")
        logger.error("=" * 60)
        if not lighter_price:
            logger.error(f"   ❌ Prix Lighter {token}: NON DISPONIBLE")
        else:
            logger.info(f"   ✅ Prix Lighter {token}: ${lighter_price}")
        
        if not paradex_price:
            logger.error(f"   ❌ Prix Paradex {token}: NON DISPONIBLE")
        else:
            logger.info(f"   ✅ Prix Paradex {token}: ${paradex_price}")
        
        logger.error("")
        logger.error("⚠️ Le bot ne peut pas s'exécuter sans les prix réels du marché")
        logger.error("⚠️ Raison: Risque de slippage trop élevé avec des prix par défaut")
        logger.error("")
        logger.error("💡 Solutions possibles:")
        logger.error("   - Vérifier la connexion aux APIs Lighter et Paradex")
        logger.error("   - Vérifier que les SDKs sont correctement installés")
        logger.error("   - Réessayer dans quelques instants")
        logger.error("=" * 60)
        
        return {
            "success": False,
            "error": "Prix non disponibles",
            "lighter_price": lighter_price,
            "paradex_price": paradex_price,
            "message": "Impossible de récupérer les prix nécessaires pour éviter le slippage"
        }
    
    # Les deux prix sont disponibles - continuer
    logger.info("=" * 60)
    logger.info("✅ PRIX RÉCUPÉRÉS AVEC SUCCÈS - Calcul de la position")
    logger.info("=" * 60)
    logger.info(f"   ✅ Prix Lighter {token} ({lighter_order_type.upper()}): ${lighter_price:.2f}")
    logger.info(f"   ✅ Prix Paradex {token} ({paradex_order_type.upper()}): ${paradex_price:.2f}")
    
    # Calculer le montant exact pour avoir exactement la position configurée
    # Position totale = margin * leverage
    margin = lighter_config.get('margin', 100)
    leverage = lighter_config.get('leverage', 10)
    position_value = margin * leverage  # Exemple: 2 * 50 = 100$
    
    logger.info(f"\n💰 CALCUL DE LA POSITION:")
    logger.info(f"   📊 Marge configurée: ${margin:.2f}")
    logger.info(f"   📊 Levier configuré: {leverage}x")
    logger.info(f"   📊 Position totale calculée: ${position_value:.2f} (${margin:.2f} × {leverage}x)")
    
    # Calculer le montant pour CHAQUE DEX en utilisant le prix MID (moyenne bid/ask)
    # IMPORTANT: Utiliser le prix MID pour le calcul du montant, pas le prix brut bid/ask
    # Le market_price (avec marge de sécurité) sera utilisé pour l'exécution, mais pas pour le calcul du montant
    
    # Récupérer les prix bid/ask depuis la config si disponibles
    lighter_bid = config['lighter'].get('bid')
    lighter_ask = config['lighter'].get('ask')
    paradex_bid = config['paradex'].get('bid')
    paradex_ask = config['paradex'].get('ask')
    
    # Utiliser le prix MID pour le calcul du montant (plus précis que bid ou ask seul)
    if lighter_bid and lighter_ask:
        lighter_mid = (lighter_bid + lighter_ask) / 2
        lighter_amount = position_value / lighter_mid
        logger.info(f"\n📏 CALCUL DU MONTANT EN {token}:")
        logger.info(f"   📊 Prix MID Lighter: ${lighter_mid:.2f} (bid=${lighter_bid:.2f}, ask=${lighter_ask:.2f}) → Montant: {lighter_amount:.8f} {token}")
    else:
        # Fallback: utiliser le prix brut si bid/ask non disponibles
        lighter_amount = position_value / lighter_price
        logger.info(f"\n📏 CALCUL DU MONTANT EN {token}:")
        logger.info(f"   📊 Prix brut Lighter: ${lighter_price:.2f} → Montant: {lighter_amount:.8f} {token}")
    
    if paradex_bid and paradex_ask:
        paradex_mid = (paradex_bid + paradex_ask) / 2
        paradex_amount = position_value / paradex_mid
        logger.info(f"   📊 Prix MID Paradex: ${paradex_mid:.2f} (bid=${paradex_bid:.2f}, ask=${paradex_ask:.2f}) → Montant: {paradex_amount:.8f} {token}")
    else:
        # Fallback: utiliser le prix brut si bid/ask non disponibles
        paradex_amount = position_value / paradex_price
        logger.info(f"   📊 Prix brut Paradex: ${paradex_price:.2f} → Montant: {paradex_amount:.8f} {token}")
    
    logger.info(f"   💰 Valeur de la position: ${position_value:.2f} pour chaque DEX")
    
    # Mettre à jour les montants dans la config
    # IMPORTANT: NE JAMAIS configurer market_price - laisser le fallback dans lighter_trader_config.py le calculer
    # Le fallback utilisera automatiquement bid/ask avec marge de sécurité
    config['lighter']['amount'] = lighter_amount
    config['paradex']['amount'] = paradex_amount
    
    # S'assurer que bid/ask sont présents pour le fallback
    if 'bid' not in config['lighter'] or config['lighter'].get('bid') is None:
        # Si bid/ask ne sont pas dans la config, essayer de les récupérer depuis les prix récupérés
        # Mais normalement ils devraient déjà être là depuis create_trade_config_from_signal
        logger.warning("   ⚠️ bid/ask Lighter non présents dans la config - le fallback pourrait ne pas fonctionner")
    
    if 'bid' not in config['paradex'] or config['paradex'].get('bid') is None:
        logger.warning("   ⚠️ bid/ask Paradex non présents dans la config - le fallback pourrait ne pas fonctionner")
    
    logger.info(f"   ✅ Montant Lighter: {lighter_amount:.8f} {token} (valeur: ${position_value:.2f})")
    logger.info(f"   ✅ Montant Paradex: {paradex_amount:.8f} {token} (valeur: ${position_value:.2f})")
    
    # Afficher la différence de prix
    diff = abs(lighter_price - paradex_price)
    diff_percent = (diff / lighter_price) * 100 if lighter_price > 0 else 0
    logger.info(f"   📊 Différence de prix: ${diff:.2f} ({diff_percent:.2f}%)")
    if diff_percent > 0.5:
        logger.info(f"   💰 Opportunité d'arbitrage détectée!")
    
    logger.info("\n🚀 Lancement simultané des trades avec les prix réels...")
    logger.info("   ⏱️  Les deux ordres seront exécutés en parallèle pour maximiser l'atomicité")
    logger.info(f"   🐍 Lighter: {PYTHON_LIGHTER}")
    logger.info(f"   🐍 Paradex: {PYTHON_PARADEX}")
    
    # Sauvegarder la config mise à jour avec les prix dans un fichier temporaire
    # pour que les subprocess puissent y accéder
    import tempfile
    import json
    temp_config_file = os.path.join(current_dir, "trading_config_temp.json")
    try:
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        # Utiliser ce fichier temporaire pour les subprocess
        original_config_file = os.path.join(current_dir, "trading_config.json")
        # Les subprocess liront trading_config.json, donc on le met à jour
        with open(original_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.warning(f"   ⚠️ Impossible de sauvegarder la config avec les prix: {e}")
    
    # Exécuter les deux trades simultanément via subprocess avec les bonnes versions Python
    start_time = datetime.now()
    
    def run_lighter_subprocess():
        """Lance le trader Lighter avec Python 3.9"""
        try:
            result = subprocess.run(
                [PYTHON_LIGHTER, os.path.join(current_dir, "lighter", "lighter_trader_config.py")],
                capture_output=True,
                text=True,
                cwd=current_dir,
                timeout=60
            )
            # Parser la sortie pour extraire le résultat JSON
            output_combined = result.stdout + result.stderr
            
            # Essayer de parser le JSON depuis la sortie
            import json
            import re
            json_match = re.search(r'RESULT_JSON_START\s*\n(.*?)\nRESULT_JSON_END', output_combined, re.DOTALL)
            if json_match:
                try:
                    parsed_result = json.loads(json_match.group(1))
                    return parsed_result
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Parser basique si pas de JSON
            success_indicators = [
                "✅ Ordre placé avec succès",
                "✅ Ordre placé",
                "'success': True",
                "tx_hash",
                "RespSendTx"
            ]
            
            if result.returncode == 0:
                # Chercher des indices de succès dans la sortie
                if any(indicator in output_combined for indicator in success_indicators):
                    return {"success": True, "output": result.stdout, "stderr": result.stderr}
                else:
                    return {"success": False, "error": "Pas d'indication de succès", "output": result.stdout, "stderr": result.stderr}
            else:
                return {"success": False, "error": result.stderr or "Code de retour non-zéro", "output": result.stdout, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_paradex_subprocess():
        """Lance le trader Paradex avec Python 3.11"""
        try:
            result = subprocess.run(
                [PYTHON_PARADEX, os.path.join(current_dir, "paradex", "paradex_trader_config.py")],
                capture_output=True,
                text=True,
                cwd=current_dir,
                timeout=60
            )
            # Parser la sortie pour extraire le résultat JSON
            output_combined = result.stdout + result.stderr
            
            # Essayer de parser le JSON depuis la sortie
            import json
            import re
            json_match = re.search(r'RESULT_JSON_START\s*\n(.*?)\nRESULT_JSON_END', output_combined, re.DOTALL)
            if json_match:
                try:
                    parsed_result = json.loads(json_match.group(1))
                    return parsed_result
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Parser basique si pas de JSON
            success_indicators = [
                "✅ Ordre placé avec succès",
                "✅ Ordre placé",
                "'id':",
                "status': 'NEW'",
                "'success': True"
            ]
            
            if result.returncode == 0:
                # Chercher des indices de succès dans la sortie
                if any(indicator in output_combined for indicator in success_indicators):
                    return {"success": True, "output": result.stdout, "stderr": result.stderr}
                else:
                    return {"success": False, "error": "Pas d'indication de succès", "output": result.stdout, "stderr": result.stderr}
            else:
                return {"success": False, "error": result.stderr or "Code de retour non-zéro", "output": result.stdout, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    try:
        # Créer les deux tâches asynchrones via subprocess
        loop = asyncio.get_event_loop()
        lighter_task = loop.run_in_executor(None, run_lighter_subprocess)
        paradex_task = loop.run_in_executor(None, run_paradex_subprocess)
        
        # Exécuter en parallèle et attendre les deux résultats
        results = await asyncio.gather(
            lighter_task,
            paradex_task,
            return_exceptions=True
        )
        
        lighter_result, paradex_result = results
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Analyser les résultats
        logger.info("\n" + "=" * 60)
        logger.info("📊 RÉSULTATS DE L'EXÉCUTION")
        logger.info("=" * 60)
        logger.info(f"⏱️  Temps d'exécution: {execution_time:.3f} secondes")
        
        # Résultat Lighter
        lighter_verification = None
        if isinstance(lighter_result, Exception):
            logger.error(f"❌ [LIGHTER] Erreur: {lighter_result}")
            lighter_success = False
            lighter_output = str(lighter_result)
            lighter_executed = False
            lighter_status = "exception"
        else:
            lighter_success = lighter_result.get('success', False)
            lighter_output = lighter_result.get('output', '')
            lighter_executed = lighter_result.get('order_executed', False)
            lighter_status = lighter_result.get('execution_status', 'unknown')
            lighter_verification = lighter_result.get('verification')
            
            if lighter_success:
                # Vérifier si une position existe réellement (plus fiable que order_executed)
                position_found = False
                if lighter_verification:
                    position_found = lighter_verification.get('position_found', False)
                    # Si position_found est True, le trade est exécuté même si order_executed est False
                    if position_found:
                        lighter_executed = True
                
                # Vérifier aussi si executed est True dans la vérification (plus fiable)
                if lighter_verification and lighter_verification.get('executed', False):
                    lighter_executed = True
                    position_found = True
                
                if lighter_executed or position_found:
                    logger.info(f"✅ [LIGHTER] Trade réussi ET exécuté confirmé!")
                    logger.info(f"   📊 Statut: {lighter_status}")
                    
                    # Afficher les détails de vérification
                    if lighter_verification:
                        if lighter_verification.get('position_found') or lighter_verification.get('executed', False):
                            position_size = lighter_verification.get('position_size', 0)
                            if abs(position_size) > 0:
                                logger.info(f"   📊 Position: {position_size} {lighter_config.get('token')}")
                            if lighter_verification.get('liquidation_price'):
                                logger.info(f"   ⚠️ Prix liquidation: ${lighter_verification.get('liquidation_price'):.2f}")
                            if lighter_verification.get('health_factor'):
                                logger.info(f"   📊 Health factor: {lighter_verification.get('health_factor'):.2f}")
                        if lighter_verification.get('balance_after'):
                            balance = lighter_verification.get('balance_after')
                            logger.info(f"   💰 Equity: ${balance.get('total_equity', 'N/A')}")
                            logger.info(f"   💵 Marge disponible: ${balance.get('available_margin', 'N/A')}")
                else:
                    logger.warning(f"⚠️ [LIGHTER] Ordre placé mais NON exécuté (slippage/annulation)")
                    logger.warning(f"   📊 Statut: {lighter_status}")
                    # Ne pas mettre lighter_success à False si le trade a été placé avec succès
                    # Seulement si vraiment aucune position n'existe
                    if not position_found:
                        lighter_success = False
                logger.debug(f"📋 Sortie Lighter: {lighter_output[-500:]}")
            else:
                logger.error(f"❌ [LIGHTER] Trade échoué: {lighter_result.get('error', 'Erreur inconnue')}")
                logger.debug(f"📋 Sortie Lighter: {lighter_output[-500:]}")
        
        # Résultat Paradex
        paradex_verification = None
        if isinstance(paradex_result, Exception):
            logger.error(f"❌ [PARADEX] Erreur: {paradex_result}")
            paradex_success = False
            paradex_output = str(paradex_result)
            paradex_executed = False
            paradex_status = "exception"
        else:
            paradex_success = paradex_result.get('success', False)
            paradex_output = paradex_result.get('output', '')
            paradex_executed = paradex_result.get('order_executed', False)
            paradex_status = paradex_result.get('execution_status', 'unknown')
            paradex_verification = paradex_result.get('verification')
            
            if paradex_success:
                # Vérifier si une position existe réellement (plus fiable que order_executed)
                position_found = False
                if paradex_verification:
                    position_found = paradex_verification.get('position_found', False)
                    # Si position_found est True, le trade est exécuté même si order_executed est False
                    if position_found:
                        paradex_executed = True
                
                if paradex_executed or position_found:
                    logger.info(f"✅ [PARADEX] Trade réussi ET exécuté confirmé!")
                    logger.info(f"   📊 Statut: {paradex_status}")
                    
                    # Afficher les détails de vérification
                    if paradex_verification:
                        if paradex_verification.get('position_found'):
                            logger.info(f"   📊 Position: {paradex_verification.get('position_size', 0)} {paradex_config.get('token')}")
                            if paradex_verification.get('liquidation_price'):
                                logger.info(f"   ⚠️ Prix liquidation: ${paradex_verification.get('liquidation_price'):.2f}")
                            if paradex_verification.get('health_factor'):
                                logger.info(f"   📊 Health factor: {paradex_verification.get('health_factor'):.2f}")
                        if paradex_verification.get('balance_after'):
                            balance = paradex_verification.get('balance_after')
                            logger.info(f"   💰 Equity: ${balance.get('total_equity', 'N/A')}")
                            logger.info(f"   💵 Balance disponible: ${balance.get('available_balance', 'N/A')}")
                else:
                    logger.warning(f"⚠️ [PARADEX] Ordre placé mais NON exécuté")
                    logger.warning(f"   📊 Statut: {paradex_status}")
                    # Ne pas mettre paradex_success à False si le trade a été placé avec succès
                    # Seulement si vraiment aucune position n'existe
                    if not position_found:
                        paradex_success = False
                logger.debug(f"📋 Sortie Paradex: {paradex_output[-500:]}")
            else:
                logger.error(f"❌ [PARADEX] Trade échoué: {paradex_result.get('error', 'Erreur inconnue')}")
                logger.debug(f"📋 Sortie Paradex: {paradex_output[-500:]}")
        
        # Résultat global - Vérifier si les positions existent réellement
        lighter_has_position = False
        paradex_has_position = False
        
        if lighter_verification:
            lighter_has_position = lighter_verification.get('position_found', False)
        if paradex_verification:
            paradex_has_position = paradex_verification.get('position_found', False)
        
        # Considérer un trade comme réussi si soit success=True, soit une position existe
        lighter_final_success = lighter_success or lighter_has_position
        paradex_final_success = paradex_success or paradex_has_position
        
        logger.info("=" * 60)
        if lighter_final_success and paradex_final_success:
            logger.info("🎉 SUCCÈS: Les deux trades ont été exécutés avec succès!")
            logger.info("✅ Arbitrage exécuté simultanément")
            
            # Vérifier les risques de liquidation
            if lighter_verification and lighter_verification.get('liquidation_price'):
                logger.info(f"   ⚠️ Lighter liquidation: ${lighter_verification.get('liquidation_price'):.2f}")
            if paradex_verification and paradex_verification.get('liquidation_price'):
                logger.info(f"   ⚠️ Paradex liquidation: ${paradex_verification.get('liquidation_price'):.2f}")
        elif lighter_final_success or paradex_final_success:
            logger.error("=" * 60)
            logger.error("❌ ÉCHEC PARTIEL: Un seul trade a réussi!")
            logger.error("=" * 60)
            logger.error("⚠️ RISQUE CRITIQUE: Position non couverte!")
            logger.error("")
            if lighter_final_success:
                logger.error(f"   ✅ Lighter: OK (position ouverte)")
                logger.error(f"   ❌ Paradex: ÉCHEC (pas de position)")
                logger.error("")
                logger.error("💡 ACTIONS RECOMMANDÉES:")
                logger.error("   1. Fermer manuellement la position Lighter")
                logger.error("   2. Vérifier pourquoi Paradex a échoué")
                logger.error("   3. Ne pas relancer le bot tant que la position n'est pas fermée")
            else:
                logger.error(f"   ❌ Lighter: ÉCHEC (pas de position)")
                logger.error(f"   ✅ Paradex: OK (position ouverte)")
                logger.error("")
                logger.error("💡 ACTIONS RECOMMANDÉES:")
                logger.error("   1. Fermer manuellement la position Paradex")
                logger.error("   2. Vérifier pourquoi Lighter a échoué")
                logger.error("   3. Ne pas relancer le bot tant que la position n'est pas fermée")
            logger.error("=" * 60)
        else:
            logger.error("❌ ÉCHEC: Aucun trade n'a réussi")
            logger.error("✅ Aucune position ouverte - pas de risque")
        
        logger.info("=" * 60)
        
        return {
            "success": lighter_success and paradex_success,
            "lighter": lighter_result if not isinstance(lighter_result, Exception) else {"error": str(lighter_result)},
            "paradex": paradex_result if not isinstance(paradex_result, Exception) else {"error": str(paradex_result)},
            "execution_time": execution_time
        }
            
    except Exception as e:
        logger.error(f"❌ Erreur fatale lors de l'exécution simultanée: {e}")
        import traceback
        logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
        raise

async def run_both_async():
    """Lance les deux trades en parallèle"""
    try:
        config = load_config()
        result = await execute_simultaneous_trades(config)
        return result
    except Exception as e:
        logger = setup_logger("arbitrage_bot")
        logger.error(f"❌ Erreur: {e}")
        raise

def main():
    """Fonction principale"""
    logger = setup_logger("arbitrage_bot")
    
    try:
        result = asyncio.run(run_both_async())
        logger.info("\n🏁 ARBITRAGE TERMINÉ")
        logger.info(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return result
    except KeyboardInterrupt:
        logger.warning("\n🛑 Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        import traceback
        logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
