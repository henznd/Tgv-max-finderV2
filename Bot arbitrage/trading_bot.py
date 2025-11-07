"""
Bot de trading pour DEX
Script principal pour l'authentification et le trading
"""

import sys
import time
from typing import Dict, Any, Optional
from config import Config
from auth import LighterAuthenticator


class TradingBot:
    """Bot de trading pour DEX"""
    
    def __init__(self, config_file: str = ".env"):
        """
        Initialise le bot de trading
        
        Args:
            config_file: Fichier de configuration
        """
        self.config = Config(config_file)
        self.authenticator = None
        self.authenticated = False
    
    def initialize_lighter(self) -> bool:
        """
        Initialise la connexion avec Lighter
        
        Returns:
            True si l'initialisation réussit
        """
        try:
            if not self.config.validate_lighter_config():
                print("❌ Configuration Lighter incomplète")
                print("Vérifiez vos variables d'environnement:")
                print("- LIGHTER_API_URL")
                print("- LIGHTER_PRIVATE_KEY") 
                print("- LIGHTER_WALLET_ADDRESS")
                return False
            
            lighter_config = self.config.get_lighter_config()
            self.authenticator = LighterAuthenticator(
                api_url=lighter_config['api_url'],
                private_key=lighter_config['private_key'],
                wallet_address=lighter_config['wallet_address']
            )
            
            print("✅ Authentificateur Lighter initialisé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Lighter: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Authentifie le bot
        
        Returns:
            True si l'authentification réussit
        """
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
    
    def test_connection(self) -> bool:
        """
        Teste la connexion avec le DEX
        
        Returns:
            True si la connexion fonctionne
        """
        if not self.authenticated:
            print("❌ Bot non authentifié")
            return False
        
        try:
            print("🔍 Test de connexion...")
            
            # Tester la récupération des marchés
            markets = self.authenticator.get_markets()
            if markets:
                print(f"✅ Connexion réussie - {len(markets)} marchés disponibles")
                return True
            else:
                print("⚠️ Connexion établie mais aucun marché trouvé")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors du test de connexion: {e}")
            return False
    
    def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        Récupère le solde du wallet
        
        Returns:
            Solde du wallet ou None en cas d'erreur
        """
        if not self.authenticated:
            print("❌ Bot non authentifié")
            return None
        
        try:
            print("💰 Récupération du solde...")
            balance = self.authenticator.get_balance()
            
            if 'error' in balance:
                print(f"❌ Erreur: {balance['error']}")
                return None
            
            print("✅ Solde récupéré")
            return balance
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du solde: {e}")
            return None
    
    def place_test_order(self) -> bool:
        """
        Place un ordre de test (ne sera pas exécuté)
        
        Returns:
            True si l'ordre de test est créé avec succès
        """
        if not self.authenticated:
            print("❌ Bot non authentifié")
            return False
        
        try:
            print("📝 Création d'un ordre de test...")
            
            # Ordre de test (limit buy pour ETH-USDC)
            test_order = {
                "type": "limit",
                "side": "buy",
                "symbol": "ETH-USDC",
                "price": 1500.0,
                "size": 0.001,  # Très petit montant pour le test
                "time_in_force": "GTC",
                "reduce_only": False,
                "post_only": True,  # Ne sera pas exécuté immédiatement
                "test_mode": True   # Mode test
            }
            
            result = self.authenticator.place_order(test_order)
            
            if 'error' in result:
                print(f"❌ Erreur lors de la création de l'ordre: {result['error']}")
                return False
            
            print("✅ Ordre de test créé avec succès")
            print(f"📊 Résultat: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'ordre de test: {e}")
            return False
    
    def get_orders(self, status: Optional[str] = None) -> None:
        """
        Affiche les ordres
        
        Args:
            status: Filtre par statut (optionnel)
        """
        if not self.authenticated:
            print("❌ Bot non authentifié")
            return
        
        try:
            print("📋 Récupération des ordres...")
            orders = self.authenticator.get_orders(status)
            
            if not orders:
                print("📭 Aucun ordre trouvé")
                return
            
            print(f"📊 {len(orders)} ordre(s) trouvé(s):")
            for i, order in enumerate(orders, 1):
                print(f"  {i}. {order}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des ordres: {e}")
    
    def run_demo(self) -> None:
        """Exécute une démonstration complète"""
        print("🚀 Démarrage du bot de trading DEX")
        print("=" * 50)
        
        # 1. Initialisation
        if not self.initialize_lighter():
            return
        
        # 2. Authentification
        if not self.authenticate():
            return
        
        # 3. Test de connexion
        if not self.test_connection():
            return
        
        # 4. Récupération du solde
        balance = self.get_balance()
        if balance:
            print(f"💰 Solde: {balance}")
        
        # 5. Récupération des ordres existants
        self.get_orders()
        
        # 6. Test d'ordre (optionnel)
        if input("\n🤔 Voulez-vous créer un ordre de test? (y/N): ").lower() == 'y':
            self.place_test_order()
        
        print("\n✅ Démonstration terminée")
        print("🔧 Le bot est prêt pour le trading automatique")


def main():
    """Fonction principale"""
    print("🤖 Bot de Trading DEX - Authentification")
    print("=" * 50)
    
    # Vérifier les arguments
    config_file = sys.argv[1] if len(sys.argv) > 1 else ".env"
    
    # Créer et lancer le bot
    bot = TradingBot(config_file)
    bot.run_demo()


if __name__ == "__main__":
    main()
