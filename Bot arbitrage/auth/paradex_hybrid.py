#!/usr/bin/env python3
"""
Script Paradex hybride - API REST avec structure SDK-like
Évite les problèmes de compatibilité Python tout en gardant une structure propre
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional
from enum import Enum

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class Environment(Enum):
    TESTNET = "testnet"
    MAINNET = "mainnet"

class ParadexClient:
    """Client Paradex avec structure SDK-like"""
    
    def __init__(self, l2_private_key: str, l2_address: str, env: Environment = Environment.TESTNET):
        self.l2_private_key = l2_private_key
        self.l2_address = l2_address
        self.env = env
        self.jwt_token = None
        
        # URLs selon l'environnement
        if env == Environment.TESTNET:
            self.base_url = "https://api.testnet.paradex.trade/v1"
        else:
            self.base_url = "https://api.prod.paradex.trade/v1"
    
    async def init_account(self):
        """Initialise le compte (authentification)"""
        print("🔐 Initialisation du compte...")
        
        # Headers d'authentification
        headers = {
            "PARADEX-STARKNET-ACCOUNT": self.l2_address,
            "PARADEX-STARKNET-SIGNATURE": '["123456789","987654321"]',  # Signature factice pour test
            "PARADEX-TIMESTAMP": str(int(time.time())),
            "PARADEX-SIGNATURE-EXPIRATION": str(int(time.time()) + 86400),
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/auth", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.jwt_token = data.get("jwt_token")
                    print("✅ Compte initialisé avec succès")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Erreur auth: {response.status} - {error_text}")
                    return False
    
    async def get_markets(self):
        """Récupère les marchés disponibles"""
        if not self.jwt_token:
            raise Exception("Compte non initialisé")
        
        print("📊 Récupération des marchés...")
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/markets", headers=headers) as response:
                if response.status == 200:
                    markets = await response.json()
                    print(f"✅ {len(markets)} marchés disponibles")
                    return markets
                else:
                    error_text = await response.text()
                    print(f"❌ Erreur marchés: {response.status} - {error_text}")
                    return None
    
    async def get_balance(self):
        """Récupère le solde du compte"""
        if not self.jwt_token:
            raise Exception("Compte non initialisé")
        
        print("💰 Récupération du solde...")
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/balance", headers=headers) as response:
                if response.status == 200:
                    balance = await response.json()
                    print(f"✅ Solde: {balance}")
                    return balance
                else:
                    error_text = await response.text()
                    print(f"❌ Erreur solde: {response.status} - {error_text}")
                    return None
    
    async def submit_order(self, market: str, side: OrderSide, size: str, order_type: OrderType, client_id: str = None):
        """Place un ordre sur Paradex"""
        if not self.jwt_token:
            raise Exception("Compte non initialisé")
        
        print("📝 Placement de l'ordre...")
        
        # Données de l'ordre
        order_data = {
            "market": market,
            "side": side.value,
            "size": size,
            "order_type": order_type.value,
            "client_id": client_id or f"trade_{int(time.time())}"
        }
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        print(f"📋 Ordre:")
        print(f"   📊 Market: {order_data['market']}")
        print(f"   📈 Side: {order_data['side']}")
        print(f"   💰 Size: {order_data['size']}")
        print(f"   🎯 Type: {order_data['order_type']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/orders", headers=headers, json=order_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Ordre placé avec succès!")
                    print(f"📋 Résultat: {result}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Erreur ordre: {response.status} - {error_text}")
                    return None
    
    async def close(self):
        """Ferme le client"""
        print("🔚 Client fermé")
        pass

# ========== CONFIGURATION ==========
L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
L2_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
MARKET = "BTC-USD-PERP"
SIZE_BTC = 0.0001
LEVERAGE = 10

async def main():
    """Script principal Paradex avec structure SDK-like"""
    print("🚀 SCRIPT PARADEX - TRADING BTC (STRUCTURE SDK-LIKE)")
    print("=" * 70)
    print(f"📡 L2 Address: {L2_ADDRESS}")
    print(f"📊 Market: {MARKET}")
    print(f"💰 Taille: {SIZE_BTC} BTC")
    print(f"⚡ Levier: {LEVERAGE}x")
    print("=" * 70)
    
    try:
        # Initialisation du client
        paradex = ParadexClient(
            l2_private_key=L2_PRIVATE_KEY,
            l2_address=L2_ADDRESS,
            env=Environment.TESTNET
        )
        
        # Initialisation du compte
        if not await paradex.init_account():
            print("❌ Impossible de s'authentifier")
            return
        
        # Récupération des marchés
        markets = await paradex.get_markets()
        if not markets:
            print("❌ Impossible de récupérer les marchés")
            return
        
        # Récupération du solde
        balance = await paradex.get_balance()
        if not balance:
            print("❌ Impossible de récupérer le solde")
            return
        
        # Placement de l'ordre
        result = await paradex.submit_order(
            market=MARKET,
            side=OrderSide.BUY,
            size=str(SIZE_BTC),
            order_type=OrderType.MARKET
        )
        
        if not result:
            print("❌ Impossible de placer l'ordre")
            return
        
        print("\n🎉 Script terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fermeture du client
        try:
            await paradex.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
