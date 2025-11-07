#!/usr/bin/env python3
"""
Test du binaire signer Lighter
"""

import sys
import os

# Ajouter le chemin du SDK Lighter
sys.path.insert(0, '/Users/baptistecuchet/Library/Python/3.9/lib/python/site-packages')

try:
    from lighter import SignerClient
    print("✅ Import SignerClient réussi")
    
    # Test d'initialisation simple
    client = SignerClient(
        url="https://mainnet.zklighter.elliot.ai",
        private_key="b8c7b83cb9b36181bf40f74e59c78d9420df8e3d9d7e17d60e1effcf42807a7f6dbbb9021bcc5344",
        account_index=2,
        api_key_index=0
    )
    print("✅ Client initialisé")
    
    # Test d'une méthode simple
    print("🔍 Test du binaire signer...")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
