import asyncio
from lighter import SignerClient

# ========= CONFIGURATION À COMPLÉTER =========
BASE_URL = "https://mainnet.zklighter.elliot.ai"  # Mainnet Lighter. Change selon environnement (testnet possible)
PRIVATE_KEY = "4ec938ba854c8af52f09cfb8cba30e140be4754d4980dbb86d1756a37b2ce9f8539fcbc4ae91183e"           # <--- Remplacer par la clé privée API générée sur le dashboard (ex: xxxxxxx)
ACCOUNT_INDEX = 116154         # <--- Remplacer par ton account_index (ex: 116154)
API_KEY_INDEX = 4          # <--- Adapter (0, 1, 2) selon API key utilisée (voir tableau dashboard)

# Paramètres custom pour la position BTC
MARKET_INDEX_BTC = 1       # BTC/USDC sur Lighter (testé avec 0, erreur NoneType)
ORDER_SIZE = 0.00001          # <--- Taille désirée en BTC
ORDER_SIZE_UNITS = int(ORDER_SIZE * 1e8)   # Conversion BTC -> unité API (1 BTC = 100 000 000) - MÊME QUE btc_trade_auto.py
CLIENT_ORDER_INDEX = 12345678              # <--- Numéro unique (à changer à chaque nouvel ordre si besoin)
LEVERAGE = 10               # <--- Levier désiré

async def main():
    print("🚀 SCRIPT COMPET - TRADING BTC")
    print("=" * 50)
    print(f"📡 API URL: {BASE_URL}")
    print(f"🔑 API Key Index: {API_KEY_INDEX}")
    print(f"👤 Account Index: {ACCOUNT_INDEX}")
    print(f"📊 Market Index BTC: {MARKET_INDEX_BTC}")
    print(f"💰 Taille ordre: {ORDER_SIZE} BTC ({ORDER_SIZE_UNITS} unités)")
    print(f"⚡ Levier: {LEVERAGE}x")
    print("=" * 50)
    
    # Init du client Signer
    print("🔧 Initialisation du client Signer...")
    try:
        client = SignerClient(BASE_URL, PRIVATE_KEY, api_key_index=API_KEY_INDEX, account_index=ACCOUNT_INDEX)
        print("✅ Client Signer initialisé avec succès")
    except Exception as e:
        print(f"❌ Erreur initialisation client: {e}")
        return

    # 1. On met à jour le levier pour BTC (market_index = 0), margin_mode = CROSS (0)
    print("\n📈 Changement du levier...")
    try:
        leverage_result = await client.update_leverage(
            market_index=MARKET_INDEX_BTC,
            margin_mode=0, # 0 pour cross, 1 pour isolated
            leverage=LEVERAGE
        )
        print(f"✅ Levier mis à jour: {leverage_result}")
    except Exception as e:
        print(f"❌ Erreur mise à jour levier: {e}")
        return

    # 2. Place un market order d'achat sur BTC
    print("\n📝 Placement de l'ordre market...")
    print(f"   📊 Market Index: {MARKET_INDEX_BTC}")
    print(f"   🆔 Client Order Index: {CLIENT_ORDER_INDEX}")
    print(f"   💰 Base Amount: {ORDER_SIZE_UNITS} unités")
    print(f"   💲 Avg Execution Price: 0 (market order)")
    print(f"   📈 Side: {'Achat' if not False else 'Vente'}")
    
    try:
        # Utiliser create_market_order selon la documentation officielle
        order, tx_hash, err = await client.create_market_order(
            market_index=MARKET_INDEX_BTC,
            client_order_index=CLIENT_ORDER_INDEX,
            base_amount=ORDER_SIZE_UNITS,    # Taille en "unités" API
            avg_execution_price=12000000,    # Prix en centimes ($120,000 * 100 = 12,000,000 centimes)
            is_ask=False                     # False = achat/long, True = vente/short
        )
        print("✅ create_order appelé avec succès")
        
        # GESTION CORRECTE DES ERREURS selon la doc Lighter (MÊME QUE btc_trade_auto.py)
        if err is not None:
            print(f"❌ Erreur lors du placement de l'ordre : {err}")
            return
        
        if order is None or tx_hash is None:
            print("❌ L'API n'a retourné aucun ordre/aucun hash, vérifiez les paramètres.")
            return
        
        print("✅ Ordre placé :", order)
        print("Hash transaction :", tx_hash)
        
    except Exception as e:
        print(f"❌ Erreur dans create_market_order: {e}")
        print(f"🔍 Type d'erreur: {type(e)}")
        import traceback
        print(f"🔍 Traceback complet:")
        traceback.print_exc()
        return

    print("\n🔚 Fermeture du client...")
    try:
        await client.close()
        print("✅ Client fermé")
    except Exception as e:
        print(f"⚠️ Erreur fermeture client: {e}")
    
    print("\n🏁 Script terminé")

if __name__ == "__main__":
    asyncio.run(main())

# ========= FIN DU SCRIPT =========

# Remarques importantes :
# - Remplace chaque valeur (<...>) par la tienne.
# - account_index, api_key_index et PRIVATE_KEY doivent typiquement matcher ton dashboard Lighter (voir tableau API Keys).
# - Adapte le MARKET_INDEX si BTC n’est pas 0 (utilise order_book_details pour vérifier).
# - Adapte la taille (ORDER_SIZE).
