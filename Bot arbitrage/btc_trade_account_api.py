#!/usr/bin/env python3
"""
Script de trading BTC avec AccountApi (contournement du bug SDK)
"""

import asyncio
from config import Config
from lighter import ApiClient, Configuration, AccountApi

async def execute_btc_trade_account_api():
    """Exécute le trade BTC avec AccountApi"""
    print("🚀 TRADE BTC AUTOMATIQUE (AccountApi)")
    print("=" * 40)
    print("💰 Montant: $10")
    print("⚡ Levier: 10x")
    print("📊 Side: BUY")
    print("=" * 40)
    
    try:
        # Configuration
        config = Config()
        if not config.validate_lighter_config():
            print("❌ Configuration Lighter incomplète")
            return False
        
        lighter_config = config.get_lighter_config()
        
        # Paramètres du trade
        amount_usd = 10.0
        leverage = 10
        btc_price = 45000.0
        btc_size = (amount_usd * leverage) / btc_price
        size_units = int(btc_size * 1e8)  # Convertir en satoshis
        
        print(f"📊 Calcul de position:")
        print(f"   💵 Montant initial: ${amount_usd}")
        print(f"   ⚡ Levier: {leverage}x")
        print(f"   💰 Montant avec levier: ${amount_usd * leverage:,.2f}")
        print(f"   ₿ Taille BTC: {btc_size:.6f} BTC")
        print(f"   💲 Prix BTC: ${btc_price:,.2f}")
        
        # Utiliser AccountApi
        print("🔧 Initialisation de l'AccountApi...")
        api_client = ApiClient(configuration=Configuration(host=lighter_config['api_url']))
        account_api = AccountApi(api_client)
        
        # Vérifier le compte d'abord
        print("🔍 Vérification du compte...")
        try:
            account_info = await account_api.account(account_index=2)
            print(f"✅ Compte trouvé: {account_info}")
        except Exception as e:
            print(f"❌ Erreur compte: {e}")
            return False
        
        # Essayer de placer l'ordre via AccountApi
        print("📝 Tentative de placement d'ordre via AccountApi...")
        
        # Note: AccountApi n'a pas de méthode directe pour placer des ordres
        # Nous devons utiliser une approche différente
        
        print("⚠️ AccountApi ne supporte pas le placement d'ordres directement")
        print("💡 Le SDK SignerClient a un bug, nous ne pouvons pas contourner facilement")
        
        return False
                    
    except Exception as e:
        print(f"❌ Erreur lors du trade: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale"""
    print("🤖 BOT DE TRADING BTC (AccountApi)")
    print("⚠️  Test de contournement du bug SDK")
    print()
    
    success = await execute_btc_trade_account_api()
    
    if success:
        print("\n🎉 Trade exécuté avec succès!")
    else:
        print("\n💥 Échec du trade")
    
    print("\n🏁 Script terminé")

if __name__ == "__main__":
    asyncio.run(main())
