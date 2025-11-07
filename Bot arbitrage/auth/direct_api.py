#!/usr/bin/env python3
"""
Script de trading direct via API REST Lighter
Contourne le problème du SDK qui retourne None
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

async def place_order_direct():
    """Place un ordre directement via l'API REST"""
    print("🚀 TRADING DIRECT VIA API REST")
    print("=" * 50)
    
    # Configuration
    config = Config()
    lighter_config = config.get_lighter_config()
    
    # Paramètres de l'ordre
    market_index = 1
    client_order_index = int(time.time() * 1000) % 1000000
    base_amount = 1000000  # 0.01 BTC en unités
    price = 0  # Market order
    is_ask = False  # Buy
    order_type = 1  # Market order
    time_in_force = 0  # GTC
    reduce_only = False
    trigger_price = 0
    order_expiry = 0
    
    print(f"📊 Paramètres de l'ordre:")
    print(f"   Market Index: {market_index}")
    print(f"   Client Order Index: {client_order_index}")
    print(f"   Base Amount: {base_amount}")
    print(f"   Price: {price}")
    print(f"   Is Ask: {is_ask}")
    print(f"   Order Type: {order_type}")
    
    # URL de l'API
    api_url = f"{lighter_config['api_url']}/api/v1/orders"
    
    # Payload de l'ordre
    order_payload = {
        "market_index": market_index,
        "client_order_index": client_order_index,
        "base_amount": base_amount,
        "price": price,
        "is_ask": is_ask,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "reduce_only": reduce_only,
        "trigger_price": trigger_price,
        "order_expiry": order_expiry
    }
    
    print(f"\n📝 Payload de l'ordre:")
    print(json.dumps(order_payload, indent=2))
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"\n🚀 Envoi de l'ordre à: {api_url}")
            
            async with session.post(api_url, json=order_payload) as resp:
                print(f"📊 Status HTTP: {resp.status}")
                
                if resp.status == 200:
                    response_data = await resp.json()
                    print("✅ Ordre placé avec succès!")
                    print(f"📋 Réponse: {json.dumps(response_data, indent=2)}")
                else:
                    error_text = await resp.text()
                    print(f"❌ Erreur HTTP {resp.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(place_order_direct())
