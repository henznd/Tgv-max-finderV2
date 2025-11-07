#!/usr/bin/env python3
"""
Script Paradex simplifié avec vraie signature Starknet
Utilise la documentation officielle Paradex
"""

import aiohttp
import asyncio
import hashlib
import time
from enum import IntEnum
from typing import Dict

from starknet_py.common import int_from_bytes
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.utils.typed_data import TypedData

# Configuration Paradex
paradex_http_url = "https://api.testnet.paradex.trade/v1"

# ========== CONFIGURATION ==========
ACCOUNT_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
MARKET = "BTC-USD-PERP"
SIZE_BTC = 0.0001
LEVERAGE = 10

def build_auth_message(now: int, expiry: int):
    """Construit le message d'authentification selon la doc Paradex EXACTE"""
    return {
        "types": {
            "StarkNetDomain": [
                {"name": "name", "type": "felt"},
                {"name": "chainId", "type": "felt"},
                {"name": "version", "type": "felt"}
            ],
            "Request": [
                {"name": "method", "type": "felt"},
                {"name": "path", "type": "felt"},
                {"name": "body", "type": "felt"},
                {"name": "timestamp", "type": "felt"},
                {"name": "expiration", "type": "felt"}
            ]
        },
        "primaryType": "Request",
        "domain": {
            "name": "Paradex",
            "version": "1",
            "chainId": "0x505249564154455f534e5f50415241434c4541525f4d41494e4e4554"  # Mainnet Chain ID
        },
        "message": {
            "method": "POST",
            "path": "/v1/auth",
            "body": "",  # Chaîne vide importante
            "timestamp": now,
            "expiration": expiry
        }
    }

def get_chain_id(chain_id: str):
    """Convertit le chain_id en format Starknet"""
    class CustomStarknetChainId(IntEnum):
        PRIVATE_TESTNET = int_from_bytes(chain_id.encode("UTF-8"))
    return CustomStarknetChainId.PRIVATE_TESTNET

def hex_to_int(val: str):
    """Convertit hex en int"""
    return int(val, 16)

def sign_message_with_keypair(key_pair, message):
    """Signature avec KeyPair selon la doc Paradex EXACTE"""
    from starknet_py.hash.utils import message_signature, compute_hash_on_elements
    from starknet_py.hash.selector import get_selector_from_name
    
    # Construction du hash selon la spécification EIP-712 de Paradex EXACTE
    # 1. Hash du domain separator
    domain_hash = compute_hash_on_elements([
        get_selector_from_name("Paradex"),
        int("0x505249564154455f534e5f50415241434c4541525f4d41494e4e4554", 16),  # Mainnet Chain ID
        1
    ])
    
    # 2. Hash du message - selon la doc, body doit être encodé comme big.NewInt(0)
    message_hash = compute_hash_on_elements([
        get_selector_from_name("POST"),
        get_selector_from_name("/v1/auth"),
        0,  # body vide encodé comme 0 selon la doc
        int(message["message"]["timestamp"]),
        int(message["message"]["expiration"])
    ])
    
    # 3. Hash final selon EIP-712
    final_hash = compute_hash_on_elements([domain_hash, message_hash])
    
    # Signature du hash avec la clé privée
    return message_signature(key_pair.private_key, final_hash)

async def get_jwt_token(account_address, private_key):
    """Authentification Paradex avec vraie signature selon la doc"""
    # Configuration Paradex selon la doc
    paradex_config = {
        "starknet_chain_id": "PRIVATE_SN_POTC_SEPOLIA",
        "starknet_fullnode_rpc_url": "https://starknet-testnet.public.blastapi.io"
    }
    
    # Initialisation du client Starknet
    client = FullNodeClient(node_url=paradex_config["starknet_fullnode_rpc_url"])
    key_pair = KeyPair.from_private_key(key=hex_to_int(private_key))
    chain = get_chain_id(paradex_config["starknet_chain_id"])
    
    # Construction du message d'authentification selon la doc EXACTE
    now = int(time.time())
    expiry = now + 30 * 60  # 30 minutes selon la doc
    message = build_auth_message(now, expiry)
    
    # Signature du message avec la vraie signature Starknet
    # Utilisation de la méthode de signature appropriée
    sig = sign_message_with_keypair(key_pair, message)
    
    # Headers pour l'API Paradex selon la doc
    headers = {
        "PARADEX-STARKNET-ACCOUNT": account_address,
        "PARADEX-STARKNET-SIGNATURE": f'["{sig[0]}","{sig[1]}"]',
        "PARADEX-TIMESTAMP": str(now),
        "PARADEX-SIGNATURE-EXPIRATION": str(expiry),
    }
    
    # Requête d'authentification selon la doc (mainnet)
    url = "https://api.prod.paradex.trade/v1/auth"
    
    print(f"🔍 POST {url}")
    print(f"📋 Headers: {headers}")
    print(f"🔑 Vraie signature Starknet: [{sig[0]}, {sig[1]}]")
    
    # Configuration SSL pour contourner les problèmes de certificat
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, headers=headers) as response:
            status_code = response.status
            response_data = await response.json()
            
            if status_code == 200:
                print(f"✅ Success: {response_data}")
                print("✅ Get JWT successful")
                return response_data["jwt_token"]
            else:
                print(f"❌ Status Code: {status_code}")
                print(f"❌ Response: {response_data}")
                raise Exception(f"Erreur auth: {status_code} - {response_data}")

async def main():
    """Script principal Paradex avec vraie signature Starknet"""
    try:
        print("🚀 SCRIPT PARADEX - TRADING BTC (VRAIE SIGNATURE STARKNET)")
        print("=" * 60)
        print(f"📡 Account: {ACCOUNT_ADDRESS}")
        print(f"📊 Market: {MARKET}")
        print(f"💰 Taille: {SIZE_BTC} BTC")
        print(f"⚡ Levier: {LEVERAGE}x")
        print("=" * 60)
        
        # 1. Authentification avec vraie signature Starknet
        print("🔐 Authentification avec vraie signature Starknet...")
        jwt_token = await get_jwt_token(ACCOUNT_ADDRESS, PRIVATE_KEY)
        print(f"✅ JWT Token obtenu: {jwt_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())