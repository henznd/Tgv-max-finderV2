"""
Script pour vérifier les positions en cours avec AccountApi
Utilise l'API officielle de Lighter pour récupérer les positions
"""

import asyncio
from config import Config
from lighter import ApiClient, Configuration, AccountApi


async def check_positions_with_api():
    """Vérifie les positions en cours avec AccountApi"""
    print("🔍 VÉRIFICATION DES POSITIONS AVEC ACCOUNT API")
    print("=" * 50)
    
    try:
        # Configuration
        config = Config()
        if not config.validate_lighter_config():
            print("❌ Configuration Lighter incomplète")
            return
        
        lighter_config = config.get_lighter_config()
        
        # Configuration de l'API
        BASE_URL = lighter_config['api_url']
        ACCOUNT_INDEX = 0  # Essayer avec le compte principal
        
        print(f"🌐 API URL: {BASE_URL}")
        print(f"👤 Account Index: {ACCOUNT_INDEX}")
        
        # Créer le client API
        print("🔧 Initialisation de l'API client...")
        api_client = ApiClient(configuration=Configuration(host=BASE_URL))
        account_api = AccountApi(api_client)
        
        # Récupérer les informations du compte par index
        print(f"📊 Récupération des informations du compte par index...")
        print(f"📍 Index: {ACCOUNT_INDEX}")
        
        # Essayer d'abord avec la méthode directe
        try:
            response = await account_api.account(account_index=ACCOUNT_INDEX)
        except Exception as e:
            print(f"⚠️ Méthode directe échouée: {e}")
            # Essayer avec la syntaxe alternative
            response = await account_api.account(by="index", value=str(ACCOUNT_INDEX))
        
        print("✅ Informations du compte récupérées")
        
        # Vérifier les positions ouvertes
        positions = response.open_positions
        
        if positions and len(positions) > 0:
            print(f"\n📈 {len(positions)} POSITION(S) OUVERTE(S):")
            print("=" * 50)
            
            for i, pos in enumerate(positions, 1):
                print(f"\n📍 Position {i}:")
                print(f"   📊 Marché Index: {pos.market_index}")
                print(f"   💰 Taille: {pos.base_amount}")
                print(f"   💲 Prix d'entrée: {pos.entry_price}")
                print(f"   📈 Side: {'LONG' if pos.base_amount > 0 else 'SHORT'}")
                print(f"   ⚡ Levier: {getattr(pos, 'leverage', 'N/A')}")
                print(f"   💵 PnL: {getattr(pos, 'pnl', 'N/A')}")
                print(f"   📊 Statut: {getattr(pos, 'status', 'N/A')}")
                print(f"   🔄 Mode: {getattr(pos, 'margin_mode', 'N/A')}")
                print("-" * 30)
        else:
            print("\n📭 AUCUNE POSITION OUVERTE")
            print("   Aucune position active trouvée sur ce compte")
        
        # Informations supplémentaires du compte
        print(f"\n💰 INFORMATIONS DU COMPTE:")
        print(f"   👤 Account Index: {ACCOUNT_INDEX}")
        print(f"   💵 Solde disponible: {getattr(response, 'available_balance', 'N/A')}")
        print(f"   📊 Total PnL: {getattr(response, 'total_pnl', 'N/A')}")
        print(f"   🔄 Nombre de positions: {len(positions) if positions else 0}")
        
        # Vérifier aussi par adresse ETH si disponible
        try:
            wallet_address = lighter_config['wallet_address']
            print(f"\n🔍 Vérification par adresse ETH: {wallet_address}")
            response_by_address = account_api.accounts_by_l1_address(l1_address=wallet_address)
            
            if response_by_address:
                print("✅ Compte trouvé par adresse ETH")
                positions_by_address = response_by_address.open_positions
                if positions_by_address:
                    print(f"📈 {len(positions_by_address)} position(s) via adresse ETH")
                else:
                    print("📭 Aucune position via adresse ETH")
            else:
                print("❌ Aucun compte trouvé pour cette adresse ETH")
                
        except Exception as e:
            print(f"⚠️ Erreur lors de la vérification par adresse: {e}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des positions: {e}")
        print("💡 Vérifiez que:")
        print("   - Votre compte est actif sur Lighter")
        print("   - L'index de compte est correct (2)")
        print("   - L'API est accessible")


def main():
    """Fonction principale"""
    print("🤖 VÉRIFICATEUR DE POSITIONS LIGHTER")
    print("🔗 Utilisation de l'AccountApi officielle")
    print("=" * 60)
    
    # Lancer la vérification
    asyncio.run(check_positions_with_api())
    
    print("\n🏁 Vérification terminée")
    print("💡 Si vous voyez des positions, votre trade précédent est actif !")


if __name__ == "__main__":
    main()
