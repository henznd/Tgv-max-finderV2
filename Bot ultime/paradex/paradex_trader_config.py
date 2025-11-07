#!/usr/bin/env python3
"""
Trader Paradex configurable - Lit la configuration depuis trading_config.json
"""

import asyncio
import json
import os
import sys
import re
from datetime import datetime
from paradex_py import Paradex
from paradex_py.common.order import Order, OrderSide, OrderType
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import du système de logs
from logger import setup_logger

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
L1_ADDRESS = "0x19bF8d22f9772b1F349a803e5B640087f3d29C2a"

# Mapping des tokens vers les marchés Paradex
TOKEN_MARKET = {
    "BTC": "BTC-USD-PERP",
    "ETH": "ETH-USD-PERP",
    "SOL": "SOL-USD-PERP",
    "USDC": "USDC-USD-PERP"
}

def load_config():
    """Charger la configuration depuis trading_config.json"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erreur lecture config: {e}")
    else:
        raise Exception(f"Fichier de configuration non trouvé: {config_file}")

async def execute_trade(config_data):
    """Exécute un trade sur Paradex selon la configuration"""
    logger = setup_logger("paradex_trader")
    
    paradex_config = config_data.get('paradex', {})
    if not paradex_config:
        raise Exception("Configuration Paradex non trouvée dans trading_config.json")
    
    token = paradex_config.get('token', 'ETH')
    amount = float(paradex_config.get('amount', 0.03))
    leverage = int(paradex_config.get('leverage', 50))
    order_type = paradex_config.get('order_type', 'buy')
    
    # Paradex accepte une précision de 0.00001 (5 décimales) pour BTC
    # Utiliser Decimal pour éviter les problèmes de précision flottante
    amount_decimal = Decimal(str(amount))
    # Utiliser 0.00001 pour BTC afin de garder la même précision que Lighter
    tick_size = Decimal('0.00001') if token == 'BTC' else Decimal('0.0001')
    # Arrondir au multiple de tick_size le plus proche (ROUND_HALF_UP pour garder la précision)
    amount = float((amount_decimal / tick_size).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * tick_size)
    
    logger.info(f"📏 Quantité originale: {paradex_config.get('amount')}, Quantité arrondie: {amount}")
    
    # Obtenir le marché pour le token
    market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
    
    # Générer un client_id unique basé sur le timestamp
    client_id = f"arbitrage_{int(datetime.now().timestamp() * 1000)}"
    
    # Déterminer OrderSide
    order_side = OrderSide.Buy if order_type.lower() == 'buy' else OrderSide.Sell
    
    logger.info("=" * 60)
    logger.info("🚀 PARADEX TRADER - EXECUTION DU TRADE")
    logger.info("=" * 60)
    logger.info(f"🌐 Environnement: PROD (mainnet)")
    logger.info(f"🪙 Token: {token}")
    logger.info(f"📊 Market: {market}")
    logger.info(f"💰 Taille ordre: {amount} {token}")
    logger.info(f"⚡ Levier: {leverage}x")
    logger.info(f"📈 Type d'ordre: {order_type.upper()} ({'Achat/Long' if order_side == OrderSide.Buy else 'Vente/Short'})")
    logger.info(f"🆔 Client ID: {client_id}")
    logger.info("=" * 60)
    
    # Initialisation du client Paradex
    logger.info("🔧 Initialisation du client Paradex...")
    try:
        paradex = Paradex(
            env='prod',
            l2_private_key=L2_PRIVATE_KEY
        )
        
        paradex.init_account(
            l1_address=L1_ADDRESS,
            l2_private_key=L2_PRIVATE_KEY
        )
        logger.info("✅ Client Paradex initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation client: {e}")
        raise
    
    try:
        # 1. Mise à jour du levier AVANT de placer l'ordre
        logger.info(f"\n📈 Configuration du levier à {leverage}x...")
        logger.warning(f"   ⚠️ ATTENTION: Paradex gère le levier au niveau du compte, pas de l'ordre")
        logger.warning(f"   ⚠️ Le levier configuré ({leverage}x) peut ne pas être appliqué si le compte a un levier différent")
        logger.warning(f"   ⚠️ Vérifiez manuellement le levier du compte Paradex avant de trader")
        logger.info(f"   📊 Levier souhaité: {leverage}x")
        
        # 2. Récupérer les informations du compte (optionnel, pour vérification)
        logger.info("\n📊 Récupération des informations du compte...")
        try:
            account_info = paradex.api_client.fetch_account_summary()
            logger.info(f"✅ Informations du compte récupérées: {account_info}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer les infos du compte: {e}")
        
        # 3. Créer l'ordre avec le levier spécifié
        logger.info(f"\n📝 Création de l'ordre market...")
        logger.info(f"   📊 Market: {market}")
        logger.info(f"   🆔 Client ID: {client_id}")
        logger.info(f"   💰 Size: {amount} {token}")
        logger.info(f"   📈 Side: {order_type.upper()}")
        
        try:
            # Créer l'ordre avec le levier spécifié
            # Note: Paradex peut nécessiter de passer le levier dans l'ordre ou via une méthode séparée
            # Vérifier la documentation de paradex_py pour la méthode exacte
            order = Order(
                market=market,
                order_type=OrderType.Market,
                order_side=order_side,
                size=Decimal(str(amount)),
                client_id=client_id,
                instruction="IOC",  # Immediate or Cancel
                reduce_only=False
            )
            
            # Si Paradex a une méthode pour mettre à jour le levier avant l'ordre, l'utiliser ici
            # Exemple (à adapter selon l'API réelle):
            # try:
            #     paradex.api_client.update_leverage(market=market, leverage=leverage)
            # except Exception as e:
            #     logger.warning(f"⚠️ Impossible de mettre à jour le levier: {e}")
            
            # Placer l'ordre
            logger.info("📤 Envoi de l'ordre...")
            result = paradex.api_client.submit_order(order=order)
            
            logger.info("✅ Ordre placé avec succès!")
            logger.info(f"   📋 Résultat: {result}")
            
            # Extraire l'ID de l'ordre depuis le résultat
            order_id = None
            if hasattr(result, 'id'):
                order_id = result.id
            elif isinstance(result, dict) and 'id' in result:
                order_id = result['id']
            elif isinstance(result, str) and "'id':" in result:
                # Parser l'ID depuis la string
                import re
                match = re.search(r"'id':\s*'([^']+)'", result)
                if match:
                    order_id = match.group(1)
            
            # Vérification complète avec le module dédié
            logger.info("\n🔍 Vérification complète de l'exécution...")
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from trade_verification import TradeVerification
            
            verifier = TradeVerification()
            verification_result = await verifier.verify_paradex_trade(
                token=token,
                expected_amount=amount,
                order_type=order_type,
                leverage=leverage,
                order_id=order_id,
                paradex_client=paradex
            )
            
            order_executed = verification_result.get("executed", False)
            execution_status = "verified" if order_executed else "not_executed"
            
            # Vérifier le risque de liquidation si position trouvée
            if verification_result.get("position_found"):
                liquidation_price = verification_result.get("liquidation_price")
                market_price = paradex_config.get('market_price')
                if liquidation_price and market_price:
                    is_risky, risk_msg = verifier.check_liquidation_risk(
                        liquidation_price,
                        market_price,
                        token
                    )
                    logger.info(f"\n{risk_msg}")
                
                # Vérifier le health factor
                health_factor = verification_result.get("health_factor")
                if health_factor:
                    is_healthy, health_msg = verifier.check_health_factor(health_factor)
                    logger.info(f"{health_msg}")
            
            return {
                "success": True,
                "result": str(result),
                "order_id": order_id,
                "token": token,
                "amount": amount,
                "leverage": leverage,
                "order_type": order_type,
                "market": market,
                "order_executed": order_executed,
                "execution_status": execution_status,
                "verification": verification_result
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du placement de l'ordre: {e}")
            logger.error(f"🔍 Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"🔍 Traceback complet:\n{traceback.format_exc()}")
            raise
    
    except Exception as e:
        logger.error(f"❌ Erreur fatale dans execute_trade: {e}")
        raise

async def main():
    """Fonction principale"""
    logger = setup_logger("paradex_trader")
    
    try:
        # Charger la configuration
        config = load_config()
        
        # Exécuter le trade
        result = await execute_trade(config)
        
        logger.info("\n🏁 Script terminé avec succès")
        logger.info(f"✅ Résultat: {result}")
        
        # Imprimer le résultat en JSON pour que le bot principal puisse le parser
        import json
        print("\n" + "=" * 60)
        print("RESULT_JSON_START")
        print(json.dumps(result, default=str))
        print("RESULT_JSON_END")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


Trader Paradex configurable - Lit la configuration depuis trading_config.json
"""

