#!/usr/bin/env python3
"""
Stratégie d'arbitrage basée sur le z-score du spread
avec pondération exponentielle pour les prix récents
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from logger import setup_logger

logger = setup_logger("arbitrage_strategy")

@dataclass
class StrategyParams:
    """Paramètres de la stratégie"""
    entry_z: float = 1.0  # Seuil d'entrée (z-score)
    exit_z: float = 0.5   # Seuil de sortie (z-score)
    stop_z: float = 4.0   # Stop loss (z-score)
    window: int = 60      # Fenêtre glissante (observations)
    min_duration_s: int = 4  # Durée minimale de confirmation (secondes)
    max_hold: int = 240   # Durée maximale de position (observations)
    decay_factor: float = 0.95  # Facteur de décroissance exponentielle (0.95 = les prix récents ont plus de poids)

@dataclass
class Trade:
    """Représente un trade"""
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_z: float
    exit_z: Optional[float]
    direction: str  # 'long_spread' ou 'short_spread'
    entry_spread: float
    exit_spread: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    duration_obs: int
    status: str  # 'open', 'closed', 'stopped'

class ArbitrageStrategy:
    """Stratégie d'arbitrage basée sur le z-score"""
    
    def __init__(self, params: StrategyParams):
        self.params = params
        self.trades: List[Trade] = []
        self.current_position: Optional[Trade] = None
        # Variables pour validation des entrées
        self.signal_start_time: Optional[datetime] = None  # Timestamp du début du signal d'entrée
        self.signal_direction: Optional[str] = None  # Direction du signal d'entrée actuel
        # Variables pour validation des sorties
        self.exit_signal_start_time: Optional[datetime] = None  # Timestamp du début du signal de sortie
        self.exit_signal_reason: Optional[str] = None  # Raison du signal de sortie
        
    def calculate_exponential_weights(self, n: int) -> np.ndarray:
        """
        Calcule les poids exponentiels pour les n dernières observations
        Les observations récentes ont plus de poids
        """
        weights = np.array([self.params.decay_factor ** (n - 1 - i) for i in range(n)])
        return weights / weights.sum()  # Normaliser pour que la somme = 1
    
    def calculate_weighted_mean_std(self, values: np.ndarray) -> Tuple[float, float]:
        """
        Calcule la moyenne et l'écart-type pondérés exponentiellement
        """
        if len(values) == 0:
            return 0.0, 1.0
        
        n = len(values)
        weights = self.calculate_exponential_weights(n)
        
        # Moyenne pondérée
        weighted_mean = np.average(values, weights=weights)
        
        # Écart-type pondéré
        variance = np.average((values - weighted_mean) ** 2, weights=weights)
        weighted_std = np.sqrt(variance)
        
        # Éviter la division par zéro
        if weighted_std < 1e-10:
            weighted_std = 1.0
        
        return weighted_mean, weighted_std
    
    def calculate_z_score(self, current_spread: float, spread_history: np.ndarray) -> float:
        """
        Calcule le z-score du spread actuel par rapport à l'historique
        avec pondération exponentielle
        """
        if len(spread_history) < 2:
            return 0.0
        
        # Utiliser la fenêtre glissante
        window_size = min(self.params.window, len(spread_history))
        recent_spreads = spread_history[-window_size:]
        
        # Calculer moyenne et écart-type pondérés
        mean, std = self.calculate_weighted_mean_std(recent_spreads)
        
        # Calculer z-score
        z_score = (current_spread - mean) / std
        
        return z_score
    
    def should_enter_position(self, z_score: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit entrer en position
        Le signal doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des gros traders
        """
        # Vérifier qu'on n'a pas déjà une position
        if self.current_position is not None:
            return False, ""
        
        # Déterminer la direction du signal actuel
        current_direction = None
        if z_score >= self.params.entry_z:
            current_direction = 'short_spread'
        elif z_score <= -self.params.entry_z:
            current_direction = 'long_spread'
        
        # Si le signal est valide
        if current_direction is not None:
            # Si c'est le même signal que précédemment
            if self.signal_direction == current_direction and self.signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé pendant assez longtemps
                    return True, current_direction
            else:
                # Nouveau signal ou changement de direction
                self.signal_start_time = current_time
                self.signal_direction = current_direction
        else:
            # Signal n'est plus valide (z-score en dessous du seuil)
            # Réinitialiser
            self.signal_start_time = None
            self.signal_direction = None
        
        return False, ""
    
    def should_exit_position(self, z_score: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit sortir de position
        Le signal de sortie doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des fluctuations temporaires
        """
        if self.current_position is None:
            return False, ""
        
        # Déterminer la raison potentielle de sortie
        current_exit_reason = None
        
        # Vérifier stop loss
        if self.current_position.direction == 'short_spread':
            if z_score >= self.params.stop_z:
                current_exit_reason = "stop_loss"
            # Sortie normale : z-score revient vers zéro
            elif z_score <= self.params.exit_z:
                current_exit_reason = "normal_exit"
        else:  # long_spread
            if z_score <= -self.params.stop_z:
                current_exit_reason = "stop_loss"
            # Sortie normale : z-score revient vers zéro
            elif z_score >= -self.params.exit_z:
                current_exit_reason = "normal_exit"
        
        # Vérifier durée maximale (pas de validation de 4 secondes pour max_duration)
        duration = len([t for t in self.trades if t.status == 'open']) if self.current_position else 0
        if duration >= self.params.max_hold:
            # Réinitialiser le signal de sortie car on sort pour max_duration
            self.exit_signal_start_time = None
            self.exit_signal_reason = None
            # Pour max_duration, pas de validation de 4 secondes, donc durée = 0
            self._last_exit_signal_duration = 0
            return True, "max_duration"
        
        # Si un signal de sortie est détecté
        if current_exit_reason is not None:
            # Si c'est le même signal que précédemment
            if self.exit_signal_reason == current_exit_reason and self.exit_signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.exit_signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé pendant assez longtemps
                    # Stocker la durée avant de réinitialiser
                    validated_duration = duration_seconds
                    # Réinitialiser avant de retourner
                    self.exit_signal_start_time = None
                    self.exit_signal_reason = None
                    # Stocker la durée dans un attribut temporaire pour exit_position
                    self._last_exit_signal_duration = validated_duration
                    return True, current_exit_reason
            else:
                # Nouveau signal de sortie ou changement de raison
                self.exit_signal_start_time = current_time
                self.exit_signal_reason = current_exit_reason
        else:
            # Signal de sortie n'est plus valide (z-score ne correspond plus aux critères)
            # Réinitialiser
            self.exit_signal_start_time = None
            self.exit_signal_reason = None
        
        return False, ""
    
    def enter_position(self, z_score: float, spread: float, timestamp: datetime, 
                      spread_PL: float, spread_LP: float):
        """Ouvre une nouvelle position"""
        direction = 'short_spread' if z_score > 0 else 'long_spread'
        
        # Calculer la durée du signal AVANT de réinitialiser
        signal_duration = (timestamp - self.signal_start_time).total_seconds() if self.signal_start_time else 0
        
        # Stocker les spreads exploitables à l'entrée
        entry_spread_PL = spread_PL
        entry_spread_LP = spread_LP
        
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            entry_z=z_score,
            exit_z=None,
            direction=direction,
            entry_spread=spread,  # Spread net pour référence
            exit_spread=None,
            pnl=None,
            pnl_percent=None,
            duration_obs=0,
            status='open'
        )
        
        # Stocker les spreads exploitables dans un attribut personnalisé
        trade.entry_spread_PL = entry_spread_PL
        trade.entry_spread_LP = entry_spread_LP
        
        self.current_position = trade
        self.trades.append(trade)
        
        spread_value = spread_PL if direction == 'short_spread' else spread_LP
        logger.info(f"📈 Entrée en position: {direction} | z={z_score:.2f} | spread_net={spread:.2f} | spread_exploitable={spread_value:.2f} | signal_validé_pendant={signal_duration:.1f}s")
        
        # Réinitialiser le signal APRÈS avoir loggé
        self.signal_start_time = None
        self.signal_direction = None
    
    def exit_position(self, z_score: float, spread: float, timestamp: datetime, reason: str, 
                      spread_PL: float, spread_LP: float, entry_spread_PL: float, entry_spread_LP: float):
        """
        Ferme la position actuelle
        spread_PL et spread_LP sont les spreads exploitables actuels
        entry_spread_PL et entry_spread_LP sont les spreads exploitables à l'entrée
        """
        if self.current_position is None:
            return
        
        # Récupérer la durée du signal de sortie (stockée par should_exit_position)
        exit_signal_duration = getattr(self, '_last_exit_signal_duration', 0)
        # Nettoyer l'attribut temporaire
        if hasattr(self, '_last_exit_signal_duration'):
            delattr(self, '_last_exit_signal_duration')
        
        # Calculer PnL basé sur les spreads exploitables réels
        if self.current_position.direction == 'short_spread':
            # Short spread = vendre Paradex, acheter Lighter
            # On utilise spread_PL : bid_paradex - ask_lighter
            # Profit si spread_PL diminue (on vendait plus cher, on achète moins cher)
            pnl = entry_spread_PL - spread_PL
        else:  # long_spread
            # Long spread = acheter Paradex, vendre Lighter
            # On utilise spread_LP : bid_lighter - ask_paradex
            # Profit si spread_LP diminue (on vendait Lighter plus cher, on achète Paradex moins cher)
            pnl = entry_spread_LP - spread_LP
        
        # PnL en pourcentage basé sur le spread initial
        entry_spread_value = entry_spread_PL if self.current_position.direction == 'short_spread' else entry_spread_LP
        pnl_percent = (pnl / abs(entry_spread_value)) * 100 if entry_spread_value != 0 else 0
        
        # Mettre à jour le trade
        self.current_position.exit_time = timestamp
        self.current_position.exit_z = z_score
        self.current_position.exit_spread = spread
        self.current_position.pnl = pnl
        self.current_position.pnl_percent = pnl_percent
        self.current_position.duration_obs = len([t for t in self.trades if t.status == 'open'])
        self.current_position.status = 'stopped' if reason == 'stop_loss' else 'closed'
        
        logger.info(f"📉 Sortie de position: {reason} | z={z_score:.2f} | spread={spread:.2f} | PnL={pnl:.2f} ({pnl_percent:.2f}%) | signal_validé_pendant={exit_signal_duration:.1f}s")
        
        # Réinitialiser les variables de sortie APRÈS avoir loggé
        self.exit_signal_start_time = None
        self.exit_signal_reason = None
        self.current_position = None
    
    def process_tick(self, spread: float, timestamp: datetime, spread_history: np.ndarray,
                    spread_PL: float, spread_LP: float):
        """Traite un nouveau tick de données"""
        # Calculer z-score
        z_score = self.calculate_z_score(spread, spread_history)
        
        # Vérifier sortie de position
        if self.current_position is not None:
            should_exit, reason = self.should_exit_position(z_score, timestamp)
            if should_exit:
                entry_spread_PL = getattr(self.current_position, 'entry_spread_PL', spread_PL)
                entry_spread_LP = getattr(self.current_position, 'entry_spread_LP', spread_LP)
                self.exit_position(z_score, spread, timestamp, reason,
                                 spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
        
        # Vérifier entrée en position
        if self.current_position is None:
            should_enter, direction = self.should_enter_position(z_score, timestamp)
            if should_enter:
                self.enter_position(z_score, spread, timestamp, spread_PL, spread_LP)
        
        # Mettre à jour la durée des positions ouvertes
        if self.current_position is not None:
            self.current_position.duration_obs += 1
    
    def get_performance_stats(self) -> Dict:
        """Calcule les statistiques de performance"""
        closed_trades = [t for t in self.trades if t.status in ['closed', 'stopped']]
        
        if len(closed_trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'win_rate': 0.0,
                'avg_duration': 0.0
            }
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
        winning_trades = [t for t in closed_trades if t.pnl is not None and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl is not None and t.pnl <= 0]
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(closed_trades) if closed_trades else 0.0,
            'win_rate': len(winning_trades) / len(closed_trades) if closed_trades else 0.0,
            'avg_duration_obs': np.mean([t.duration_obs for t in closed_trades]) if closed_trades else 0.0,
            'avg_duration_seconds': np.mean([getattr(t, 'duration_seconds', 0) for t in closed_trades]) if closed_trades else 0.0,
            'max_profit': max([t.pnl for t in closed_trades if t.pnl is not None], default=0.0),
            'max_loss': min([t.pnl for t in closed_trades if t.pnl is not None], default=0.0)
        }


