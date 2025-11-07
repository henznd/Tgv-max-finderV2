#!/usr/bin/env python3
"""
Script Paradex avec authentification et trading
Utilise la vraie signature Starknet selon la documentation officielle
"""

import aiohttp
import asyncio
import hashlib
import logging
import random
import re
import time
from enum import IntEnum
from typing import Callable, Dict, Optional, Tuple

from eth_account.messages import encode_structured_data
from eth_account.signers.local import LocalAccount
from web3.auto import Web3, w3
from web3.middleware import construct_sign_and_send_raw_middleware

from starknet_py.common import int_from_bytes
from starknet_py.constants import RPC_CONTRACT_ERROR
from starknet_py.hash.address import compute_address
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client import Client
from starknet_py.net.client_errors import ClientError
from starknet_py.net.client_models import Call, Hash, TransactionExecutionStatus, TransactionFinalityStatus
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models import Address
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.proxy.contract_abi_resolver import ProxyConfig
from starknet_py.proxy.proxy_check import ArgentProxyCheck, OpenZeppelinProxyCheck, ProxyCheck
from starknet_py.transaction_errors import (
    TransactionRevertedError,
    TransactionNotReceivedError,
)
from starknet_py.utils.typed_data import TypedData

# Configuration Paradex
paradex_http_url = "https://api.testnet.paradex.trade/v1"

# ========== CONFIGURATION ==========
ACCOUNT_ADDRESS = "0x6e10b01c79d6dee5c462492f278a010d6ae2847bedecd075d89868fa7516a7c"
PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
MARKET = "BTC-USD-PERP"
SIZE_BTC = 0.0001                             # Taille ordonnée, en BTC
LEVERAGE = 10                                 # Levier

def build_auth_message(chainId: int, now: int, expiry: int) -> TypedData:
    """Construit le message d'authentification pour Paradex selon la doc"""
    message = {
        "message": {
            "method": "POST",
            "path": "/v1/auth",
            "body": "",
            "timestamp": now,
            "expiration": expiry,
        },
        "domain": {"name": "Paradex", "chainId": hex(chainId), "version": "1"},
        "primaryType": "Request",
        "types": {
            "StarkNetDomain": [
                {"name": "name", "type": "felt"},
                {"name": "chainId", "type": "felt"},
                {"name": "version", "type": "felt"},
            ],
            "Request": [
                {"name": "method", "type": "felt"},
                {"name": "path", "type": "felt"},
                {"name": "body", "type": "felt"},
                {"name": "timestamp", "type": "felt"},
                {"name": "expiration", "type": "felt"},
            ],
        },
    }
    return message

def grind_key(key_seed: int, key_value_limit: int) -> int:
    """Fonction de génération de clé selon la spécification Paradex"""
    max_allowed_value = 2**256 - (2**256 % key_value_limit)
    current_index = 0

    def indexed_sha256(seed: int, index: int) -> int:
        def padded_hex(x: int) -> str:
            # Hex string should have an even
            # number of characters to convert to bytes.
            hex_str = hex(x)[2:]
            return hex_str if len(hex_str) % 2 == 0 else "0" + hex_str

        digest = hashlib.sha256(bytes.fromhex(padded_hex(seed) + padded_hex(index))).hexdigest()
        return int(digest, 16)

    key = indexed_sha256(seed=key_seed, index=current_index)
    while key >= max_allowed_value:
        current_index += 1
        key = indexed_sha256(seed=key_seed, index=current_index)

    return key % key_value_limit

def get_private_key_from_eth_signature(eth_signature_hex: str) -> int:
    """Extrait la clé privée d'une signature Ethereum"""
    r = eth_signature_hex[2 : 64 + 2]
    # Utilisation d'une valeur par défaut au lieu d'EC_ORDER
    return grind_key(int(r, 16), 2**256 - 1)

def get_chain_id(chain_id: str):
    """Convertit le chain_id en format Starknet"""
    class CustomStarknetChainId(IntEnum):
        PRIVATE_TESTNET = int_from_bytes(chain_id.encode("UTF-8"))
    return CustomStarknetChainId.PRIVATE_TESTNET

