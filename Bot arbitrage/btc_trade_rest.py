#!/usr/bin/env python3
"""
Script de trading BTC avec API REST directe (contournement du bug SDK)
"""

import asyncio
import aiohttp
import json
import time
from config import Config

async def execute_btc_trade_rest():
    """Exécute le trade BTC avec API REST directe"""
    print("🚀 TRADE BTC AUTOMATIQUE (API REST)")
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
        
        # Utiliser l'API REST directement
        async with aiohttp.ClientSession() as session:
            # 1. Récupérer le nonce
            nonce_url = f"{lighter_config['api_url']}/api/v1/nextNonce"
            params = {"account_index": 2, "api_key_index": 0}
            
            async with session.get(nonce_url, params=params) as resp:
                if resp.status != 200:
                    print(f"❌ Erreur nonce: {resp.status}")
                    return False
                nonce_data = await resp.json()
                nonce = nonce_data.get("nonce", 0)
                print(f"✅ Nonce récupéré: {nonce}")
            
            # 2. Créer l'ordre via API REST
            order_url = f"{lighter_config['api_url']}/api/v1/orders"
            
            order_payload = {
                "market_index": 1,
                "client_order_index": int(time.time() * 1000) % 1000000,
                "base_amount": size_units,
                "price": 0,  # Market order
                "is_ask": False,  # Buy
                "order_type": 1,  # Market
                "time_in_force": 0,  # IOC
                "reduce_only": False,
                "trigger_price": 0,
                "order_expiry": -1
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {lighter_config['private_key']}"
            }
            
            print(f"📝 Placement de l'ordre via API REST...")
            print(f"   URL: {order_url}")
            print(f"   Payload: {order_payload}")
            
            async with session.post(order_url, json=order_payload, headers=headers) as resp:
                print(f"📊 Réponse HTTP: {resp.status}")
                
                if resp.status == 200:
                    result = await resp.json()
                    print("✅ Ordre placé avec succès!")
                    print(f"📋 Résultat: {result}")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Erreur API: {resp.status}")
                    print(f"📋 Détails: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erreur lors du trade: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale"""
    print("🤖 BOT DE TRADING BTC (API REST)")
    print("⚠️  Contournement du bug SDK")
    print()
    
    success = await execute_btc_trade_rest()
    
    if success:
        print("\n🎉 Trade exécuté avec succès!")
    else:
        print("\n💥 Échec du trade")
    
    print("\n🏁 Script terminé")

if __name__ == "__main__":
    asyncio.run(main())
