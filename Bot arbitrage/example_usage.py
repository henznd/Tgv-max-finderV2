"""
Exemple d'utilisation du bot de trading DEX
Montre comment utiliser l'authentification et placer des ordres
"""

from trading_bot import TradingBot
from auth import LighterAuthenticator
from config import Config


def example_lighter_trading():
    """Exemple de trading avec Lighter"""
    print("🔵 Exemple de trading avec Lighter DEX")
    print("=" * 50)
    
    # Configuration
    config = Config()
    lighter_config = config.get_lighter_config()
    
    # Créer l'authentificateur
    auth = LighterAuthenticator(
        api_url=lighter_config['api_url'],
        private_key=lighter_config['private_key'],
        wallet_address=lighter_config['wallet_address']
    )
    
    # Authentification
    if not auth.authenticate():
        print("❌ Échec de l'authentification")
        return
    
    print("✅ Authentifié avec succès")
    
    # Récupérer les marchés
    markets = auth.get_markets()
    print(f"📊 {len(markets)} marchés disponibles")
    
    # Récupérer le solde
    balance = auth.get_balance()
    print(f"💰 Solde: {balance}")
    
    # Exemple d'ordre limit buy
    order_data = {
        "type": "limit",
        "side": "buy",
        "symbol": "ETH-USDC",
        "price": 1500.0,
        "size": 0.1,
        "time_in_force": "GTC",
        "reduce_only": False,
        "post_only": False
    }
    
    print("📝 Placement d'un ordre...")
    result = auth.place_order(order_data)
    print(f"📊 Résultat: {result}")
    
    # Récupérer les ordres
    orders = auth.get_orders()
    print(f"📋 {len(orders)} ordre(s) actif(s)")


def example_signature_verification():
    """Exemple de vérification de signature"""
    print("\n🔐 Exemple de vérification de signature")
    print("=" * 50)
    
    from auth.signature_manager import SignatureManager
    
    # Configuration (utilisez vos vraies clés)
    private_key = "your_private_key_here"
    wallet_address = "your_wallet_address_here"
    
    # Créer le gestionnaire de signatures
    sig_manager = SignatureManager(private_key, wallet_address)
    
    # Exemple de message à signer
    message = "Hello, Lighter DEX!"
    
    # Signer le message
    signature = sig_manager.sign_message(message)
    print(f"📝 Message: {message}")
    print(f"🔑 Signature: {signature}")
    
    # Vérifier la signature
    is_valid = sig_manager.verify_signature(message, signature, wallet_address)
    print(f"✅ Signature valide: {is_valid}")
    
    # Informations du wallet
    wallet_info = sig_manager.get_wallet_info()
    print(f"📍 Adresse: {wallet_info['address']}")


def example_structured_data_signing():
    """Exemple de signature de données structurées (EIP-712)"""
    print("\n📋 Exemple de signature EIP-712")
    print("=" * 50)
    
    from auth.signature_manager import SignatureManager
    
    # Configuration
    private_key = "your_private_key_here"
    wallet_address = "your_wallet_address_here"
    
    sig_manager = SignatureManager(private_key, wallet_address)
    
    # Données EIP-712 pour un ordre
    domain = {
        "name": "Lighter DEX",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0x..."
    }
    
    types = {
        "Order": [
            {"name": "wallet", "type": "address"},
            {"name": "side", "type": "string"},
            {"name": "symbol", "type": "string"},
            {"name": "price", "type": "uint256"},
            {"name": "size", "type": "uint256"},
            {"name": "timestamp", "type": "uint256"}
        ]
    }
    
    message = {
        "wallet": wallet_address,
        "side": "buy",
        "symbol": "ETH-USDC",
        "price": 1500000000000000000000,  # 1500 USDC en wei
        "size": 100000000000000000,       # 0.1 ETH en wei
        "timestamp": 1234567890
    }
    
    # Signer les données structurées
    signature = sig_manager.sign_structured_data(
        domain=domain,
        types=types,
        primary_type="Order",
        message=message
    )
    
    print(f"📝 Données signées: {message}")
    print(f"🔑 Signature EIP-712: {signature}")


if __name__ == "__main__":
    print("🤖 Exemples d'utilisation du bot de trading DEX")
    print("=" * 60)
    
    # Exemple 1: Trading avec Lighter
    try:
        example_lighter_trading()
    except Exception as e:
        print(f"❌ Erreur dans l'exemple Lighter: {e}")
    
    # Exemple 2: Vérification de signature
    try:
        example_signature_verification()
    except Exception as e:
        print(f"❌ Erreur dans l'exemple de signature: {e}")
    
    # Exemple 3: Signature EIP-712
    try:
        example_structured_data_signing()
    except Exception as e:
        print(f"❌ Erreur dans l'exemple EIP-712: {e}")
    
    print("\n✅ Tous les exemples terminés")
