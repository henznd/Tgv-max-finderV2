"""
Script de trading BTC avec levier 10
Trade de 10$ avec levier 10x sur Bitcoin
⚠️ ATTENTION: Trading avec de l'argent réel - Risque élevé !
"""

import sys
import time
from config import Config
from auth import LighterAuthenticator


class BTCTrader:
    """Trader Bitcoin avec levier"""
    
    def __init__(self):
        """Initialise le trader BTC"""
        self.config = Config()
        self.authenticator = None
        self.authenticated = False
    
    def initialize(self) -> bool:
        """Initialise la connexion avec Lighter"""
        try:
            if not self.config.validate_lighter_config():
                print("❌ Configuration Lighter incomplète")
                return False
            
            lighter_config = self.config.get_lighter_config()
            self.authenticator = LighterAuthenticator(
                api_url=lighter_config['api_url'],
                private_key=lighter_config['private_key'],
                wallet_address=lighter_config['wallet_address']
            )
            
            print("✅ Trader BTC initialisé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authentifie le trader"""
        if not self.authenticator:
            print("❌ Authentificateur non initialisé")
            return False
        
        try:
            print("🔐 Authentification en cours...")
            self.authenticated = self.authenticator.authenticate()
            
            if self.authenticated:
                print("✅ Authentification réussie")
                print(f"📍 Wallet: {self.authenticator.get_wallet_address()}")
            else:
                print("❌ Échec de l'authentification")
            
            return self.authenticated
            
        except Exception as e:
            print(f"❌ Erreur lors de l'authentification: {e}")
            return False
    
    def get_btc_price(self) -> float:
        """Récupère le prix actuel du BTC"""
        try:
            # Prix BTC approximatif (vous pouvez utiliser une API de prix)
            # Pour l'exemple, on utilise un prix fixe
            btc_price = 45000.0  # $45,000
            print(f"💰 Prix BTC actuel: ${btc_price:,.2f}")
            return btc_price
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du prix: {e}")
            return 45000.0  # Prix par défaut
    
    def calculate_position_size(self, amount_usd: float, leverage: int, btc_price: float) -> dict:
        """Calcule la taille de position"""
        try:
            # Montant avec levier
            leveraged_amount = amount_usd * leverage
            
            # Taille de position en BTC
            btc_size = leveraged_amount / btc_price
            
            # Taille de position en USDC (pour l'ordre)
            usdc_size = leveraged_amount
            
            print(f"📊 Calcul de position:")
            print(f"   💵 Montant initial: ${amount_usd}")
            print(f"   ⚡ Levier: {leverage}x")
            print(f"   💰 Montant avec levier: ${leveraged_amount:,.2f}")
            print(f"   ₿ Taille BTC: {btc_size:.6f} BTC")
            
            return {
                "amount_usd": amount_usd,
                "leverage": leverage,
                "leveraged_amount": leveraged_amount,
                "btc_size": btc_size,
                "usdc_size": usdc_size,
                "btc_price": btc_price
            }
            
        except Exception as e:
            print(f"❌ Erreur dans le calcul: {e}")
            return {}
    
    def place_btc_order(self, position_data: dict, side: str = "buy") -> dict:
        """Place un ordre BTC"""
        try:
            if not self.authenticated:
                print("❌ Non authentifié")
                return {"error": "Non authentifié"}
            
            # Créer l'ordre BTC
            order_data = {
                "type": "market",  # Ordre au marché pour exécution immédiate
                "side": side,      # "buy" ou "sell"
                "symbol": "BTC-USDC",  # Paire BTC/USDC
                "size": position_data["btc_size"],  # Taille en BTC
                "leverage": position_data["leverage"],  # Levier
                "time_in_force": "IOC",  # Immediate or Cancel
                "reduce_only": False,
                "post_only": False
            }
            
            print(f"📝 Ordre BTC créé:")
            print(f"   📈 Type: {order_data['type']}")
            print(f"   📊 Side: {order_data['side']}")
            print(f"   💰 Taille: {order_data['size']:.6f} BTC")
            print(f"   ⚡ Levier: {order_data['leverage']}x")
            print(f"   💵 Valeur: ${position_data['leveraged_amount']:,.2f}")
            
            # Placer l'ordre
            print("🚀 Placement de l'ordre...")
            result = self.authenticator.place_order(order_data)
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur lors du placement de l'ordre: {e}")
            return {"error": str(e)}
    
    def execute_trade(self, amount_usd: float = 10.0, leverage: int = 10, side: str = "buy") -> dict:
        """Exécute le trade BTC"""
        print("🚀 EXÉCUTION DU TRADE BTC")
        print("=" * 50)
        print(f"💰 Montant: ${amount_usd}")
        print(f"⚡ Levier: {leverage}x")
        print(f"📊 Side: {side}")
        print("=" * 50)
        
        # 1. Récupérer le prix BTC
        btc_price = self.get_btc_price()
        
        # 2. Calculer la position
        position_data = self.calculate_position_size(amount_usd, leverage, btc_price)
        if not position_data:
            return {"error": "Erreur dans le calcul de position"}
        
        # 3. Placer l'ordre
        result = self.place_btc_order(position_data, side)
        
        return result


def main():
    """Fonction principale"""
    print("🤖 TRADER BTC - LEVIER 10x")
    print("⚠️  ATTENTION: Trading avec de l'argent réel!")
    print("=" * 60)
    
    # Confirmation de sécurité
    print("🚨 AVERTISSEMENT:")
    print("   - Vous allez trader avec de l'argent réel")
    print("   - Le levier 10x amplifie les gains ET les pertes")
    print("   - Vous pouvez perdre plus que votre investissement initial")
    print("   - Assurez-vous d'avoir les fonds nécessaires")
    print()
    
    confirm = input("🤔 Êtes-vous sûr de vouloir continuer? (tapez 'OUI' pour confirmer): ")
    if confirm != "OUI":
        print("❌ Trade annulé par l'utilisateur")
        return
    
    # Créer le trader
    trader = BTCTrader()
    
    # Initialiser
    if not trader.initialize():
        print("❌ Échec de l'initialisation")
        return
    
    # Authentifier
    if not trader.authenticate():
        print("❌ Échec de l'authentification")
        return
    
    # Exécuter le trade
    print("\n🚀 LANCEMENT DU TRADE...")
    result = trader.execute_trade(
        amount_usd=10.0,    # $10
        leverage=10,        # Levier 10x
        side="buy"          # Achat
    )
    
    # Afficher le résultat
    print("\n📊 RÉSULTAT DU TRADE:")
    print("=" * 30)
    if "error" in result:
        print(f"❌ Erreur: {result['error']}")
    else:
        print("✅ Ordre placé avec succès!")
        print(f"📋 Résultat: {result}")
    
    print("\n🎯 Trade terminé")


if __name__ == "__main__":
    main()
