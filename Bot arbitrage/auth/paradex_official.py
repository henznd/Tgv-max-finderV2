#!/usr/bin/env python3
"""
Script Paradex avec le SDK officiel paradex-py
Utilise Python 3.11 et le SDK officiel
"""

import asyncio
from paradex_py import ParadexSubkey
from paradex_py.environment import Environment
from paradex_py.api.models import Order, OrderSide, OrderType

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
MARKET = "BTC-USD-PERP"
SIZE_BTC = 0.0001
LEVERAGE = 10

async def main():
    """Script principal Paradex avec SDK officiel"""
    print("🚀 SCRIPT PARADEX - TRADING BTC (SDK OFFICIEL)")
    print("=" * 60)
    print(f"📡 L2 Address: {L2_ADDRESS}")
    print(f"📊 Market: {MARKET}")
    print(f"💰 Taille: {SIZE_BTC} BTC")
    print(f"⚡ Levier: {LEVERAGE}x")
    print("=" * 60)
    
    try:
        # Initialisation avec le SDK officiel
        print("🔧 Initialisation du SDK Paradex...")
        paradex = ParadexSubkey(
            env=Environment.TESTNET,  # Utilise TESTNET pour les tests
            l2_private_key=L2_PRIVATE_KEY,
            l2_address=L2_ADDRESS
        )
        
        # Initialisation du compte
        print("🔐 Initialisation du compte...")
        await paradex.init_account()
        print("✅ Compte initialisé avec succès")
        
        # Récupérer les marchés disponibles
        print("📊 Récupération des marchés...")
        markets = await paradex.api_client.get_markets()
        print(f"✅ {len(markets)} marchés disponibles")
        
        # Récupérer le solde
        print("💰 Récupération du solde...")
        balance = await paradex.api_client.get_balance()
        print(f"✅ Solde: {balance}")
        
        # Configuration du levier
        print(f"📈 Configuration du levier {LEVERAGE}x...")
        # Note: Le SDK gère automatiquement le levier
        
        # Création de l'ordre
        print("📝 Création de l'ordre...")
        order = Order(
            market=MARKET,
            side=OrderSide.BUY,
            size=str(SIZE_BTC),  # Convertir en string
            order_type=OrderType.MARKET
        )
        
        print(f"📋 Ordre créé:")
        print(f"   📊 Market: {order.market}")
        print(f"   📈 Side: {order.side}")
        print(f"   💰 Size: {order.size}")
        print(f"   🎯 Type: {order.order_type}")
        
        # Placement de l'ordre
        print("🚀 Placement de l'ordre...")
        result = await paradex.api_client.submit_order(order)
        print(f"✅ Ordre placé avec succès!")
        print(f"📋 Résultat: {result}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fermeture du client
        try:
            await paradex.close()
            print("🔚 Client fermé")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
