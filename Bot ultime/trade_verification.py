#!/usr/bin/env python3
"""
Module de vérification complète des trades
Vérifie l'exécution, les balances, les positions et les niveaux de liquidation
"""

import asyncio
import aiohttp
from typing import Dict, Optional, Tuple
from decimal import Decimal
from logger import setup_logger

logger = setup_logger("trade_verification")

# ========== CONFIGURATION LIGHTER ==========
LIGHTER_BASE_URL = "https://mainnet.zklighter.elliot.ai"
LIGHTER_ACCOUNT_INDEX = 116154
LIGHTER_API_KEY_INDEX = 4

# ========== CONFIGURATION PARADEX ==========
PARADEX_L2_PRIVATE_KEY = "0x416487c13e987b1283d69e73c4fd50af863742d0df0e07dcaaa7135d57ecd21"
PARADEX_L1_ADDRESS = "0x19bF8d22f9772b1F349a803e5B640087f3d29C2a"

# Mapping des tokens vers market_index (Lighter)
LIGHTER_MARKET_IDS = {
    "BTC": 1,
    "ETH": 0,
    "SOL": 2,
    "BNB": 25
}

# Mapping des tokens vers les marchés (Paradex)
PARADEX_MARKETS = {
    "BTC": "BTC-USD-PERP",
    "ETH": "ETH-USD-PERP",
    "SOL": "SOL-USD-PERP"
}


