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
    entry_z: float = 1.0  # Seuil d'entrée (z-score) - Opportunité exceptionnelle
    exit_spread_threshold: float = 6.0  # Seuil de sortie : convergence minimale du spread en $ (sortie rapide)
    stop_z: float = 4.0   # Stop loss (z-score)
    min_spread: float = 12.0  # Spread minimum favorable pour entrer (en $) - Opportunités solides uniquement
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
    
    def calculate_z_scores(self, current_spread_PL: float, current_spread_LP: float,
                          spread_PL_history: np.ndarray, spread_LP_history: np.ndarray) -> Tuple[float, float]:
        """
        Calcule les deux z-scores séparés pour les spreads exploitables
        
        Returns:
            z_score_short: Z-score pour short_spread (basé sur spread_PL)
            z_score_long: Z-score pour long_spread (basé sur spread_LP)
        """
        z_score_short = self.calculate_z_score(current_spread_PL, spread_PL_history)
        z_score_long = self.calculate_z_score(current_spread_LP, spread_LP_history)
        
        return z_score_short, z_score_long
    
    def should_enter_position(self, z_score_short: float, z_score_long: float, 
                             current_spread_PL: float, current_spread_LP: float,
                             current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit entrer en position en utilisant les 2 Z-scores séparés
        z_score_short: basé sur spread_PL (pour détecter short_spread)
        z_score_long: basé sur spread_LP (pour détecter long_spread)
        current_spread_PL: spread actuel Paradex-Lighter
        current_spread_LP: spread actuel Lighter-Paradex
        
        STRATÉGIE D'ARBITRAGE PUR:
        - N'entre QUE si le spread est FAVORABLE (positif = on gagne de l'argent)
        - ET si le Z-score indique une opportunité exceptionnelle
        
        Le signal doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des gros traders
        """
        # Vérifier qu'on n'a pas déjà une position
        if self.current_position is not None:
            return False, ""
        
        # Déterminer la direction du signal actuel
        current_direction = None
        active_z_score = None
        
        # Pour short_spread: VENDRE Paradex (bid) + ACHETER Lighter (ask)
        # Gain immédiat = spread_PL = Paradex_bid - Lighter_ask
        # N'entrer QUE si spread_PL > min_spread (Paradex plus cher)
        # ET Z-score élevé (opportunité exceptionnelle)
        if z_score_short >= self.params.entry_z and current_spread_PL >= self.params.min_spread:
            current_direction = 'short_spread'
            active_z_score = z_score_short
        # Pour long_spread: VENDRE Lighter (bid) + ACHETER Paradex (ask)
        # Gain immédiat = spread_LP = Lighter_bid - Paradex_ask
        # N'entrer QUE si spread_LP > min_spread (Lighter plus cher)
        # ET Z-score élevé (opportunité exceptionnelle)
        elif z_score_long >= self.params.entry_z and current_spread_LP >= self.params.min_spread:
            current_direction = 'long_spread'
            active_z_score = z_score_long
        
        # Si le signal est valide
        if current_direction is not None:
            # Si c'est le même signal que précédemment
            if self.signal_direction == current_direction and self.signal_start_time is not None:
                # Vérifier si le signal dure depuis au moins min_duration_s secondes
                duration_seconds = (current_time - self.signal_start_time).total_seconds()
                
                if duration_seconds >= self.params.min_duration_s:
                    # Signal confirmé pendant assez longtemps
                    spread_value = current_spread_PL if current_direction == 'short_spread' else current_spread_LP
                    logger.info(f"🎯 Signal d'entrée validé: {current_direction} | z={active_z_score:.2f} | spread_favorable={spread_value:.2f}$ | durée={duration_seconds:.1f}s")
                    return True, current_direction
                else:
                    # Signal en cours de validation
                    logger.debug(f"⏳ Signal en validation: {current_direction} | z={active_z_score:.2f} | durée={duration_seconds:.1f}s/{self.params.min_duration_s}s")
            else:
                # Nouveau signal ou changement de direction
                self.signal_start_time = current_time
                self.signal_direction = current_direction
                spread_value = current_spread_PL if current_direction == 'short_spread' else current_spread_LP
                logger.info(f"🔔 Nouveau signal détecté: {current_direction} | z={active_z_score:.2f} | spread_favorable={spread_value:.2f}$ | Attente validation ({self.params.min_duration_s}s)")
        else:
            # Signal n'est plus valide (z-score en dessous du seuil)
            # Réinitialiser seulement si on avait un signal en cours
            if self.signal_start_time is not None:
                logger.debug(f"❌ Signal annulé: z_short={z_score_short:.2f}, z_long={z_score_long:.2f} < seuil {self.params.entry_z}")
            self.signal_start_time = None
            self.signal_direction = None
        
        return False, ""
    
    def should_exit_position(self, z_score_short: float, z_score_long: float, 
                            current_spread_PL: float, current_spread_LP: float,
                            current_time: datetime) -> Tuple[bool, str]:
        """
        Détermine si on doit sortir de position basé sur la CONVERGENCE DU SPREAD en dollars
        
        Pour short_spread: surveille spread_PL
        Pour long_spread: surveille spread_LP
        
        Sortie si:
        - CONVERGENCE: Le spread a convergé d'au moins exit_spread_threshold dollars par rapport à l'entrée
        - INVERSION: Le spread s'est inversé (changement de signe)
        - STOP LOSS: Z-score dépasse stop_z (spread continue de diverger)
        
        Le signal de sortie doit être maintenu pendant min_duration_s secondes consécutives
        pour éviter les faux signaux causés par des fluctuations temporaires
        """
        if self.current_position is None:
            return False, ""
        
        # Récupérer les spreads d'entrée et actuels selon la direction
        if self.current_position.direction == 'short_spread':
            entry_spread = getattr(self.current_position, 'entry_spread_PL', self.current_position.entry_spread)
            current_spread = current_spread_PL
            z_score = z_score_short
        else:  # long_spread
            entry_spread = getattr(self.current_position, 'entry_spread_LP', self.current_position.entry_spread)
            current_spread = current_spread_LP
            z_score = z_score_long
        
        # INVERSION: Sortie immédiate si le spread s'est inversé (changement de signe)
        # Pour short_spread: entry négatif, si current devient positif = inversion
        # Pour long_spread: entry positif, si current devient négatif = inversion
        if (entry_spread < 0 and current_spread > 0) or (entry_spread > 0 and current_spread < 0):
            logger.info(f"🔄 Inversion détectée: entry_spread={entry_spread:.2f}, current_spread={current_spread:.2f}")
            return True, "inversion"
        
        # Déterminer la raison potentielle de sortie
        current_exit_reason = None
        
        # Vérifier stop loss (z-score trop élevé = spread continue de diverger)
        if z_score >= self.params.stop_z:
            current_exit_reason = "stop_loss"
        else:
            # CONVERGENCE: Vérifier si le spread a suffisamment convergé
            # Convergence = réduction de l'écart absolu du spread
            spread_convergence = abs(entry_spread) - abs(current_spread)
            
            if spread_convergence >= self.params.exit_spread_threshold:
                logger.debug(f"✅ Convergence détectée: {spread_convergence:.2f}$ >= {self.params.exit_spread_threshold}$ (entry={entry_spread:.2f}, current={current_spread:.2f})")
                current_exit_reason = "convergence"
        
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
                    logger.info(f"✅ Signal de sortie validé: {current_exit_reason} | z={z_score:.2f} | durée={validated_duration:.1f}s")
                    return True, current_exit_reason
                else:
                    # Signal en cours de validation
                    logger.debug(f"⏳ Signal de sortie en validation: {current_exit_reason} | z={z_score:.2f} | durée={duration_seconds:.1f}s/{self.params.min_duration_s}s")
            else:
                # Nouveau signal de sortie ou changement de raison
                self.exit_signal_start_time = current_time
                self.exit_signal_reason = current_exit_reason
                logger.info(f"🔔 Nouveau signal de sortie: {current_exit_reason} | z={z_score:.2f} | Attente validation ({self.params.min_duration_s}s)")
        else:
            # Signal de sortie n'est plus valide (z-score ne correspond plus aux critères)
            # Réinitialiser
            self.exit_signal_start_time = None
            self.exit_signal_reason = None
        
        return False, ""
    
    def enter_position(self, z_score_short: float, z_score_long: float, direction: str,
                      timestamp: datetime, spread_PL: float, spread_LP: float):
        """
        Ouvre une nouvelle position
        z_score_short: Z-score basé sur spread_PL
        z_score_long: Z-score basé sur spread_LP
        direction: 'short_spread' ou 'long_spread'
        """
        # Calculer la durée du signal AVANT de réinitialiser
        signal_duration = (timestamp - self.signal_start_time).total_seconds() if self.signal_start_time else 0
        
        # Sélectionner le z-score correspondant à la direction
        z_score = z_score_short if direction == 'short_spread' else z_score_long
        
        # Stocker les spreads exploitables à l'entrée
        entry_spread_PL = spread_PL
        entry_spread_LP = spread_LP
        
        # Stocker le spread exploitable utilisé pour l'entrée
        entry_spread_value = spread_PL if direction == 'short_spread' else spread_LP
        
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            entry_z=z_score,
            exit_z=None,
            direction=direction,
            entry_spread=entry_spread_value,  # Spread exploitable réel (plus besoin de spread_net)
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
        
        logger.info(f"📈 Entrée en position: {direction}")
        logger.info(f"   Z-score utilisé: {z_score:.2f} (z_short={z_score_short:.2f}, z_long={z_score_long:.2f})")
        logger.info(f"   Spread exploitable (entrée): {entry_spread_value:.2f}$")
        logger.info(f"   Signal validé pendant: {signal_duration:.1f}s")
        
        # Réinitialiser le signal APRÈS avoir loggé
        self.signal_start_time = None
        self.signal_direction = None
    
    def exit_position(self, z_score_short: float, z_score_long: float, timestamp: datetime, reason: str, 
                      spread_PL: float, spread_LP: float, entry_spread_PL: float, entry_spread_LP: float):
        """
        Ferme la position actuelle
        z_score_short: Z-score actuel basé sur spread_PL
        z_score_long: Z-score actuel basé sur spread_LP
        spread_PL et spread_LP sont les spreads exploitables actuels
        entry_spread_PL et entry_spread_LP sont les spreads exploitables à l'entrée
        """
        if self.current_position is None:
            return
        
        # Sélectionner le z-score correspondant à la direction
        z_score = z_score_short if self.current_position.direction == 'short_spread' else z_score_long
        exit_spread_value = spread_PL if self.current_position.direction == 'short_spread' else spread_LP
        
        # Récupérer la durée du signal de sortie (stockée par should_exit_position)
        exit_signal_duration = getattr(self, '_last_exit_signal_duration', 0)
        # Nettoyer l'attribut temporaire
        if hasattr(self, '_last_exit_signal_duration'):
            delattr(self, '_last_exit_signal_duration')
        
        # Calculer PnL basé sur les spreads exploitables réels
        # IMPORTANT: Le PnL est la SOMME des cash-flows d'entrée et de sortie
        if self.current_position.direction == 'short_spread':
            # Short spread = SELL Paradex (bid), BUY Lighter (ask)
            # Entrée : spread_PL = paradex_bid - lighter_ask (NÉGATIF = on paye)
            # Sortie : on fait l'INVERSE = SELL Lighter (bid), BUY Paradex (ask)
            # Sortie : spread_LP = lighter_bid - paradex_ask (POSITIF = on reçoit)
            # 
            # PnL = cash-flow entrée + cash-flow sortie
            # PnL = entry_spread_PL + exit_spread_LP
            pnl = entry_spread_PL + spread_LP
        else:  # long_spread
            # Long spread = SELL Lighter (bid), BUY Paradex (ask)
            # Entrée : spread_LP = lighter_bid - paradex_ask
            # Sortie : on fait l'INVERSE = SELL Paradex (bid), BUY Lighter (ask)
            # Sortie : spread_PL = paradex_bid - lighter_ask
            # 
            # PnL = entry_spread_LP + exit_spread_PL
            pnl = entry_spread_LP + spread_PL
        
        # PnL en pourcentage basé sur le spread initial
        entry_spread_value = entry_spread_PL if self.current_position.direction == 'short_spread' else entry_spread_LP
        pnl_percent = (pnl / abs(entry_spread_value)) * 100 if entry_spread_value != 0 else 0
        
        # Mettre à jour le trade
        self.current_position.exit_time = timestamp
        self.current_position.exit_z = z_score
        self.current_position.exit_spread = exit_spread_value
        self.current_position.pnl = pnl
        self.current_position.pnl_percent = pnl_percent
        self.current_position.duration_obs = len([t for t in self.trades if t.status == 'open'])
        self.current_position.status = 'stopped' if reason == 'stop_loss' else 'closed'
        
        logger.info(f"📉 Sortie de position: {reason}")
        logger.info(f"   Z-score utilisé: {z_score:.2f} (z_short={z_score_short:.2f}, z_long={z_score_long:.2f})")
        logger.info(f"   Spread exploitable (sortie): {exit_spread_value:.2f}$")
        logger.info(f"   PnL: {pnl:.2f}$ ({pnl_percent:.2f}%)")
        logger.info(f"   Signal validé pendant: {exit_signal_duration:.1f}s")
        
        # Réinitialiser les variables de sortie APRÈS avoir loggé
        self.exit_signal_start_time = None
        self.exit_signal_reason = None
        self.current_position = None
    
    def process_tick(self, timestamp: datetime, 
                    spread_PL: float, spread_LP: float,
                    spread_PL_history: np.ndarray, spread_LP_history: np.ndarray):
        """
        Traite un nouveau tick de données en utilisant les 2 Z-scores séparés
        
        spread_PL: Spread exploitable pour short_spread (paradex_bid - lighter_ask)
        spread_LP: Spread exploitable pour long_spread (lighter_bid - paradex_ask)
        spread_PL_history: Historique de spread_PL
        spread_LP_history: Historique de spread_LP
        """
        # Calculer les 2 z-scores séparés
        z_score_short, z_score_long = self.calculate_z_scores(
            spread_PL, spread_LP, 
            spread_PL_history, spread_LP_history
        )
        
        # Vérifier sortie de position
        if self.current_position is not None:
            should_exit, reason = self.should_exit_position(z_score_short, z_score_long, timestamp)
            if should_exit:
                entry_spread_PL = getattr(self.current_position, 'entry_spread_PL', spread_PL)
                entry_spread_LP = getattr(self.current_position, 'entry_spread_LP', spread_LP)
                self.exit_position(z_score_short, z_score_long, timestamp, reason,
                                 spread_PL, spread_LP, entry_spread_PL, entry_spread_LP)
        
        # Vérifier entrée en position
        if self.current_position is None:
            should_enter, direction = self.should_enter_position(z_score_short, z_score_long, 
                                                                 spread_PL, spread_LP, timestamp)
            if should_enter:
                self.enter_position(z_score_short, z_score_long, direction, timestamp, spread_PL, spread_LP)
        
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

