"""
Configuration du bot de trading DEX
Gère les paramètres et les clés API
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration du bot de trading"""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialise la configuration
        
        Args:
            env_file: Fichier d'environnement à charger
        """
        load_dotenv(env_file)
        
        # Configuration Lighter
        self.lighter_api_url = os.getenv('LIGHTER_API_URL', 'https://api.lighter.xyz/v1')
        self.lighter_private_key = os.getenv('LIGHTER_PRIVATE_KEY')
        self.lighter_wallet_address = os.getenv('LIGHTER_WALLET_ADDRESS')
        self.lighter_api_key_index = int(os.getenv('LIGHTER_API_KEY_INDEX', '0'))
        
        # Configuration réseau
        self.network = os.getenv('NETWORK', 'mainnet')
        self.rpc_url = os.getenv('RPC_URL')
        self.gas_price_multiplier = float(os.getenv('GAS_PRICE_MULTIPLIER', '1.1'))
        
        # Configuration générale
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('TIMEOUT', '30'))
    
    def get_lighter_config(self) -> Dict[str, Any]:
        """Retourne la configuration Lighter"""
        return {
            'api_url': self.lighter_api_url,
            'private_key': self.lighter_private_key,
            'wallet_address': self.lighter_wallet_address,
            'api_key_index': self.lighter_api_key_index
        }
    
    def validate_lighter_config(self) -> bool:
        """Valide la configuration Lighter"""
        return all([
            self.lighter_api_url,
            self.lighter_private_key,
            self.lighter_wallet_address
        ])
    
    def get_network_config(self) -> Dict[str, Any]:
        """Retourne la configuration réseau"""
        return {
            'network': self.network,
            'rpc_url': self.rpc_url,
            'gas_price_multiplier': self.gas_price_multiplier
        }
    
    def is_debug_mode(self) -> bool:
        """Vérifie si le mode debug est activé"""
        return self.debug
    
    def get_retry_config(self) -> Dict[str, int]:
        """Retourne la configuration des tentatives"""
        return {
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }
