"""
Gestionnaire de signatures pour l'authentification DEX
Utilise le SDK Lighter pour signer les requêtes avec la clé API
"""

import json
import hashlib
from typing import Dict, Any, Optional
import time


class SignatureManager:
    """Gestionnaire de signatures pour l'authentification DEX"""
    
    def __init__(self, private_key: str, wallet_address: str):
        """
        Initialise le gestionnaire de signatures
        
        Args:
            private_key: Clé API Lighter (format 80 caractères)
            wallet_address: Adresse du wallet
        """
        self.private_key = private_key
        self.wallet_address = wallet_address
        
        # Vérifier le format de la clé API Lighter
        if len(private_key) != 80:
            print(f"⚠️ Clé API Lighter: {len(private_key)} caractères (attendu: 80)")
        else:
            print(f"✅ Clé API Lighter valide: {len(private_key)} caractères")
    
    def sign_message(self, message: str) -> str:
        """
        Signe un message avec la clé API Lighter
        
        Args:
            message: Message à signer
            
        Returns:
            Signature hexadécimale
        """
        # Pour Lighter, on utilise le SDK officiel
        # Cette méthode sera remplacée par le client Lighter
        import hashlib
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        return f"lighter_signature_{message_hash[:16]}"
    
    def sign_structured_data(self, domain: Dict[str, Any], types: Dict[str, Any], 
                           primary_type: str, message: Dict[str, Any]) -> str:
        """
        Signe des données structurées (EIP-712)
        
        Args:
            domain: Domaine EIP-712
            types: Types EIP-712
            primary_type: Type principal
            message: Données du message
            
        Returns:
            Signature hexadécimale
        """
        structured_data = {
            'domain': domain,
            'types': types,
            'primaryType': primary_type,
            'message': message
        }
        
        encoded_data = encode_structured_data(structured_data)
        signed_message = self.account.sign_message(encoded_data)
        return signed_message.signature.hex()
    
    def sign_payload(self, payload: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """
        Signe un payload pour une requête API
        
        Args:
            payload: Données à envoyer
            method: Méthode HTTP
            
        Returns:
            Payload avec signature ajoutée
        """
        # Ajouter des métadonnées de signature
        timestamp = int(time.time())
        nonce = self._generate_nonce()
        
        # Créer le message à signer
        message_data = {
            "method": method,
            "timestamp": timestamp,
            "nonce": nonce,
            "wallet": self.wallet_address,
            "payload": payload
        }
        
        message_json = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
        signature = self.sign_message(message_json)
        
        # Retourner le payload avec la signature
        signed_payload = {
            "wallet": self.wallet_address,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature,
            "data": payload
        }
        
        return signed_payload
    
    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        """
        Vérifie une signature
        
        Args:
            message: Message original
            signature: Signature à vérifier
            address: Adresse qui a signé
            
        Returns:
            True si la signature est valide
        """
        try:
            message_hash = encode_defunct(text=message)
            recovered_address = Account.recover_message(message_hash, signature=signature)
            return recovered_address.lower() == address.lower()
        except Exception:
            return False
    
    def _generate_nonce(self) -> str:
        """Génère un nonce unique"""
        return hashlib.sha256(
            f"{self.wallet_address}{time.time()}".encode()
        ).hexdigest()[:16]
    
    def get_wallet_info(self) -> Dict[str, str]:
        """Retourne les informations du wallet"""
        return {
            "address": self.wallet_address,
            "public_key": self.account._key_obj.public_key.to_hex(),
            "private_key": self.private_key  # Attention: ne pas exposer en production
        }