class TradeVerification:
    """Classe pour vérifier l'exécution complète des trades"""
    
    def __init__(self):
        self.logger = setup_logger("trade_verification")
    
    async def verify_lighter_trade(
        self,
        token: str,
        expected_amount: float,
        order_type: str,
        leverage: int,
        tx_hash: Optional[str] = None
    ) -> Dict:
        """
        Vérifie complètement un trade Lighter
        
        Returns:
            dict avec les clés:
            - executed: bool
            - position_found: bool
            - balance_before: dict
            - balance_after: dict
            - position_size: float
            - liquidation_price: Optional[float]
            - margin_used: Optional[float]
            - health_factor: Optional[float]
        """
        self.logger.info("=" * 60)
        self.logger.info("🔍 VÉRIFICATION COMPLÈTE LIGHTER")
        self.logger.info("=" * 60)
        
        market_index = LIGHTER_MARKET_IDS.get(token)
        if market_index is None:
            self.logger.error(f"❌ Token {token} non supporté pour Lighter")
            return {"executed": False, "error": f"Token {token} non supporté"}
        
        result = {
            "executed": False,
            "position_found": False,
            "balance_before": None,
            "balance_after": None,
            "position_size": 0.0,
            "liquidation_price": None,
            "margin_used": None,
            "health_factor": None,
            "error": None
        }
        
        try:
            # 1. Récupérer l'état du compte AVANT (si possible)
            self.logger.info("📊 Récupération de l'état du compte...")
            account_state = await self._get_lighter_account_state()
            
            if account_state:
                result["balance_before"] = {
                    "total_equity": account_state.get("total_equity"),
                    "available_margin": account_state.get("available_margin"),
                    "used_margin": account_state.get("used_margin"),
                    "positions": account_state.get("positions", [])
                }
                self.logger.info(f"   💰 Equity totale: ${account_state.get('total_equity', 'N/A')}")
                self.logger.info(f"   💵 Marge disponible: ${account_state.get('available_margin', 'N/A')}")
                self.logger.info(f"   📊 Positions ouvertes: {len(account_state.get('positions', []))}")
            
            # 2. Attendre un peu pour que l'ordre soit traité
            await asyncio.sleep(3)
            
            # 3. Vérifier les positions après le trade
            self.logger.info("🔍 Vérification des positions après le trade...")
            account_state_after = await self._get_lighter_account_state()
            
            if account_state_after:
                result["balance_after"] = {
                    "total_equity": account_state_after.get("total_equity"),
                    "available_margin": account_state_after.get("available_margin"),
                    "used_margin": account_state_after.get("used_margin"),
                    "positions": account_state_after.get("positions", [])
                }
                
                # Chercher la position pour ce market_index
                positions = account_state_after.get("positions", [])
                for pos in positions:
                    pos_market = pos.get("market_index") or pos.get("marketIndex")
                    if pos_market == market_index:
                        pos_size = float(pos.get("size") or pos.get("base_amount") or pos.get("baseAmount") or 0)
                        
                        if abs(pos_size) > 0:
                            result["position_found"] = True
                            result["position_size"] = pos_size
                            result["executed"] = True
                            
                            # Calculer le prix de liquidation approximatif
                            # liquidation_price = entry_price * (1 - 1/leverage) pour long
                            # liquidation_price = entry_price * (1 + 1/leverage) pour short
                            entry_price = float(pos.get("entry_price") or pos.get("entryPrice") or 0)
                            if entry_price > 0:
                                if order_type.lower() == "buy":  # Long
                                    result["liquidation_price"] = entry_price * (1 - 1/leverage)
                                else:  # Short
                                    result["liquidation_price"] = entry_price * (1 + 1/leverage)
                            
                            # Marge utilisée
                            result["margin_used"] = float(pos.get("margin") or pos.get("margin_used") or 0)
                            
                            # Health factor (approximatif)
                            if result["balance_after"]["total_equity"] and result["margin_used"]:
                                result["health_factor"] = result["balance_after"]["total_equity"] / result["margin_used"]
                            
                            self.logger.info(f"   ✅ Position trouvée: {pos_size} {token}")
                            self.logger.info(f"   💰 Prix d'entrée: ${entry_price:.2f}")
                            if result["liquidation_price"]:
                                self.logger.info(f"   ⚠️ Prix de liquidation: ${result['liquidation_price']:.2f}")
                            if result["health_factor"]:
                                self.logger.info(f"   📊 Health factor: {result['health_factor']:.2f}")
                            break
                
                if not result["position_found"]:
                    self.logger.warning(f"   ⚠️ Aucune position trouvée pour market_index {market_index}")
                    self.logger.warning("   ⚠️ L'ordre n'a probablement pas été exécuté")
                else:
                    # Comparer les balances
                    if result["balance_before"] and result["balance_after"]:
                        equity_diff = (result["balance_after"]["total_equity"] or 0) - (result["balance_before"]["total_equity"] or 0)
                        margin_diff = (result["balance_after"]["available_margin"] or 0) - (result["balance_before"]["available_margin"] or 0)
                        self.logger.info(f"   📊 Changement equity: ${equity_diff:.2f}")
                        self.logger.info(f"   📊 Changement marge disponible: ${margin_diff:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la vérification Lighter: {e}")
            import traceback
            self.logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
            result["error"] = str(e)
        
        self.logger.info("=" * 60)
        return result
    
    async def verify_paradex_trade(
        self,
        token: str,
        expected_amount: float,
        order_type: str,
        leverage: int,
        order_id: Optional[str] = None,
        paradex_client = None
    ) -> Dict:
        """
        Vérifie complètement un trade Paradex
        
        Args:
            paradex_client: Instance du client Paradex (optionnel, sera créé si None)
        
        Returns:
            dict avec les mêmes clés que verify_lighter_trade
        """
        self.logger.info("=" * 60)
        self.logger.info("🔍 VÉRIFICATION COMPLÈTE PARADEX")
        self.logger.info("=" * 60)
        
        market = PARADEX_MARKETS.get(token, f"{token}-USD-PERP")
        
        result = {
            "executed": False,
            "position_found": False,
            "balance_before": None,
            "balance_after": None,
            "position_size": 0.0,
            "liquidation_price": None,
            "margin_used": None,
            "health_factor": None,
            "error": None
        }
        
        try:
            # Si pas de client fourni, on ne peut pas vérifier
            if paradex_client is None:
                self.logger.warning("⚠️ Client Paradex non fourni, vérification limitée")
                return result
            
            # 1. Récupérer l'état du compte AVANT
            self.logger.info("📊 Récupération de l'état du compte...")
            try:
                account_summary_before = paradex_client.api_client.fetch_account_summary()
                if account_summary_before:
                    # AccountSummary peut être un objet ou un dict
                    if isinstance(account_summary_before, dict):
                        total_equity = account_summary_before.get("total_equity")
                        available_balance = account_summary_before.get("available_balance")
                        margin_used = account_summary_before.get("margin_used")
                        unrealized_pnl = account_summary_before.get("unrealized_pnl")
                    else:
                        # C'est un objet, utiliser getattr
                        total_equity = getattr(account_summary_before, 'total_equity', None)
                        available_balance = getattr(account_summary_before, 'available_balance', None)
                        margin_used = getattr(account_summary_before, 'margin_used', None)
                        unrealized_pnl = getattr(account_summary_before, 'unrealized_pnl', None)
                    
                    result["balance_before"] = {
                        "total_equity": total_equity,
                        "available_balance": available_balance,
                        "margin_used": margin_used,
                        "unrealized_pnl": unrealized_pnl
                    }
                    self.logger.info(f"   💰 Equity totale: ${total_equity or 'N/A'}")
                    self.logger.info(f"   💵 Balance disponible: ${available_balance or 'N/A'}")
            except Exception as e:
                self.logger.warning(f"   ⚠️ Impossible de récupérer l'état avant: {e}")
            
            # 2. Attendre un peu pour que l'ordre soit traité
            await asyncio.sleep(2)
            
            # 3. Vérifier le statut de l'ordre
            if order_id:
                self.logger.info(f"🔍 Vérification de l'ordre ID: {order_id}")
                try:
                    orders = paradex_client.api_client.fetch_orders()
                    if orders and 'results' in orders:
                        for o in orders['results']:
                            if str(o.get('id')) == str(order_id):
                                order_status = o.get('status', 'UNKNOWN')
                                remaining_size = float(o.get('remaining_size', '0') or 0)
                                self.logger.info(f"   📊 Statut: {order_status}")
                                self.logger.info(f"   📊 Taille restante: {remaining_size}")
                                
                                if order_status == 'FILLED' or remaining_size == 0:
                                    result["executed"] = True
                                break
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Erreur vérification ordre: {e}")
            
            # 4. Vérifier les positions
            self.logger.info("🔍 Vérification des positions...")
            try:
                positions = paradex_client.api_client.fetch_positions()
                if positions and 'results' in positions:
                    for pos in positions['results']:
                        if pos.get('market') == market and pos.get('status') == 'OPEN':
                            size = float(pos.get('size', 0) or 0)
                            if abs(size) > 0:
                                result["position_found"] = True
                                result["position_size"] = size
                                result["executed"] = True
                                
                                # Prix de liquidation
                                result["liquidation_price"] = float(pos.get('liquidation_price') or pos.get('liquidationPrice') or 0)
                                
                                # Marge utilisée
                                result["margin_used"] = float(pos.get('margin') or pos.get('margin_used') or 0)
                                
                                # Health factor (maintenance margin ratio)
                                maintenance_margin = float(pos.get('maintenance_margin') or pos.get('maintenanceMargin') or 0)
                                if result["margin_used"] > 0:
                                    result["health_factor"] = result["margin_used"] / maintenance_margin if maintenance_margin > 0 else None
                                
                                self.logger.info(f"   ✅ Position trouvée: {size} {token}")
                                if result["liquidation_price"]:
                                    self.logger.info(f"   ⚠️ Prix de liquidation: ${result['liquidation_price']:.2f}")
                                if result["health_factor"]:
                                    self.logger.info(f"   📊 Health factor: {result['health_factor']:.2f}")
                                break
            except Exception as e:
                self.logger.warning(f"   ⚠️ Erreur vérification positions: {e}")
            
            # 5. Récupérer l'état du compte APRÈS
            try:
                account_summary_after = paradex_client.api_client.fetch_account_summary()
                if account_summary_after:
                    # AccountSummary peut être un objet ou un dict
                    if isinstance(account_summary_after, dict):
                        total_equity = account_summary_after.get("total_equity")
                        available_balance = account_summary_after.get("available_balance")
                        margin_used = account_summary_after.get("margin_used")
                        unrealized_pnl = account_summary_after.get("unrealized_pnl")
                    else:
                        # C'est un objet, utiliser getattr
                        total_equity = getattr(account_summary_after, 'total_equity', None)
                        available_balance = getattr(account_summary_after, 'available_balance', None)
                        margin_used = getattr(account_summary_after, 'margin_used', None)
                        unrealized_pnl = getattr(account_summary_after, 'unrealized_pnl', None)
                    
                    result["balance_after"] = {
                        "total_equity": total_equity,
                        "available_balance": available_balance,
                        "margin_used": margin_used,
                        "unrealized_pnl": unrealized_pnl
                    }
                    
                    # Comparer les balances
                    if result["balance_before"] and result["balance_after"]:
                        equity_diff = (result["balance_after"]["total_equity"] or 0) - (result["balance_before"]["total_equity"] or 0)
                        margin_diff = (result["balance_after"]["available_balance"] or 0) - (result["balance_before"]["available_balance"] or 0)
                        self.logger.info(f"   📊 Changement equity: ${equity_diff:.2f}")
                        self.logger.info(f"   📊 Changement balance disponible: ${margin_diff:.2f}")
            except Exception as e:
                self.logger.warning(f"   ⚠️ Impossible de récupérer l'état après: {e}")
            
            if not result["executed"]:
                self.logger.warning("   ⚠️ Ordre non exécuté confirmé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la vérification Paradex: {e}")
            import traceback
            self.logger.debug(f"🔍 Traceback: {traceback.format_exc()}")
            result["error"] = str(e)
        
        self.logger.info("=" * 60)
        return result
    
    async def _get_lighter_account_state(self) -> Optional[Dict]:
        """Récupère l'état du compte Lighter via AccountApi"""
        try:
            from lighter.api.account_api import AccountApi
            from lighter.api_client import ApiClient
            import ssl
            
            # Créer un client API avec SSL désactivé (comme pour les autres appels)
            api_client = ApiClient()
            api_client.configuration.host = LIGHTER_BASE_URL
            api_client.configuration.ssl_ca_cert = False  # Désactiver la vérification SSL
            # Configurer le connector aiohttp pour désactiver SSL
            import aiohttp
            connector = aiohttp.TCPConnector(ssl=False)
            api_client.rest_client.pool_manager._connector = connector
            
            # Créer l'API Account
            account_api = AccountApi(api_client)
            
            # Récupérer le compte par index
            self.logger.info(f"📡 Récupération de l'état du compte Lighter (index: {LIGHTER_ACCOUNT_INDEX})...")
            accounts_response = await account_api.account(by="index", value=str(LIGHTER_ACCOUNT_INDEX))
            
            # accounts_response est un DetailedAccounts qui contient une liste accounts
            account = None
            if hasattr(accounts_response, 'accounts') and accounts_response.accounts:
                account = accounts_response.accounts[0]  # Prendre le premier compte
            elif hasattr(accounts_response, 'account'):
                account = accounts_response.account
            else:
                account = accounts_response
            
            if not account:
                self.logger.warning("⚠️ Aucun compte trouvé dans la réponse")
                return None
            
            # Extraire les informations pertinentes
            positions = []
            if hasattr(account, 'positions') and account.positions:
                for pos in account.positions:
                    if hasattr(pos, 'base_amount') or hasattr(pos, 'size'):
                        size = getattr(pos, 'base_amount', getattr(pos, 'size', 0))
                        if hasattr(size, '__float__'):
                            size = float(size)
                        positions.append({
                            "market_index": getattr(pos, 'market_index', None),
                            "size": size,
                            "entry_price": float(getattr(pos, 'entry_price', 0)) if hasattr(pos, 'entry_price') else 0,
                        })
            
            # Récupérer les stats de marge si disponibles
            # Essayer différents noms d'attributs possibles
            total_equity = None
            available_margin = None
            used_margin = None
            
            # Chercher dans account directement
            if hasattr(account, 'total_equity'):
                total_equity = float(account.total_equity) if account.total_equity else None
            if hasattr(account, 'available_margin'):
                available_margin = float(account.available_margin) if account.available_margin else None
            if hasattr(account, 'used_margin'):
                used_margin = float(account.used_margin) if account.used_margin else None
            
            # Chercher dans margin_stats si disponible
            margin_stats = getattr(account, 'margin_stats', None)
            if margin_stats:
                if hasattr(margin_stats, 'total_equity'):
                    total_equity = float(margin_stats.total_equity) if margin_stats.total_equity else None
                if hasattr(margin_stats, 'available_margin'):
                    available_margin = float(margin_stats.available_margin) if margin_stats.available_margin else None
                if hasattr(margin_stats, 'used_margin'):
                    used_margin = float(margin_stats.used_margin) if margin_stats.used_margin else None
            
            result = {
                "total_equity": total_equity,
                "available_margin": available_margin,
                "used_margin": used_margin,
                "positions": positions
            }
            
            self.logger.info(f"✅ État du compte récupéré: {len(positions)} positions")
            await api_client.close()
            
            return result
            
        except ImportError:
            self.logger.warning("⚠️ AccountApi non disponible, impossible de récupérer l'état")
            return None
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur récupération état Lighter: {e}")
            import traceback
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def check_liquidation_risk(
        self,
        liquidation_price: Optional[float],
        current_price: float,
        token: str
    ) -> Tuple[bool, str]:
        """
        Vérifie le risque de liquidation
        
        Returns:
            (is_risky: bool, message: str)
        """
        if liquidation_price is None:
            return False, "Prix de liquidation non disponible"
        
        # Calculer la distance en pourcentage
        if liquidation_price > 0:
            distance_pct = abs((current_price - liquidation_price) / current_price) * 100
            
            # Seuil de risque: si on est à moins de 5% du prix de liquidation
            if distance_pct < 5:
                return True, f"⚠️ RISQUE ÉLEVÉ: Prix actuel ${current_price:.2f} très proche du prix de liquidation ${liquidation_price:.2f} ({distance_pct:.2f}%)"
            elif distance_pct < 10:
                return True, f"⚠️ Risque modéré: Prix actuel ${current_price:.2f} à {distance_pct:.2f}% du prix de liquidation ${liquidation_price:.2f}"
            else:
                return False, f"✅ Sécurité: Prix actuel ${current_price:.2f} à {distance_pct:.2f}% du prix de liquidation ${liquidation_price:.2f}"
        
        return False, "Prix de liquidation invalide"
    
    def check_health_factor(self, health_factor: Optional[float]) -> Tuple[bool, str]:
        """
        Vérifie le health factor
        
        Returns:
            (is_healthy: bool, message: str)
        """
        if health_factor is None:
            return False, "Health factor non disponible"
        
        # Health factor > 2 = très sain
        # Health factor < 1.5 = risque
        # Health factor < 1 = liquidation imminente
        if health_factor < 1:
            return False, f"❌ CRITIQUE: Health factor {health_factor:.2f} < 1 (liquidation imminente)"
        elif health_factor < 1.5:
            return False, f"⚠️ DANGER: Health factor {health_factor:.2f} < 1.5 (risque élevé)"
        elif health_factor < 2:
            return True, f"⚠️ Attention: Health factor {health_factor:.2f} < 2 (risque modéré)"
        else:
            return True, f"✅ Santé: Health factor {health_factor:.2f} ≥ 2 (sain)"