def get_account(account_address: str, account_key: str, paradex_config: dict):
    """Crée un compte Starknet selon la doc Paradex"""
    client = FullNodeClient(node_url=paradex_config["starknet_fullnode_rpc_url"])
    key_pair = KeyPair.from_private_key(key=hex_to_int(account_key))
    chain = get_chain_id(paradex_config["starknet_chain_id"])
    
    # Retourne les composants nécessaires
    return client, key_pair, chain

def hex_to_int(val: str):
    """Convertit hex en int"""
    return int(val, 16)

async def get_jwt_token(account_address, private_key, chain_id):
    """Authentification Paradex avec vraie signature selon la doc"""
    # Configuration Paradex selon la doc
    paradex_config = {
        "starknet_chain_id": "PRIVATE_SN_POTC_SEPOLIA",
        "starknet_fullnode_rpc_url": "https://starknet-testnet.public.blastapi.io"
    }
    
    # Création des composants selon la doc Paradex
    client, key_pair, chain = get_account(account_address, private_key, paradex_config)
    
    # Construction du message d'authentification selon la doc
    now = int(time.time())
    expiry = now + 24 * 60 * 60
    message = build_auth_message(chain.value, now, expiry)
    
    # Signature du message avec la vraie signature Starknet
    # Utilisation de starknet_crypto_py pour signer
    from starknet_crypto_py import sign_message
    sig = sign_message(key_pair.private_key, message)
    
    # Headers pour l'API Paradex selon la doc
    headers = {
        "PARADEX-STARKNET-ACCOUNT": account_address,
        "PARADEX-STARKNET-SIGNATURE": f'["{sig[0]}","{sig[1]}"]',
        "PARADEX-TIMESTAMP": str(now),
        "PARADEX-SIGNATURE-EXPIRATION": str(expiry),
    }
    
    # Requête d'authentification selon la doc
    url = "https://api.prod.paradex.trade/v1/auth"
    
    print(f"🔍 POST {url}")
    print(f"📋 Headers: {headers}")
    print(f"🔑 Vraie signature Starknet: [{sig[0]}, {sig[1]}]")
    
    async with aiohttp.ClientSession() as session:
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

def set_leverage(jwt_token, leverage):
    """Configure le levier via l'API Paradex"""
    import requests
    
    leverage_data = {
        "leverage": leverage
    }
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.prod.paradex.trade/v1/margin/margin-modification",
        headers=headers,
        json=leverage_data
    )
    return response.json()

def create_order(jwt_token, account_address, private_key, chain_id):
    """Crée un ordre via l'API Paradex"""
    import requests
    import json
    from datetime import datetime
    
    timestamp = int(datetime.now().timestamp() * 1000)
    # Conversion Paradex base units : 1 BTC = 1e8 (satoshi sur l'API en doc)
    size_btc_units = str(int(float(SIZE_BTC) * 10**8))
    # side: 1=BUY, 2=SELL selon doc Paradex
    side = "1"  # 1 = BUY, 2 = SELL (short)

    order_data = {
        "client_id": f"trade_market_btc_{timestamp}",
        "market": MARKET,
        "side": "BUY",           # Pour l'API REST c'est le string, pour le hash c'est le chiffre
        "size": SIZE_BTC,        # Pour la REST API, le float. Pour la signature: unités
        "type": "MARKET",
        "signature_timestamp": timestamp
    }

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.prod.paradex.trade/v1/orders",
        headers=headers,
        json=order_data
    )
    return response.json()

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
        jwt_token = await get_jwt_token(ACCOUNT_ADDRESS, PRIVATE_KEY, "0x505249564154455f534e5f504f54435f5345504f4c4941")
        print(f"✅ JWT Token obtenu: {jwt_token[:20]}...")
        
        # 2. Configuration du levier
        print(f"📈 Configuration du levier {LEVERAGE}x...")
        leverage_result = set_leverage(jwt_token, LEVERAGE)
        print(f"✅ Levier configuré: {leverage_result}")
        
        # 3. Placement de l'ordre
        print("📝 Placement de l'ordre...")
        result = create_order(jwt_token, ACCOUNT_ADDRESS, PRIVATE_KEY, "0x505249564154455f534e5f504f54435f5345504f4c4941")
        print(f"✅ Ordre placé: {result}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())