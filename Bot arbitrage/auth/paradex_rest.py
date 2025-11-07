#!/usr/bin/env python3
"""
Script Paradex avec API REST directe
Évite les problèmes de compatibilité du SDK
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
MARKET = "BTC-USD-PERP"
SIZE_BTC = 0.0001
LEVERAGE = 10

# URLs API Paradex
BASE_URL = "https://api.testnet.paradex.trade/v1"
AUTH_URL = f"{BASE_URL}/auth"
MARKETS_URL = f"{BASE_URL}/markets"
ORDERS_URL = f"{BASE_URL}/orders"

async def get_jwt_token():
    """Authentification Paradex avec signature factice pour test"""
    print("🔐 Authentification...")
    
    # Headers d'authentification (version simplifiée)
    headers = {
        "PARADEX-STARKNET-ACCOUNT": L2_ADDRESS,
        "PARADEX-STARKNET-SIGNATURE": '["123456789","987654321"]',  # Signature factice
        "PARADEX-TIMESTAMP": str(int(time.time())),
        "PARADEX-SIGNATURE-EXPIRATION": str(int(time.time()) + 86400),
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(AUTH_URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Authentification réussie")
                return data.get("jwt_token")
            else:
                error_text = await response.text()
                print(f"❌ Erreur auth: {response.status} - {error_text}")
                return None

async def get_markets(jwt_token: str):
    """Récupère les marchés disponibles"""
    print("📊 Récupération des marchés...")
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(MARKETS_URL, headers=headers) as response:
            if response.status == 200:
                markets = await response.json()
                print(f"✅ {len(markets)} marchés disponibles")
                return markets
            else:
                error_text = await response.text()
                print(f"❌ Erreur marchés: {response.status} - {error_text}")
                return None

async def get_balance(jwt_token: str):
    """Récupère le solde du compte"""
    print("💰 Récupération du solde...")
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    balance_url = f"{BASE_URL}/balance"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(balance_url, headers=headers) as response:
            if response.status == 200:
                balance = await response.json()
                print(f"✅ Solde: {balance}")
                return balance
            else:
                error_text = await response.text()
                print(f"❌ Erreur solde: {response.status} - {error_text}")
                return None

async def place_order(jwt_token: str):
    """Place un ordre sur Paradex"""
    print("📝 Placement de l'ordre...")
    
    # Données de l'ordre
    order_data = {
        "market": MARKET,
        "side": "BUY",
        "size": str(SIZE_BTC),
        "order_type": "MARKET",
        "client_id": f"trade_btc_{int(time.time())}"
    }
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📋 Ordre:")
    print(f"   📊 Market: {order_data['market']}")
    print(f"   📈 Side: {order_data['side']}")
    print(f"   💰 Size: {order_data['size']}")
    print(f"   🎯 Type: {order_data['order_type']}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(ORDERS_URL, headers=headers, json=order_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Ordre placé avec succès!")
                print(f"📋 Résultat: {result}")
                return result
            else:
                error_text = await response.text()
                print(f"❌ Erreur ordre: {response.status} - {error_text}")
                return None

async def main():
    """Script principal Paradex avec API REST"""
    print("🚀 SCRIPT PARADEX - TRADING BTC (API REST)")
    print("=" * 60)
    print(f"📡 L2 Address: {L2_ADDRESS}")
    print(f"📊 Market: {MARKET}")
    print(f"💰 Taille: {SIZE_BTC} BTC")
    print(f"⚡ Levier: {LEVERAGE}x")
    print("=" * 60)
    
    try:
        # 1. Authentification
        jwt_token = await get_jwt_token()
        if not jwt_token:
            print("❌ Impossible de s'authentifier")
            return
        
        # 2. Récupération des marchés
        markets = await get_markets(jwt_token)
        if not markets:
            print("❌ Impossible de récupérer les marchés")
            return
        
        # 3. Récupération du solde
        balance = await get_balance(jwt_token)
        if not balance:
            print("❌ Impossible de récupérer le solde")
            return
        
        # 4. Placement de l'ordre
        result = await place_order(jwt_token)
        if not result:
            print("❌ Impossible de placer l'ordre")
            return
        
        print("\n🎉 Script terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
