#!/usr/bin/env python3
"""
Test exact selon la documentation Paradex
"""

import asyncio
from paradex_py import Paradex
from paradex_py.environment import Environment

# ========== CONFIGURATION ==========
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"

async def test_paradex_auth():
    """Test exact selon la doc Paradex"""
    print("🚀 TEST PARADEX - EXACTEMENT SELON LA DOC")
    print("=" * 50)
    print(f"📡 L2 Address: {L2_ADDRESS}")
    print(f"🔑 Private Key: {L2_PRIVATE_KEY[:10]}...")
    print("=" * 50)
    
    try:
        # Code exact de la documentation
        print("🔧 Initialisation selon la doc...")
        paradex = Paradex(env='prod')  # prod pour mainnet
        
        print("🔐 init_account selon la doc...")
        paradex.init_account(
            l1_address="VOTRE_ADRESSE_L1",  # Selon la doc
            l2_private_key=L2_PRIVATE_KEY
        )
        
        print("✅ Authentification réussie !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_paradex_auth())
