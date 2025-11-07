#!/usr/bin/env python3
"""
Script de trading BTC automatique avec récupération dynamique des paramètres
"""

import asyncio
import aiohttp
import time
from config import Config
from auth import LighterAuthenticator

async def get_account_info(api_url: str, l1_address: str):
    """Récupère l'index de compte depuis l'API Lighter"""
    print(f"🔍 Récupération de l'index de compte pour l'adresse L1: {l1_address}")
    
    try:
        async with aiohttp.ClientSession() as session:
            accounts_url = f"{api_url}/api/v1/accountsByL1Address"
            params = {"l1_address": l1_address}
            
            async with session.get(accounts_url, params=params) as resp:
                if resp.status == 200:
                    accounts_data = await resp.json()
                    print(f"✅ Comptes trouvés: {accounts_data}")
                    
                    if "sub_accounts" in accounts_data and len(accounts_data["sub_accounts"]) > 0:
                        sub_accounts = accounts_data["sub_accounts"]
                        print(f"📋 {len(sub_accounts)} sous-compte(s) trouvé(s):")
                        
                        for i, account in enumerate(sub_accounts):
                            print(f"   Compte {i+1}: index={account.get('index')}, type={account.get('account_type')}")
                        
                        # Prendre le premier compte
                        account_index = sub_accounts[0].get('index')
                        print(f"✅ Index de compte sélectionné: {account_index}")
                        return account_index
                    else:
                        print("❌ Aucun sous-compte trouvé")
                        return None
                else:
                    print(f"❌ Erreur récupération comptes: {resp.status}")
                    error_text = await resp.text()
                    print(f"📋 Détails: {error_text}")
                    return None
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        return None

async def execute_btc_trade():
    """Exécute le trade BTC automatiquement"""
    print("🚀 TRADE BTC AUTOMATIQUE")
    print("=" * 40)
    print("💰 Montant: $10")
    print("⚡ Levier: 10x")
    print("📊 Side: BUY")
    print("=" * 40)
    
    try:
        # Configuration depuis .env
        config = Config()
        if not config.validate_lighter_config():
            print("❌ Configuration Lighter incomplète")
            return False
        
        lighter_config = config.get_lighter_config()
        
        # Récupérer l'index de compte dynamiquement
        l1_address = "0x19bF8d22f9772b1F349a803e5B640087f3d29C2a"  # Adresse L1
        account_index = await get_account_info(lighter_config['api_url'], l1_address)
        
        if not account_index:
            print("❌ Impossible de récupérer l'index de compte")
            return False
        
        # Initialisation authentificateur avec les paramètres du .env
        print("🔧 Initialisation de l'authentificateur...")
        print(f"   📡 API URL: {lighter_config['api_url']}")
        print(f"   🔑 API Key Index: {lighter_config['api_key_index']}")
        print(f"   👤 Account Index: {account_index}")
        
        authenticator = LighterAuthenticator(
            api_url=lighter_config['api_url'],
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address'],
            account_index=account_index,
            api_key_index=lighter_config['api_key_index']
        )

        # Authentification
        print("🔐 Authentification...")
        is_auth = await authenticator.authenticate() \
            if asyncio.iscoroutinefunction(authenticator.authenticate) \
            else authenticator.authenticate()
        if not is_auth:
            print("❌ Échec de l'authentification")
            return False
        
        print("✅ Authentifié avec succès")
        
        # Paramètres du trade - Ordre limite à $50,000
        btc_price = 50000.0  # Prix limite fixe
        amount_usd = 10.0
        leverage = 10
        btc_size = (amount_usd * leverage) / btc_price
        size_units = int(btc_size * 1e8)  # Convertir en satoshis
        
        print(f"📊 Calcul de position:")
        print(f"   💵 Montant initial: ${amount_usd}")
        print(f"   ⚡ Levier: {leverage}x")
        print(f"   💰 Montant avec levier: ${amount_usd * leverage:,.2f}")
        print(f"   ₿ Taille BTC: {btc_size:.6f} BTC")
        print(f"   💲 Prix limite: ${btc_price:,.2f}")

        # Créer l'ordre limite avec les paramètres directs
        order_data = {
            "market_index": 1,            # Index BTC/USDC
            "client_order_index": int(time.time() * 1000) % 1000000,  # ID unique
            "base_amount": size_units,    # IMPORTANT : unité entière
            "price": int(btc_price * 100),  # Prix limite en centimes
            "is_ask": False,  # Buy
        }
        
        print(f"📝 Ordre BTC:")
        print(f"   📈 Type: limit")
        print(f"   📊 Side: buy")
        print(f"   💰 Taille: {btc_size:.6f} BTC ({size_units} unités)")
        print(f"   💲 Prix limite: ${btc_price:,.2f} ({int(btc_price * 100)} centimes)")
        print(f"   ⚡ Levier: {leverage}x")
        print(f"   💵 Valeur: ${amount_usd * leverage:,.2f}")
        
        # Placer l'ordre
        print("🚀 Placement de l'ordre...")
        result = await authenticator.place_order(order_data)

        print("\n📊 RÉSULTAT:")
        print("=" * 20)
        # Gestion propre du retour
        if isinstance(result, dict) and "error" in result:
            print(f"❌ Erreur: {result['error']}")
            return False
        elif result is None:
            print(f"❌ Erreur inconnue, aucun retour de l'API !")
            return False
        else:
            print("✅ Ordre placé avec succès!")
            print(f"📋 Détails: {result}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du trade: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale"""
    print("🤖 BOT DE TRADING BTC (AUTO)")
    print("⚠️  Récupération dynamique des paramètres")
    print()
    
    success = await execute_btc_trade()
    
    if success:
        print("\n🎉 Trade exécuté avec succès!")
    else:
        print("\n💥 Échec du trade")
    
    print("\n🏁 Script terminé")

if __name__ == "__main__":
    asyncio.run(main())