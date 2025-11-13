#!/usr/bin/env python3
"""
Stratégie d'arbitrage SIMPLE basée sur le spread brut
Sans Z-score, juste comparer le spread à un seuil fixe

Logique:
1. Entrée: spread > entry_spread_threshold pendant 4 secondes
           → Vendre le plus cher, acheter le moins cher
2. Sortie: spread < exit_spread_threshold pendant 4 secondes
3. Hold time minimum: position doit être ouverte au moins min_hold_time secondes

Auteur: Baptiste Cuchet
Date: 2025-11-13
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("arbitrage_strategy_simple")


@dataclass
class StrategyParamsSimple:
    """Paramètres de la stratégie simple"""
    entry_spread: float = 15.0  # Spread minimum pour entrer (en $)
    exit_spread: float = 5.0    # Spread maximum pour sortir (en $)
    min_duration_s: int = 4     # Durée minimale de confirmation du signal (en secondes)
    min_hold_time: int = 10     # Durée minimale de détention de la position (en secondes) - ex: 10s = position ouverte au moins 10 secondes
    max_hold: int = 999999      # Durée maximale de position (en secondes) - DÉSACTIVÉ (999999s = ~11 jours)


@dataclass
class TradeSimple:
    """Représente un trade simple"""
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str  # 'sell_lighter' ou 'sell_paradex'
    entry_spread: float
    exit_spread: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    duration_s: int
    status: str  # 'open', 'closed', 'stopped'


class ArbitrageStrategySimple:
    """
    Stratégie d'arbitrage simple basée sur le spread brut
    """
    
    def __init__(self, params: StrategyParamsSimple):
        self.params = params
        self.current_position: Optional[TradeSimple] = None
        self.trades: List[TradeSimple] = []
        
        # Pour validation des signaux (4 secondes)
        self.signal_start_time: Optional[datetime] = None
        self.signal_direction: Optional[str] = None
        self.exit_signal_start_time: Optional[datetime] = None
        
        # Pour hold time minimum
        self.position_open_time: Optional[datetime] = None
        
        # Attribut temporaire pour stocker la durée de validation du signal de sortie
        self._last_exit_signal_duration: float = 0
        
        logger.info("🤖 Stratégie simple initialisée")
        logger.info(f"   📊 Paramètres:")
        logger.info(f"      Entry spread: ${params.entry_spread}")
        logger.info(f"      Exit spread: ${params.exit_spread}")
        logger.info(f"      Min duration: {params.min_duration_s}s")
        logger.info(f"      Min hold time: {params.min_hold_time}s")
        logger.info(f"      Max hold: {params.max_hold}s")
    
    def calculate_spread(self, lighter_bid: float, lighter_ask: float,
                        paradex_bid: float, paradex_ask: float) -> Tuple[float, str]:
        """
        Calcule le spread exploitable et la direction
        
        Returns:
            spread: Spread absolu (toujours positif)
            direction: 'sell_lighter' ou 'sell_paradex'
        """
        # Spread si on vend Lighter et achète Paradex
        spread_sell_lighter = lighter_bid - paradex_ask
        
        # Spread si on vend Paradex et achète Lighter
        spread_sell_paradex = paradex_bid - lighter_ask
        
        # Prendre le spread le plus favorable (le plus élevé)
        if spread_sell_lighter > spread_sell_paradex:
            return spread_sell_lighter, 'sell_lighter'
        else:
            return spread_sell_paradex, 'sell_paradex'
    
    def should_enter_position(self, spread: float, direction: str, current_time: datetime) -> bool:
        """
        Détermine si on doit entrer en position
        
        Args:
            spread: Spread actuel (positif)
            direction: Direction du spread ('sell_lighter' ou 'sell_paradex')
            current_time: Timestamp actuel
        
        Returns:
            True si on doit entrer, False sinon
        """
        # Vérifier qu'on n'a pas déjà une position
        if self.current_position is not None:
            return False
        
        # Vérifier si le spread est suffisant
        if spread >= self.params.entry_spread:
            # Si c'est la même direction que précédemment
            if self.signal_direction == direction and self.signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé
                    logger.info(f"🎯 Signal d'entrée validé: {direction} | spread=${spread:.2f} | durée={duration_seconds:.1f}s")
                    return True
                else:
                    # Signal en cours de validation
                    logger.debug(f"⏳ Signal en validation: {direction} | spread=${spread:.2f} | durée={duration_seconds:.1f}s/{self.params.min_duration_s}s")
            else:
                # Nouveau signal ou changement de direction
                self.signal_start_time = current_time
                self.signal_direction = direction
                logger.info(f"🔔 Nouveau signal détecté: {direction} | spread=${spread:.2f} | Attente validation ({self.params.min_duration_s}s)")
        else:
            # Signal n'est plus valide
            if self.signal_start_time is not None:
                logger.debug(f"❌ Signal annulé: spread=${spread:.2f} < seuil ${self.params.entry_spread}")
            self.signal_start_time = None
            self.signal_direction = None
        
        return False
    
    def should_exit_position(self, spread: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit sortir de position
        
        Args:
            spread: Spread actuel (positif)
            current_time: Timestamp actuel
        
        Returns:
            (should_exit, reason)
        """
        if self.current_position is None:
            return False, ""
        
        # Vérifier le hold time minimum
        if self.position_open_time is not None:
            hold_duration = (current_time - self.position_open_time).total_seconds()
            if hold_duration < self.params.min_hold_time:
                logger.debug(f"⏱️ Hold time insuffisant: {hold_duration:.1f}s < {self.params.min_hold_time}s")
                return False, ""
        
        # Vérifier durée maximale
        if self.position_open_time is not None:
            duration = (current_time - self.position_open_time).total_seconds()
            if duration >= self.params.max_hold:
                logger.info(f"⏰ Durée maximale atteinte: {duration:.1f}s >= {self.params.max_hold}s")
                self._last_exit_signal_duration = 0
                return True, "max_duration"
        
        # Vérifier si le spread est suffisamment réduit
        if spread <= self.params.exit_spread:
            # Si on a déjà détecté un signal de sortie
            if self.exit_signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.exit_signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé
                    validated_duration = duration_seconds
                    self.exit_signal_start_time = None
                    self._last_exit_signal_duration = validated_duration
                    logger.info(f"✅ Signal de sortie validé: spread=${spread:.2f} | durée={validated_duration:.1f}s")
                    return True, "convergence"
                else:
                    # Signal en cours de validation
                    logger.debug(f"⏳ Signal de sortie en validation: spread=${spread:.2f} | durée={duration_seconds:.1f}s/{self.params.min_duration_s}s")
            else:
                # Nouveau signal de sortie
                self.exit_signal_start_time = current_time
                logger.info(f"🔔 Nouveau signal de sortie: spread=${spread:.2f} | Attente validation ({self.params.min_duration_s}s)")
        else:
            # Signal de sortie n'est plus valide
            self.exit_signal_start_time = None
        
        return False, ""
    
    def enter_position(self, spread: float, direction: str, timestamp: datetime):
        """
        Ouvre une nouvelle position
        
        Args:
            spread: Spread d'entrée
            direction: Direction du trade ('sell_lighter' ou 'sell_paradex')
            timestamp: Timestamp d'entrée
        """
        # Calculer la durée du signal
        signal_duration = (timestamp - self.signal_start_time).total_seconds() if self.signal_start_time else 0
        
        trade = TradeSimple(
            entry_time=timestamp,
            exit_time=None,
            direction=direction,
            entry_spread=spread,
            exit_spread=None,
            pnl=None,
            pnl_percent=None,
            duration_s=0,
            status='open'
        )
        
        self.current_position = trade
        self.trades.append(trade)
        self.position_open_time = timestamp
        
        logger.info(f"📈 Entrée en position: {direction}")
        logger.info(f"   Spread d'entrée: ${spread:.2f}")
        logger.info(f"   Signal validé pendant: {signal_duration:.1f}s")
        
        # Réinitialiser le signal
        self.signal_start_time = None
        self.signal_direction = None
    
    def exit_position(self, spread: float, timestamp: datetime, reason: str):
        """
        Ferme la position actuelle
        
        Args:
            spread: Spread de sortie
            timestamp: Timestamp de sortie
            reason: Raison de sortie
        """
        if self.current_position is None:
            return
        
        # Calculer PnL
        entry_spread = self.current_position.entry_spread
        exit_spread = spread
        
        # PnL = spread capturé à l'entrée - spread de sortie
        # Plus le spread de sortie est petit, meilleur est le PnL
        pnl = entry_spread - exit_spread
        pnl_percent = (pnl / entry_spread) * 100 if entry_spread != 0 else 0
        
        # Calculer durée
        duration_s = (timestamp - self.current_position.entry_time).total_seconds()
        
        # Récupérer la durée de validation du signal de sortie
        exit_signal_duration = getattr(self, '_last_exit_signal_duration', 0)
        if hasattr(self, '_last_exit_signal_duration'):
            delattr(self, '_last_exit_signal_duration')
        
        # Mettre à jour le trade
        self.current_position.exit_time = timestamp
        self.current_position.exit_spread = exit_spread
        self.current_position.pnl = pnl
        self.current_position.pnl_percent = pnl_percent
        self.current_position.duration_s = int(duration_s)
        self.current_position.status = 'stopped' if reason == 'max_duration' else 'closed'
        
        logger.info(f"📉 Sortie de position: {reason}")
        logger.info(f"   Spread de sortie: ${exit_spread:.2f}")
        logger.info(f"   PnL: ${pnl:.2f} ({pnl_percent:.2f}%)")
        logger.info(f"   Durée: {duration_s:.1f}s")
        logger.info(f"   Signal validé pendant: {exit_signal_duration:.1f}s")
        
        # Réinitialiser
        self.exit_signal_start_time = None
        self.position_open_time = None
        self.current_position = None
    
    def process_tick(self, lighter_bid: float, lighter_ask: float,
                    paradex_bid: float, paradex_ask: float, timestamp: datetime):
        """
        Traite un nouveau tick de données
        
        Args:
            lighter_bid: Bid Lighter
            lighter_ask: Ask Lighter
            paradex_bid: Bid Paradex
            paradex_ask: Ask Paradex
            timestamp: Timestamp actuel
        """
        # Calculer le spread et la direction pour l'entrée
        spread, direction = self.calculate_spread(lighter_bid, lighter_ask, paradex_bid, paradex_ask)
        
        # Vérifier sortie de position
        if self.current_position is not None:
            # Pour la sortie, calculer le spread dans la DIRECTION OPPOSÉE à l'entrée
            # (c'est-à-dire le coût pour fermer la position)
            if self.current_position.direction == 'sell_lighter':
                # On avait vendu Lighter et acheté Paradex
                # Pour fermer: acheter Lighter et vendre Paradex
                # Coût de fermeture: paradex_bid - lighter_ask (on reçoit paradex_bid, on paye lighter_ask)
                exit_spread = paradex_bid - lighter_ask
            else:  # sell_paradex
                # On avait vendu Paradex et acheté Lighter
                # Pour fermer: vendre Lighter et acheter Paradex
                # Coût de fermeture: lighter_bid - paradex_ask (on reçoit lighter_bid, on paye paradex_ask)
                exit_spread = lighter_bid - paradex_ask
            
            should_exit, reason = self.should_exit_position(exit_spread, timestamp)
            if should_exit:
                self.exit_position(exit_spread, timestamp, reason)
        
        # Vérifier entrée en position
        if self.current_position is None:
            should_enter = self.should_enter_position(spread, direction, timestamp)
            if should_enter:
                self.enter_position(spread, direction, timestamp)
    
    def get_performance_stats(self) -> dict:
        """
        Retourne les statistiques de performance
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "avg_duration_s": 0
            }
        
        closed_trades = [t for t in self.trades if t.status in ['closed', 'stopped']]
        if not closed_trades:
            return {
                "total_trades": len(self.trades),
                "open_trades": len([t for t in self.trades if t.status == 'open']),
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "avg_duration_s": 0
            }
        
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        avg_pnl = total_pnl / len(closed_trades)
        avg_duration_s = sum(t.duration_s for t in closed_trades) / len(closed_trades)
        
        return {
            "total_trades": len(self.trades),
            "open_trades": len([t for t in self.trades if t.status == 'open']),
            "closed_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_duration_s": int(avg_duration_s)
        }

