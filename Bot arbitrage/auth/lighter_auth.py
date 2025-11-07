"""
Authentification spécifique pour Lighter DEX
Utilise le SDK officiel de Lighter
"""

import json
import time
from typing import Dict, Any, Optional, List
from lighter import SignerClient
from .signature_manager import SignatureManager


class LighterAuthenticator:
    """Authentificateur pour Lighter DEX"""
    
    def __init__(self, api_url: str, private_key: str, wallet_address: str, account_index: int, api_key_index: int = 4):
        """
        Initialise l'authentificateur Lighter
        
        Args:
            api_url: URL de l'API Lighter
            private_key: Clé API Lighter (80 caractères)
            wallet_address: Adresse du wallet
            account_index: Index du compte (récupéré via API)
            api_key_index: Index de la clé API (depuis .env)
        """
        self.api_url = api_url.rstrip('/')
        self.private_key = private_key
        self.wallet_address = wallet_address
        
        # Initialiser le client Lighter
        try:
            self.client = SignerClient(
                self.api_url,
                self.private_key,
                api_key_index=api_key_index,
                account_index=account_index
            )
            print(f"✅ Client Lighter initialisé avec account_index={account_index}, api_key_index={api_key_index}")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du client Lighter: {e}")
            self.client = None
    
    def authenticate(self) -> bool:
        """
        Authentifie le bot avec Lighter
        
        Returns:
            True si l'authentification réussit
        """
        try:
            if not self.client:
                print("❌ Client Lighter non initialisé")
                return False
            
            # Le client Lighter gère l'authentification automatiquement
            print("✅ Authentification Lighter réussie (via SDK)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'authentification: {e}")
            return False
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place un ordre sur Lighter avec les paramètres directs
        """
        try:
            if not self.client:
                return {"error": "Client Lighter non initialisé"}

            print(f"📝 Placement de l'ordre...")
            
            # Utiliser les paramètres directement passés
            try:
                print(f"🔍 Appel create_order avec:")
                print(f"   market_index: {order_data.get('market_index')}")
                print(f"   client_order_index: {order_data.get('client_order_index')}")
                print(f"   base_amount: {order_data.get('base_amount')}")
                print(f"   price: {order_data.get('price')}")
                print(f"   is_ask: {order_data.get('is_ask')}")
                
                # Utiliser create_order avec order_type=0 (Limit order)
                order, tx_hash, err = await self.client.create_order(
                    market_index=int(order_data.get('market_index', 1)),
                    client_order_index=int(order_data.get('client_order_index', 100001)),
                    base_amount=int(order_data.get('base_amount', 0)),
                    price=int(order_data.get('price', 11700000)),  # Prix limite en centimes
                    is_ask=bool(order_data.get('is_ask', False)),
                    order_type=0,  # Limit order
                    time_in_force=0,  # GTC
                    reduce_only=False,
                    trigger_price=0,
                    order_expiry=0
                )
                print("✅ create_order appelé avec succès")
            except Exception as e:
                print(f"❌ Erreur dans create_order: {e}")
                print(f"🔍 Type d'erreur: {type(e)}")
                import traceback
                print(f"🔍 Traceback complet:")
                traceback.print_exc()
                return {"error": f"Erreur create_order: {e}", "success": False}
            
            # GESTION CORRECTE DES ERREURS selon la doc Lighter
            if err is not None:
                print(f"❌ Erreur lors du placement de l'ordre : {err}")
                return {"error": f"Erreur API: {err}", "success": False}
            
            if order is None or tx_hash is None:
                print("❌ L'API n'a retourné aucun ordre/aucun hash, vérifiez les paramètres.")
                return {"error": "L'API n'a retourné aucun ordre/aucun hash", "success": False}
            
            print("✅ Ordre placé :", order)
            print("Hash transaction :", tx_hash)
            
            # Retourner le résultat
            result = {
                "order": order,
                "tx_hash": tx_hash,
                "error": None,
                "success": True,
                "message": "Ordre placé avec succès"
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Erreur lors du placement de l'ordre: {e}"}
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les ordres
        
        Args:
            status: Filtre par statut (optionnel)
            
        Returns:
            Liste des ordres
        """
        try:
            params = {}
            if status:
                params['status'] = status
            
            response = self.session.get(
                f"{self.api_url}/orders",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('orders', [])
            else:
                print(f"Erreur lors de la récupération des ordres: {response.text}")
                return []
                
        except Exception as e:
            print(f"Erreur lors de la récupération des ordres: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Annule un ordre
        
        Args:
            order_id: ID de l'ordre à annuler
            
        Returns:
            Réponse de l'API
        """
        try:
            cancel_payload = {
                "wallet": self.signature_manager.wallet_address,
                "order_id": order_id,
                "action": "cancel",
                "timestamp": int(time.time())
            }
            
            signed_payload = self.signature_manager.sign_payload(cancel_payload)
            
            response = self.session.post(
                f"{self.api_url}/orders/cancel",
                json=signed_payload,
                timeout=30
            )
            
            return response.json()
            
        except Exception as e:
            return {"error": f"Erreur lors de l'annulation de l'ordre: {e}"}
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Récupère le solde du wallet
        
        Returns:
            Solde du wallet
        """
        try:
            balance_payload = {
                "wallet": self.signature_manager.wallet_address,
                "action": "get_balance",
                "timestamp": int(time.time())
            }
            
            signed_payload = self.signature_manager.sign_payload(balance_payload)
            
            response = self.session.post(
                f"{self.api_url}/balance",
                json=signed_payload,
                timeout=30
            )
            
            return response.json()
            
        except Exception as e:
            return {"error": f"Erreur lors de la récupération du solde: {e}"}
    
    def get_markets(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des marchés disponibles
        
        Returns:
            Liste des marchés
        """
        try:
            if not self.client:
                print("❌ Client Lighter non initialisé")
                return []
            
            # Utiliser le client Lighter pour récupérer les marchés
            markets = self.client.get_markets()
            return markets if markets else []
                
        except Exception as e:
            print(f"Erreur lors de la récupération des marchés: {e}")
            return []
