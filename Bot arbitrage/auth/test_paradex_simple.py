#!/usr/bin/env python3
"""
Test simple Paradex avec le SDK officiel
Selon la documentation Paradex
"""

import asyncio
from paradex_py import Paradex
from paradex_py.environment import Environment

# ========== CONFIGURATION ==========
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"

async def test_paradex_auth():
    """Test simple d'authentification Paradex avec SDK officiel"""
    print("🚀 TEST SIMPLE PARADEX - AUTHENTIFICATION")
    print("=" * 50)
    print(f"📡 L2 Address: {L2_ADDRESS}")
    print(f"🔑 Private Key: {L2_PRIVATE_KEY[:10]}...")
    print("=" * 50)
    
    try:
        # Test avec le SDK officiel selon la doc
        print("🔧 Initialisation du SDK Paradex...")
        paradex = Paradex(env=Environment.PROD)  # PROD pour mainnet
        
        print("🔐 Initialisation du compte...")
        paradex.init_account(
            l1_address="VOTRE_ADRESSE_L1",  # Placeholder selon la doc
            l2_private_key=L2_PRIVATE_KEY
        )
        
        print("🔐 Tentative d'authentification...")
        await paradex.init_account()
        print("✅ Authentification réussie !")
        
        # Test des fonctionnalités de base
        print("📊 Test des fonctionnalités...")
        
        # Récupérer les marchés
        markets = await paradex.api_client.get_markets()
        print(f"✅ {len(markets)} marchés disponibles")
        
        # Récupérer le solde
        balance = await paradex.api_client.get_balance()
        print(f"✅ Solde: {balance}")
        
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await paradex.close()
            print("🔚 Client fermé")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_paradex_auth())
