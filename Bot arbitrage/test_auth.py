"""
Script de test pour l'authentification DEX
Teste la connexion et l'authentification avec vos vraies clés
"""

import sys
import os
from config import Config
from auth import LighterAuthenticator, SignatureManager


def test_signature_manager():
    """Test du gestionnaire de signatures"""
    print("🔐 Test du gestionnaire de signatures")
    print("-" * 40)
    
    try:
        config = Config()
        lighter_config = config.get_lighter_config()
        
        # Créer le gestionnaire de signatures
        sig_manager = SignatureManager(
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address']
        )
        
        print(f"✅ Gestionnaire de signatures créé")
        print(f"📍 Adresse: {sig_manager.wallet_address}")
        
        # Test de signature
        test_message = "Test message for Lighter DEX"
        signature = sig_manager.sign_message(test_message)
        print(f"📝 Message: {test_message}")
        print(f"🔑 Signature: {signature[:20]}...")
        
        # Test de vérification
        is_valid = sig_manager.verify_signature(test_message, signature, sig_manager.wallet_address)
        print(f"✅ Signature valide: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test de signature: {e}")
        return False


def test_lighter_connection():
    """Test de connexion avec Lighter"""
    print("\n🔗 Test de connexion Lighter")
    print("-" * 40)
    
    try:
        config = Config()
        lighter_config = config.get_lighter_config()
        
        # Créer l'authentificateur
        auth = LighterAuthenticator(
            api_url=lighter_config['api_url'],
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address']
        )
        
        print(f"✅ Authentificateur Lighter créé")
        print(f"🌐 API URL: {lighter_config['api_url']}")
        
        # Test d'authentification
        print("🔐 Tentative d'authentification...")
        auth_result = auth.authenticate()
        
        if auth_result:
            print("✅ Authentification réussie !")
            
            # Test de récupération des marchés
            print("📊 Récupération des marchés...")
            markets = auth.get_markets()
            print(f"📈 {len(markets)} marchés disponibles")
            
            # Test de récupération du solde
            print("💰 Récupération du solde...")
            balance = auth.get_balance()
            print(f"💵 Solde: {balance}")
            
            return True
        else:
            print("❌ Échec de l'authentification")
            return False
            
    except Exception as e:
        print(f"❌ Erreur dans le test de connexion: {e}")
        return False


def test_order_creation():
    """Test de création d'ordre (simulation)"""
    print("\n📝 Test de création d'ordre")
    print("-" * 40)
    
    try:
        config = Config()
        lighter_config = config.get_lighter_config()
        
        auth = LighterAuthenticator(
            api_url=lighter_config['api_url'],
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address']
        )
        
        # Authentification d'abord
        if not auth.authenticate():
            print("❌ Authentification requise")
            return False
        
        # Ordre de test (très petit montant)
        test_order = {
            "type": "limit",
            "side": "buy",
            "symbol": "ETH-USDC",
            "price": 1500.0,
            "size": 0.001,  # 0.001 ETH
            "time_in_force": "GTC",
            "reduce_only": False,
            "post_only": True,  # Ne sera pas exécuté immédiatement
            "test_mode": True
        }
        
        print("📋 Création d'un ordre de test...")
        print(f"📊 Ordre: {test_order}")
        
        result = auth.place_order(test_order)
        print(f"📤 Résultat: {result}")
        
        if 'error' not in result:
            print("✅ Ordre créé avec succès")
            return True
        else:
            print(f"⚠️ Erreur dans la création d'ordre: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur dans le test d'ordre: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🧪 Tests d'authentification DEX")
    print("=" * 50)
    
    # Vérifier la configuration
    config = Config()
    if not config.validate_lighter_config():
        print("❌ Configuration incomplète")
        print("Vérifiez vos variables d'environnement dans .env")
        return
    
    print("✅ Configuration validée")
    
    # Tests
    tests = [
        ("Signature Manager", test_signature_manager),
        ("Connexion Lighter", test_lighter_connection),
        ("Création d'ordre", test_order_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Résultat: {passed}/{len(results)} tests réussis")
    
    if passed == len(results):
        print("🎉 Tous les tests sont passés ! Le bot est prêt.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")


if __name__ == "__main__":
    main()
