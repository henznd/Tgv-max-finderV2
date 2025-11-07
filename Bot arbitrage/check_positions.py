"""
Script pour vérifier les positions en cours sur Lighter
"""

import asyncio
from config import Config
from auth import LighterAuthenticator


async def check_positions():
    """Vérifie les positions en cours"""
    print("🔍 VÉRIFICATION DES POSITIONS")
    print("=" * 40)
    
    try:
        # Configuration
        config = Config()
        if not config.validate_lighter_config():
            print("❌ Configuration Lighter incomplète")
            return
        
        lighter_config = config.get_lighter_config()
        
        # Créer l'authentificateur
        print("🔧 Initialisation...")
        authenticator = LighterAuthenticator(
            api_url=lighter_config['api_url'],
            private_key=lighter_config['private_key'],
            wallet_address=lighter_config['wallet_address']
        )
        
        # Authentification
        print("🔐 Authentification...")
        if not authenticator.authenticate():
            print("❌ Échec de l'authentification")
            return
        
        print("✅ Authentifié avec succès")
        
        # Récupérer les positions via le client Lighter
        print("📊 Récupération des positions...")
        
        try:
            # Utiliser le client Lighter pour récupérer les positions
            positions = await authenticator.client.get_positions()
            
            if positions:
                print(f"📈 {len(positions)} position(s) trouvée(s):")
                for i, position in enumerate(positions, 1):
                    print(f"\n  Position {i}:")
                    print(f"    📊 Marché: {position.get('market', 'N/A')}")
                    print(f"    💰 Taille: {position.get('size', 'N/A')}")
                    print(f"    💲 Prix: {position.get('price', 'N/A')}")
                    print(f"    ⚡ Levier: {position.get('leverage', 'N/A')}x")
                    print(f"    📈 PnL: {position.get('pnl', 'N/A')}")
                    print(f"    📊 Statut: {position.get('status', 'N/A')}")
            else:
                print("📭 Aucune position active")
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des positions: {e}")
            
            # Essayer une méthode alternative
            print("🔄 Tentative avec méthode alternative...")
            try:
                # Récupérer les ordres actifs
                orders = await authenticator.client.get_orders()
                if orders:
                    print(f"📋 {len(orders)} ordre(s) actif(s):")
                    for order in orders:
                        print(f"    📝 Ordre: {order}")
                else:
                    print("📭 Aucun ordre actif")
            except Exception as e2:
                print(f"❌ Erreur alternative: {e2}")
        
        # Récupérer le solde
        print("\n💰 Récupération du solde...")
        try:
            balance = await authenticator.client.get_balance()
            print(f"💵 Solde: {balance}")
        except Exception as e:
            print(f"❌ Erreur solde: {e}")
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")


def main():
    """Fonction principale"""
    print("🤖 VÉRIFICATEUR DE POSITIONS LIGHTER")
    print("=" * 50)
    
    # Lancer la vérification
    asyncio.run(check_positions())
    
    print("\n🏁 Vérification terminée")


if __name__ == "__main__":
    main()
