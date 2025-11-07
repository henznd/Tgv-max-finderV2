#!/usr/bin/env python3
"""
Test simple d'authentification Lighter
"""

import asyncio
from config import Config
from auth import LighterAuthenticator

async def test_auth_only():
    """Test seulement l'authentification"""
    print("🔐 TEST AUTHENTIFICATION SEULE")
    print("=" * 40)
    
    try:
        # Configuration
        config = Config()
        if not config.validate_lighter_config():
            print("❌ Configuration Lighter incomplète")
            return False
        
        lighter_config = config.get_lighter_config()
        
        # Créer l'authentificateur
        print("🔧 Initialisation de l'authentificateur...")
        authenticator = LighterAuthenticator(
            api_url=lighter_config['api_url'],
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address']
        )
        
        # Test d'authentification
        print("🔐 Test d'authentification...")
        if authenticator.authenticate():
            print("✅ Authentification réussie !")
            print("✅ Le compte est reconnu par Lighter")
            return True
        else:
            print("❌ Échec de l'authentification")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_auth_only())