import asyncio
import json
import os
import sys
import re
from datetime import datetime
from paradex_py import Paradex
from paradex_py.common.order import Order, OrderSide, OrderType
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import du système de logs
from logger import setup_logger

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
L1_ADDRESS = "0x19bF8d22f9772b1F349a803e5B640087f3d29C2a"

# Mapping des tokens vers les marchés Paradex
TOKEN_MARKET = {
    "BTC": "BTC-USD-PERP",
    "ETH": "ETH-USD-PERP",
    "SOL": "SOL-USD-PERP",
    "USDC": "USDC-USD-PERP"
}

def load_config():
    """Charger la configuration depuis trading_config.json"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Erreur lecture config: {e}")
    else:
        raise Exception(f"Fichier de configuration non trouvé: {config_file}")

async def execute_trade(config_data):
    """Exécute un trade sur Paradex selon la configuration"""
    logger = setup_logger("paradex_trader")
    
    paradex_config = config_data.get('paradex', {})
    if not paradex_config:
        raise Exception("Configuration Paradex non trouvée dans trading_config.json")
    
    token = paradex_config.get('token', 'ETH')
    amount = float(paradex_config.get('amount', 0.03))
    leverage = int(paradex_config.get('leverage', 50))
    order_type = paradex_config.get('order_type', 'buy')
    
    # Paradex accepte une précision de 0.00001 (5 décimales) pour BTC
    # Utiliser Decimal pour éviter les problèmes de précision flottante
    amount_decimal = Decimal(str(amount))
    # Utiliser 0.00001 pour BTC afin de garder la même précision que Lighter
    tick_size = Decimal('0.00001') if token == 'BTC' else Decimal('0.0001')
    # Arrondir au multiple de tick_size le plus proche (ROUND_HALF_UP pour garder la précision)
    amount = float((amount_decimal / tick_size).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * tick_size)
    
    logger.info(f"📏 Quantité originale: {paradex_config.get('amount')}, Quantité arrondie: {amount}")
    
    # Obtenir le marché pour le token
    market = TOKEN_MARKET.get(token, f"{token}-USD-PERP")
    
    # Générer un client_id unique basé sur le timestamp
    client_id = f"arbitrage_{int(datetime.now().timestamp() * 1000)}"
    
    # Déterminer OrderSide
    order_side = OrderSide.Buy if order_type.lower() == 'buy' else OrderSide.Sell
    
    logger.info("=" * 60)
    logger.info("🚀 PARADEX TRADER - EXECUTION DU TRADE")
    logger.info("=" * 60)
    logger.info(f"🌐 Environnement: PROD (mainnet)")
    logger.info(f"🪙 Token: {token}")
    logger.info(f"📊 Market: {market}")
    logger.info(f"💰 Taille ordre: {amount} {token}")
    logger.info(f"⚡ Levier: {leverage}x")
    logger.info(f"📈 Type d'ordre: {order_type.upper()} ({'Achat/Long' if order_side == OrderSide.Buy else 'Vente/Short'})")
    logger.info(f"🆔 Client ID: {client_id}")
    logger.info("=" * 60)
    
    # Initialisation du client Paradex
    logger.info("🔧 Initialisation du client Paradex...")
    try:
        paradex = Paradex(
            env='prod',
            l2_private_key=L2_PRIVATE_KEY
        )
        
        paradex.init_account(
            l1_address=L1_ADDRESS,
            l2_private_key=L2_PRIVATE_KEY
        )
        logger.info("✅ Client Paradex initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation client: {e}")
        raise
    
    try:
        # 1. Mise à jour du levier AVANT de placer l'ordre
        logger.info(f"\n📈 Configuration du levier à {leverage}x...")
        logger.warning(f"   ⚠️ ATTENTION: Paradex gère le levier au niveau du compte, pas de l'ordre")
        logger.warning(f"   ⚠️ Le levier configuré ({leverage}x) peut ne pas être appliqué si le compte a un levier différent")
        logger.warning(f"   ⚠️ Vérifiez manuellement le levier du compte Paradex avant de trader")
        logger.info(f"   📊 Levier souhaité: {leverage}x")
        
        # 2. Récupérer les informations du compte (optionnel, pour vérification)
        logger.info("\n📊 Récupération des informations du compte...")
        try:
            account_info = paradex.api_client.fetch_account_summary()
            logger.info(f"✅ Informations du compte récupérées: {account_info}")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer les infos du compte: {e}")
        
        # 3. Créer l'ordre avec le levier spécifié
        logger.info(f"\n📝 Création de l'ordre market...")
        logger.info(f"   📊 Market: {market}")
        logger.info(f"   🆔 Client ID: {client_id}")
        logger.info(f"   💰 Size: {amount} {token}")
        logger.info(f"   📈 Side: {order_type.upper()}")
        
        try:
            # Créer l'ordre avec le levier spécifié
            # Note: Paradex peut nécessiter de passer le levier dans l'ordre ou via une méthode séparée
            # Vérifier la documentation de paradex_py pour la méthode exacte
            order = Order(
                market=market,
                order_type=OrderType.Market,
                order_side=order_side,
                size=Decimal(str(amount)),
                client_id=client_id,
                instruction="IOC",  # Immediate or Cancel
                reduce_only=False
            )
            
            # Si Paradex a une méthode pour mettre à jour le levier avant l'ordre, l'utiliser ici
            # Exemple (à adapter selon l'API réelle):
            # try:
            #     paradex.api_client.update_leverage(market=market, leverage=leverage)
            # except Exception as e:
            #     logger.warning(f"⚠️ Impossible de mettre à jour le levier: {e}")
            
            # Placer l'ordre
            logger.info("📤 Envoi de l'ordre...")
            result = paradex.api_client.submit_order(order=order)
            
            logger.info("✅ Ordre placé avec succès!")
            logger.info(f"   📋 Résultat: {result}")
            
            # Extraire l'ID de l'ordre depuis le résultat
            order_id = None
            if hasattr(result, 'id'):
                order_id = result.id
            elif isinstance(result, dict) and 'id' in result:
                order_id = result['id']
            elif isinstance(result, str) and "'id':" in result:
                # Parser l'ID depuis la string
                import re
                match = re.search(r"'id':\s*'([^']+)'", result)
                if match:
                    order_id = match.group(1)
            
            # Vérification complète avec le module dédié
            logger.info("\n🔍 Vérification complète de l'exécution...")
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from trade_verification import TradeVerification
            
            verifier = TradeVerification()
            verification_result = await verifier.verify_paradex_trade(
                token=token,
                expected_amount=amount,
                order_type=order_type,
                leverage=leverage,
                order_id=order_id,
                paradex_client=paradex
            )
            
            order_executed = verification_result.get("executed", False)
            execution_status = "verified" if order_executed else "not_executed"
            
            # Vérifier le risque de liquidation si position trouvée
            if verification_result.get("position_found"):
                liquidation_price = verification_result.get("liquidation_price")
                market_price = paradex_config.get('market_price')
                if liquidation_price and market_price:
                    is_risky, risk_msg = verifier.check_liquidation_risk(
                        liquidation_price,
                        market_price,
                        token
                    )
                    logger.info(f"\n{risk_msg}")
                
                # Vérifier le health factor
                health_factor = verification_result.get("health_factor")
                if health_factor:
                    is_healthy, health_msg = verifier.check_health_factor(health_factor)
                    logger.info(f"{health_msg}")
            
            return {
                "success": True,
                "result": str(result),
                "order_id": order_id,
                "token": token,
                "amount": amount,
                "leverage": leverage,
                "order_type": order_type,
                "market": market,
                "order_executed": order_executed,
                "execution_status": execution_status,
                "verification": verification_result
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du placement de l'ordre: {e}")
            logger.error(f"🔍 Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"🔍 Traceback complet:\n{traceback.format_exc()}")
            raise
    
    except Exception as e:
        logger.error(f"❌ Erreur fatale dans execute_trade: {e}")
        raise

async def main():
    """Fonction principale"""
    logger = setup_logger("paradex_trader")
    
    try:
        # Charger la configuration
        config = load_config()
        
        # Exécuter le trade
        result = await execute_trade(config)
        
        logger.info("\n🏁 Script terminé avec succès")
        logger.info(f"✅ Résultat: {result}")
        
        # Imprimer le résultat en JSON pour que le bot principal puisse le parser
        import json
        print("\n" + "=" * 60)
        print("RESULT_JSON_START")
        print(json.dumps(result, default=str))
        print("RESULT_JSON_END")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

