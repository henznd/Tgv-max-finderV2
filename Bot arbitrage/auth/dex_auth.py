"""
Authentificateur générique pour DEX
Interface commune pour différents DEX
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import requests


class DEXAuthenticator(ABC):
    """Interface abstraite pour l'authentification DEX"""
    
    def __init__(self, api_url: str, private_key: str, wallet_address: str):
        """
        Initialise l'authentificateur DEX
        
        Args:
            api_url: URL de l'API du DEX
            private_key: Clé privée du wallet
            wallet_address: Adresse du wallet
        """
        self.api_url = api_url
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authentifie le bot avec le DEX
        
        Returns:
            True si l'authentification réussit
        """
        pass
    
    @abstractmethod
    def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place un ordre
        
        Args:
            order_data: Données de l'ordre
            
        Returns:
            Réponse de l'API
        """
        pass
    
    @abstractmethod
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les ordres
        
        Args:
            status: Filtre par statut (optionnel)
            
        Returns:
            Liste des ordres
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Annule un ordre
        
        Args:
            order_id: ID de l'ordre à annuler
            
        Returns:
            Réponse de l'API
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """
        Récupère le solde du wallet
        
        Returns:
            Solde du wallet
        """
        pass
    
    def is_authenticated(self) -> bool:
        """Vérifie si le bot est authentifié"""
        return self.authenticated
    
    def get_wallet_address(self) -> str:
        """Retourne l'adresse du wallet"""
        return self.wallet_address