Stratégie d'arbitrage basée sur le z-score du spread
avec pondération exponentielle pour les prix récents
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from logger import setup_logger

logger = setup_logger("arbitrage_strategy")

@dataclass
class StrategyParams:
    """Paramètres de la stratégie"""
    entry_z: float = 1.0  # Seuil d'entrée (z-score)
    exit_z: float = 0.5   # Seuil de sortie (z-score)
    stop_z: float = 4.0   # Stop loss (z-score)
    window: int = 60      # Fenêtre glissante (observations)
    min_duration_s: int = 4  # Durée minimale de confirmation (secondes)
    max_hold: int = 240   # Durée maximale de position (observations)
    decay_factor: float = 0.95  # Facteur de décroissance exponentielle (0.95 = les prix récents ont plus de poids)

@dataclass
class Trade:
    """Représente un trade"""
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_z: float
    exit_z: Optional[float]
    direction: str  # 'long_spread' ou 'short_spread'
    entry_spread: float
    exit_spread: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    duration_obs: int
    status: str  # 'open', 'closed', 'stopped'

class ArbitrageStrategy:
    """Stratégie d'arbitrage basée sur le z-score"""
    
    def __init__(self, params: StrategyParams):
        self.params = params
        self.trades: List[Trade] = []
        self.current_position: Optional[Trade] = None
        # Variables pour validation des entrées
        self.signal_start_time: Optional[datetime] = None  # Timestamp du début du signal d'entrée
        self.signal_direction: Optional[str] = None  # Direction du signal d'entrée actuel
        # Variables pour validation des sorties
        self.exit_signal_start_time: Optional[datetime] = None  # Timestamp du début du signal de sortie
        self.exit_signal_reason: Optional[str] = None  # Raison du signal de sortie
        
    def calculate_exponential_weights(self, n: int) -> np.ndarray:
        """
        Calcule les poids exponentiels pour les n dernières observations
        Les observations récentes ont plus de poids
        """
        weights = np.array([self.params.decay_factor ** (n - 1 - i) for i in range(n)])
        return weights / weights.sum()  # Normaliser pour que la somme = 1
    
    def calculate_weighted_mean_std(self, values: np.ndarray) -> Tuple[float, float]:
        """
        Calcule la moyenne et l'écart-type pondérés exponentiellement
        """
        if len(values) == 0:
            return 0.0, 1.0
        
        n = len(values)
        weights = self.calculate_exponential_weights(n)
        
        # Moyenne pondérée
        weighted_mean = np.average(values, weights=weights)
        
        # Écart-type pondéré
        variance = np.average((values - weighted_mean) ** 2, weights=weights)
        weighted_std = np.sqrt(variance)
        
        # Éviter la division par zéro
        if weighted_std < 1e-10:
            weighted_std = 1.0
        
        return weighted_mean, weighted_std
    
    def calculate_z_score(self, current_spread: float, spread_history: np.ndarray) -> float:
        """
        Calcule le z-score du spread actuel par rapport à l'historique
        avec pondération exponentielle
        """
        if len(spread_history) < 2:
            return 0.0
        
        # Utiliser la fenêtre glissante
        window_size = min(self.params.window, len(spread_history))
        recent_spreads = spread_history[-window_size:]
        
        # Calculer moyenne et écart-type pondérés
        mean, std = self.calculate_weighted_mean_std(recent_spreads)
        
        # Calculer z-score
        z_score = (current_spread - mean) / std
        
        return z_score
    
    def should_enter_position(self, z_score: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit entrer en position
        Le signal doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des gros traders
        """
        # Vérifier qu'on n'a pas déjà une position
        if self.current_position is not None:
            return False, ""
        
        # Déterminer la direction du signal actuel
        current_direction = None
        if z_score >= self.params.entry_z:
            current_direction = 'short_spread'
        elif z_score <= -self.params.entry_z:
            current_direction = 'long_spread'
        
        # Si le signal est valide
        if current_direction is not None:
            # Si c'est le même signal que précédemment
            if self.signal_direction == current_direction and self.signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé pendant assez longtemps
                    return True, current_direction
            else:
                # Nouveau signal ou changement de direction
                self.signal_start_time = current_time
                self.signal_direction = current_direction
        else:
            # Signal n'est plus valide (z-score en dessous du seuil)
            # Réinitialiser
            self.signal_start_time = None
            self.signal_direction = None
        
        return False, ""
    
    def should_exit_position(self, z_score: float, current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit sortir de position
        Le signal de sortie doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des fluctuations temporaires
        """
        if self.current_position is None:
            return False, ""
        
        # Déterminer la raison potentielle de sortie
        current_exit_reason = None
        
        # Vérifier stop loss
        if self.current_position.direction == 'short_spread':
            if z_score >= self.params.stop_z:
                current_exit_reason = "stop_loss"
            # Sortie normale : z-score revient vers zéro
            elif z_score <= self.params.exit_z:
                current_exit_reason = "normal_exit"
        else:  # long_spread
            if z_score <= -self.params.stop_z:
                current_exit_reason = "stop_loss"
            # Sortie normale : z-score revient vers zéro
            elif z_score >= -self.params.exit_z:
                current_exit_reason = "normal_exit"
        
        # Vérifier durée maximale (pas de validation de 4 secondes pour max_duration)
        duration = len([t for t in self.trades if t.status == 'open']) if self.current_position else 0
        if duration >= self.params.max_hold:
            # Réinitialiser le signal de sortie car on sort pour max_duration
            self.exit_signal_start_time = None
            self.exit_signal_reason = None
            # Pour max_duration, pas de validation de 4 secondes, donc durée = 0
            self._last_exit_signal_duration = 0
            return True, "max_duration"
        
        # Si un signal de sortie est détecté
        if current_exit_reason is not None:
            # Si c'est le même signal que précédemment
            if self.exit_signal_reason == current_exit_reason and self.exit_signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.exit_signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé pendant assez longtemps
                    # Stocker la durée avant de réinitialiser
                    validated_duration = duration_seconds
                    # Réinitialiser avant de retourner
                    self.exit_signal_start_time = None
                    self.exit_signal_reason = None
                    # Stocker la durée dans un attribut temporaire pour exit_position
                    self._last_exit_signal_duration = validated_duration
                    return True, current_exit_reason
            else:
                # Nouveau signal de sortie ou changement de raison
                self.exit_signal_start_time = current_time
                self.exit_signal_reason = current_exit_reason
        else:
            # Signal de sortie n'est plus valide (z-score ne correspond plus aux critères)
            # Réinitialiser
            self.exit_signal_start_time = None
            self.exit_signal_reason = None
        
        return False, ""
    
    def enter_position(self, z_score: float, spread: float, timestamp: datetime, 
                      spread_PL: float, spread_LP: float):
        """Ouvre une nouvelle position"""
        direction = 'short_spread' if z_score > 0 else 'long_spread'
        
        # Calculer la durée du signal AVANT de réinitialiser
        signal_duration = (timestamp - self.signal_start_time).total_seconds() if self.signal_start_time else 0
        
        # Stocker les spreads exploitables à l'entrée
        entry_spread_PL = spread_PL
        entry_spread_LP = spread_LP
        
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            entry_z=z_score,
            exit_z=None,
            direction=direction,
            entry_spread=spread,  # Spread net pour référence
            exit_spread=None,
            pnl=None,
            pnl_percent=None,
            duration_obs=0,
            status='open'
        )
        
        # Stocker les spreads exploitables dans un attribut personnalisé
        trade.entry_spread_PL = entry_spread_PL
        trade.entry_spread_LP = entry_spread_LP
        
        self.current_position = trade
        self.trades.append(trade)
        
        spread_value = spread_PL if direction == 'short_spread' else spread_LP
        logger.info(f"📈 Entrée en position: {direction} | z={z_score:.2f} | spread_net={spread:.2f} | spread_exploitable={spread_value:.2f} | signal_validé_pendant={signal_duration:.1f}s")
        
        # Réinitialiser le signal APRÈS avoir loggé
        self.signal_start_time = None
        self.signal_direction = None
    
    def exit_position(self, z_score: float, spread: float, timestamp: datetime, reason: str, 
                      spread_PL: float, spread_LP: float, entry_spread_PL: float, entry_spread_LP: float):
        """
        Ferme la position actuelle
        spread_PL et spread_LP sont les spreads exploitables actuels
        entry_spread_PL et entry_spread_LP sont les spreads exploitables à l'entrée
        """
        if self.current_position is None:
            return
        
        # Récupérer la durée du signal de sortie (stockée par should_exit_position)
        exit_signal_duration = getattr(self, '_last_exit_signal_duration', 0)
        # Nettoyer l'attribut temporaire
        if hasattr(self, '_last_exit_signal_duration'):
            delattr(self, '_last_exit_signal_duration')
        
        # Calculer PnL basé sur les spreads exploitables réels
        if self.current_position.direction == 'short_spread':
            # Short spread = vendre Paradex, acheter Lighter
            # On utilise spread_PL : bid_paradex - ask_lighter
            # Profit si spread_PL diminue (on vendait plus cher, on achète moins cher)
            pnl = entry_spread_PL - spread_PL
        else:  # long_spread
            # Long spread = acheter Paradex, vendre Lighter
            # On utilise spread_LP : bid_lighter - ask_paradex
            # Profit si spread_LP diminue (on vendait Lighter plus cher, on achète Paradex moins cher)
            pnl = entry_spread_LP - spread_LP
        
        # PnL en pourcentage basé sur le spread initial
        entry_spread_value = entry_spread_PL if self.current_position.direction == 'short_spread' else entry_spread_LP
        pnl_percent = (pnl / abs(entry_spread_value)) * 100 if entry_spread_value != 0 else 0
        
        # Mettre à jour le trade
        self.current_position.exit_time = timestamp
        self.current_position.exit_z = z_score
        self.current_position.exit_spread = spread
        self.current_position.pnl = pnl
        self.current_position.pnl_percent = pnl_percent
        self.current_position.duration_obs = len([t for t in self.trades if t.status == 'open'])
        self.current_position.status = 'stopped' if reason == 'stop_loss' else 'closed'
        
        logger.info(f"📉 Sortie de position: {reason} | z={z_score:.2f} | spread={spread:.2f} | PnL={pnl:.2f} ({pnl_percent:.2f}%) | signal_validé_pendant={exit_signal_duration:.1f}s")
        
        # Réinitialiser les variables de sortie APRÈS avoir loggé
        self.exit_signal_start_time = None
        self.exit_signal_reason = None
        self.current_position = None
    
    def process_tick(self, spread: float, timestamp: datetime, spread_history: np.ndarray,
                    spread_PL: float, spread_LP: float):
        """Traite un nouveau tick de données"""
        # Calculer z-score
        z_score = self.calculate_z_score(spread, spread_history)
        
        # Vérifier sortie de position
        if self.current_position is not None:
            should_exit, reason = self.should_exit_position(z_score, timestamp)
            if should_exit:
                entry_spread_PL = getattr(self.current_position, 'entry_spread_PL', spread_PL)
                entry_spread_LP = getattr(self.current_position, 'entry_spread_LP', spread_LP)
                self.exit_position(z_score, spread, timestamp, reason,
                                 spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
        
        # Vérifier entrée en position
        if self.current_position is None:
            should_enter, direction = self.should_enter_position(z_score, timestamp)
            if should_enter:
                self.enter_position(z_score, spread, timestamp, spread_PL, spread_LP)
        
        # Mettre à jour la durée des positions ouvertes
        if self.current_position is not None:
            self.current_position.duration_obs += 1
    
    def get_performance_stats(self) -> Dict:
        """Calcule les statistiques de performance"""
        closed_trades = [t for t in self.trades if t.status in ['closed', 'stopped']]
        
        if len(closed_trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'win_rate': 0.0,
                'avg_duration': 0.0
            }
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
        winning_trades = [t for t in closed_trades if t.pnl is not None and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl is not None and t.pnl <= 0]
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(closed_trades) if closed_trades else 0.0,
            'win_rate': len(winning_trades) / len(closed_trades) if closed_trades else 0.0,
            'avg_duration_obs': np.mean([t.duration_obs for t in closed_trades]) if closed_trades else 0.0,
            'avg_duration_seconds': np.mean([getattr(t, 'duration_seconds', 0) for t in closed_trades]) if closed_trades else 0.0,
            'max_profit': max([t.pnl for t in closed_trades if t.pnl is not None], default=0.0),
            'max_loss': min([t.pnl for t in closed_trades if t.pnl is not None], default=0.0)
        }

