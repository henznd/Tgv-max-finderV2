#!/usr/bin/env python3
"""
Trader Lighter configurable - Lit la configuration depuis trading_config.json
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from lighter import SignerClient

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import du système de logs
from logger import setup_logger

# ========= CONFIGURATION =========
BASE_URL = "https://mainnet.zklighter.elliot.ai"
PRIVATE_KEY = "4ec938ba854c8af52f09cfb8cba30e140be4754d4980dbb86d1756a37b2ce9f8539fcbc4ae91183e"
ACCOUNT_INDEX = 116154
API_KEY_INDEX = 4

# Mapping des tokens vers market_index (vérifié avec les prix réels)
TOKEN_MARKET_INDEX = {
    "BTC": 1,  # BTC/USDC sur Lighter (prix ~$100,000)
    "ETH": 0,  # ETH/USDC sur Lighter (prix ~$3,300) - CORRIGÉ: market_id 0
    "SOL": 2,  # SOL/USDC sur Lighter (prix ~$154) - market_id 2 est SOL
    "BNB": 25,  # BNB/USDC sur Lighter
    "USDC": 0  # À adapter
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
    """Exécute un trade sur Lighter selon la configuration"""
    logger = setup_logger("lighter_trader")
    
    lighter_config = config_data.get('lighter', {})
    if not lighter_config:
        raise Exception("Configuration Lighter non trouvée dans trading_config.json")
    
    token = lighter_config.get('token', 'BTC')
    amount = float(lighter_config.get('amount', 0.00001))
    leverage = int(lighter_config.get('leverage', 10))
    order_type = lighter_config.get('order_type', 'buy')
    
    # Vérifier que le token est bien défini
    if not token:
        raise Exception("Token non défini dans la configuration Lighter")
    
    # Obtenir le market_index pour le token
    # Note: Si le token n'est pas dans le mapping, utiliser 1 (BTC) par défaut
    # Mais on devrait loguer un avertissement
    market_index = TOKEN_MARKET_INDEX.get(token)
    if market_index is None:
        logger.warning(f"⚠️ Token {token} non trouvé dans TOKEN_MARKET_INDEX, utilisation de l'index par défaut 1 (BTC)")
        market_index = 1
    else:
        logger.info(f"✅ Market index trouvé pour {token}: {market_index}")
    
    # Conversion de la quantité en unités API
    # ATTENTION: Lighter utilise des unités différentes selon les tokens
    # Pour BTC: Lighter divise par 1e5 (100,000) - CORRIGÉ: facteur 10
    # Donc pour obtenir le bon montant, on doit multiplier par 1e5
    # Pour ETH: 1 ETH = 10,000 unités (1e4)
    if token == "BTC":
        # CORRIGÉ: Lighter divise par 1e5, donc on multiplie par 1e5
        # Cela permet de garder la précision (0.00096281 * 1e5 = 96.281 → 96 unités)
        order_size_units = int(amount * 1e5)  # 1 BTC = 100,000 unités (1e5)
        logger.info(f"📏 Conversion BTC: {amount} BTC = {order_size_units} unités (précision 1e5 pour Lighter)")
    elif token == "ETH":
        # ETH utilise 1e4 (10,000 unités par ETH) sur Lighter
        order_size_units = int(amount * 1e4)  # 1 ETH = 10,000 unités
        logger.info(f"📏 Conversion ETH: {amount} ETH = {order_size_units} unités (précision 1e4)")
    else:
        # Par défaut, utiliser 1e3 pour BTC-like tokens (Lighter divise par 1e3)
        order_size_units = int(amount * 1e3)
        logger.info(f"📏 Conversion {token}: {amount} {token} = {order_size_units} unités (précision 1e3)")
    
    # Générer un client_order_index unique basé sur le timestamp
    client_order_index = int(datetime.now().timestamp() * 1000) % 2147483647
    
    # Déterminer is_ask (True = vente/short, False = achat/long)
    is_ask = (order_type.lower() == 'sell')
    
    logger.info("=" * 60)
    logger.info("🚀 LIGHTER TRADER - EXECUTION DU TRADE")
    logger.info("=" * 60)
    logger.info(f"📡 API URL: {BASE_URL}")
    logger.info(f"🔑 API Key Index: {API_KEY_INDEX}")
    logger.info(f"👤 Account Index: {ACCOUNT_INDEX}")
    logger.info(f"🪙 Token: {token}")
    logger.info(f"📊 Market Index: {market_index} (pour {token})")
    logger.info(f"💰 Taille ordre: {amount} {token} ({order_size_units} unités)")
    logger.info(f"⚡ Levier: {leverage}x")
    logger.info(f"📈 Type d'ordre: MARKET ORDER - {order_type.upper()} ({'Vente/Short' if is_ask else 'Achat/Long'})")
    logger.info(f"🆔 Client Order Index: {client_order_index}")
    logger.info("=" * 60)
    
    # Initialisation du client
    logger.info("🔧 Initialisation du client Signer...")
    try:
        client = SignerClient(BASE_URL, PRIVATE_KEY, api_key_index=API_KEY_INDEX, account_index=ACCOUNT_INDEX)
        logger.info("✅ Client Signer initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation client: {e}")
        raise
    
    try:
        # 1. Mise à jour du levier
        logger.info(f"\n📈 Mise à jour du levier à {leverage}x...")
        try:
            leverage_result = await client.update_leverage(
                market_index=market_index,
                margin_mode=0,  # 0 pour cross, 1 pour isolated
                leverage=leverage
            )
            logger.info(f"✅ Levier mis à jour: {leverage_result}")
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour levier: {e}")
            raise
        
        # 2. Placement de l'ordre market
        logger.info(f"\n📝 Placement de l'ordre MARKET (pas limit!)...")
        logger.info(f"   🪙 Token: {token}")
        logger.info(f"   📊 Market Index: {market_index} (pour {token})")
        logger.info(f"   🆔 Client Order Index: {client_order_index}")
        logger.info(f"   💰 Base Amount: {order_size_units} unités ({amount} {token})")
        logger.info(f"   📈 Side: {'Vente/Short' if is_ask else 'Achat/Long'}")
        logger.info(f"   🔄 Type: MARKET ORDER (avg_execution_price sera utilisé comme référence)")
        
        # Prix pour le market order (en centimes)
        # Récupérer le prix depuis la config si fourni, sinon utiliser un prix par défaut
        market_price = lighter_config.get('market_price')  # Prix en USD depuis l'API
        if market_price:
            # Le prix récupéré est déjà en USD, convertir en centimes (prix * 100)
            # Lighter attend le prix en centimes pour avg_execution_price
            avg_execution_price = int(float(market_price) * 100)
            logger.info(f"   💲 Prix marché réel: ${market_price:.2f} = {avg_execution_price} centimes")
            logger.info(f"   ✅ Utilisation du prix réel pour éviter le slippage")
        else:
            # Fallback: Prix approximatif par défaut (en centimes)
            logger.warning(f"   ⚠️ Prix marché non fourni, utilisation d'un prix par défaut")
            logger.warning(f"   ⚠️ RISQUE DE SLIPPAGE ÉLEVÉ")
            if token == "BTC":
                avg_execution_price = 12000000  # $120,000 * 100 centimes
            elif token == "ETH":
                avg_execution_price = 300000  # $3,000 * 100 centimes = 300,000 centimes
            else:
                avg_execution_price = 100000  # Prix par défaut
            logger.info(f"   💲 Prix par défaut: {avg_execution_price} centimes")
        
        try:
            order, tx_hash, err = await client.create_market_order(
                market_index=market_index,
                client_order_index=client_order_index,
                base_amount=order_size_units,
                avg_execution_price=avg_execution_price,
                is_ask=is_ask
            )
            
            if err is not None:
                logger.error(f"❌ Erreur lors du placement de l'ordre: {err}")
                raise Exception(f"Erreur API: {err}")
            
            if order is None or tx_hash is None:
                logger.error("❌ L'API n'a retourné aucun ordre/aucun hash")
                raise Exception("Ordre non retourné par l'API")
            
            logger.info("✅ Ordre placé avec succès!")
            logger.info(f"   📋 Ordre: {order}")
            logger.info(f"   🔗 Hash transaction: {tx_hash}")
            
            # Extraire le tx_hash réel
            tx_hash_str = str(tx_hash)
            actual_tx_hash = None
            if hasattr(tx_hash, 'tx_hash'):
                actual_tx_hash = tx_hash.tx_hash
            else:
                # Parser depuis la string
                import re
                match = re.search(r"tx_hash='([^']+)'", tx_hash_str)
                if match:
                    actual_tx_hash = match.group(1)
            
            # Vérification complète avec le module dédié
            logger.info("\n🔍 Vérification complète de l'exécution...")
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from trade_verification import TradeVerification
            
            verifier = TradeVerification()
            verification_result = await verifier.verify_lighter_trade(
                token=token,
                expected_amount=amount,
                order_type=order_type,
                leverage=leverage,
                tx_hash=actual_tx_hash
            )
            
            order_executed = verification_result.get("executed", False)
            execution_status = "verified" if order_executed else "not_executed"
            
            # Vérifier le risque de liquidation si position trouvée
            if verification_result.get("position_found"):
                liquidation_price = verification_result.get("liquidation_price")
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
                "order": str(order),
                "tx_hash": str(tx_hash),
                "token": token,
                "amount": amount,
                "leverage": leverage,
                "order_type": order_type,
                "order_executed": order_executed,
                "execution_status": execution_status,
                "verification": verification_result
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur dans create_market_order: {e}")
            logger.error(f"🔍 Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"🔍 Traceback complet:\n{traceback.format_exc()}")
            raise
    
    finally:
        # Fermeture du client
        logger.info("\n🔚 Fermeture du client...")
        try:
            await client.close()
            logger.info("✅ Client fermé")
        except Exception as e:
            logger.warning(f"⚠️ Erreur fermeture client: {e}")

async def main():
    """Fonction principale"""
    logger = setup_logger("lighter_trader")
    
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

