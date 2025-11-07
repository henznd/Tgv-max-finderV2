#!/usr/bin/env python3
"""
Test exact selon le code fourni par l'utilisateur
"""

from paradex_py import Paradex
from paradex_py.environment import Environment
from paradex_py.common.order import Order, OrderSide, OrderType
from decimal import Decimal
import asyncio

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"

async def main():
    # Configuration avec vos clés du site web Paradex
    paradex = Paradex(
        env='prod',  # Pour mainnet (modifié de Environment.PROD)
        l2_private_key=L2_PRIVATE_KEY  # Clé privée récupérée depuis l'interface
    )
    
    try:
        # Initialisation du compte avec votre adresse
        paradex.init_account(
            l1_address="0x19bF8d22f9772b1F349a803e5B640087f3d29C2a",  # Votre vraie adresse L1
            l2_private_key=L2_PRIVATE_KEY
        )
        print("✅ Compte initialisé avec succès")
        
        # Récupérer les informations du compte
        account_info = paradex.api_client.fetch_account_summary()
        print(f"Informations du compte: {account_info}")
        
        # Récupérer le solde
        balances = paradex.api_client.fetch_balances()
        print(f"Soldes: {balances}")
        
        # Récupérer les marchés disponibles
        markets = paradex.api_client.fetch_markets()
        print(f"Marchés disponibles: {len(markets['results'])}")
        
        # Créer un ordre pour 100 USD avec effet de levier
        # Exemple avec ETH-USD-PERP
        buy_order = Order(
            market="ETH-USD-PERP",
            order_type=OrderType.Market,  # Ordre de marché
            order_side=OrderSide.Buy,
            size=Decimal("0.03"),  # ~100 USD selon le prix ETH
            client_id="trade_100_usd_10x",
            instruction="IOC",  # Immediate or Cancel
            reduce_only=False
        )
        
        # Placer l'ordre
        result = paradex.api_client.submit_order(order=buy_order)
        print(f"✅ Ordre placé: {result}")
        
        # Vérifier les positions ouvertes
        positions = paradex.api_client.fetch_positions()
        print(f"Positions: {positions}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
