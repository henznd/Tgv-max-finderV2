#!/usr/bin/env python3
"""
Script pour récupérer l'index de compte Lighter
"""

import asyncio
import aiohttp
import json

async def get_account_index():
    """Récupère l'index de compte depuis l'API Lighter"""
    l1_address = "0x19bF8d22f9772b1F349a803e5B640087f3d29C2a"
    api_url = "https://mainnet.zklighter.elliot.ai"
    
    print(f"🔍 Récupération de l'index de compte pour l'adresse L1: {l1_address}")
    
    try:
        async with aiohttp.ClientSession() as session:
            accounts_url = f"{api_url}/api/v1/accountsByL1Address"
            params = {"l1_address": l1_address}
            
            print(f"📡 URL: {accounts_url}")
            print(f"📋 Paramètres: {params}")
            
            async with session.get(accounts_url, params=params) as resp:
                print(f"📊 Status HTTP: {resp.status}")
                
                if resp.status == 200:
                    accounts_data = await resp.json()
                    print(f"✅ Réponse complète:")
                    print(json.dumps(accounts_data, indent=2))
                    
                    # Parser la réponse
                    if "sub_accounts" in accounts_data and len(accounts_data["sub_accounts"]) > 0:
                        sub_accounts = accounts_data["sub_accounts"]
                        print(f"\n📋 {len(sub_accounts)} sous-compte(s) trouvé(s):")
                        
                        for i, account in enumerate(sub_accounts):
                            print(f"   Compte {i+1}:")
                            print(f"     Index: {account.get('index', 'N/A')}")
                            print(f"     Type: {account.get('account_type', 'N/A')}")
                            print(f"     Autres champs: {list(account.keys())}")
                        
                        # Prendre le premier compte (ou celui avec account_type=0 si disponible)
                        first_account = sub_accounts[0]
                        account_index = first_account.get('index')
                        
                        print(f"\n✅ Index de compte sélectionné: {account_index}")
                        return account_index
                    else:
                        print("❌ Aucun sous-compte trouvé dans la réponse")
                        return None
                else:
                    error_text = await resp.text()
                    print(f"❌ Erreur HTTP {resp.status}: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Fonction principale"""
    print("🤖 RÉCUPÉRATEUR D'INDEX DE COMPTE LIGHTER")
    print("=" * 50)
    
    account_index = await get_account_index()
    
    if account_index:
        print(f"\n🎉 Index de compte récupéré: {account_index}")
        print(f"💡 Vous pouvez maintenant utiliser cet index dans vos scripts")
    else:
        print(f"\n💥 Échec de la récupération de l'index")
    
    print("\n🏁 Script terminé")

if __name__ == "__main__":
    asyncio.run(main())
