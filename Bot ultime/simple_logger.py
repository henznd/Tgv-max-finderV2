#!/usr/bin/env python3
"""
Système de logs simplifié avec couleurs pour le bot d'arbitrage
Affiche seulement l'essentiel : Bot lancé, Trade lancé, Trade fermé, PNL
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Créer le dossier logs s'il n'existe pas
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Codes couleur ANSI
class Colors:
    GREEN = '\033[92m'      # Vert - Succès, trades ouverts
    RED = '\033[91m'        # Rouge - Erreurs, PNL négatif
    BLUE = '\033[94m'       # Bleu - Informations importantes
    YELLOW = '\033[93m'     # Jaune - Warnings
    MAGENTA = '\033[95m'    # Magenta - PNL positif
    CYAN = '\033[96m'       # Cyan - Bot lancé
    RESET = '\033[0m'       # Reset
    BOLD = '\033[1m'        # Gras

class SimpleLogger:
    """Logger simplifié avec couleurs"""
    
    def __init__(self, name="arbitrage_bot"):
        self.name = name
        self.log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Créer le logger standard pour le fichier
        self.file_logger = logging.getLogger(f"{name}_file")
        self.file_logger.setLevel(logging.DEBUG)
        
        if not self.file_logger.handlers:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.file_logger.addHandler(file_handler)
    
    def _log(self, message, color="", to_file=True):
        """Log avec couleur en console et fichier"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Console avec couleur
        print(f"{color}{Colors.BOLD}[{timestamp}]{Colors.RESET} {color}{message}{Colors.RESET}")
        
        # Fichier sans couleur
        if to_file:
            self.file_logger.info(message)
    
    def bot_started(self, token, margin, leverage):
        """Bot lancé"""
        message = f"🤖 BOT LANCÉ | Token: {token} | Marge: ${margin} | Levier: {leverage}x"
        self._log(message, Colors.CYAN)
    
    def trade_opened(self, direction, token, amount, entry_price, entry_z):
        """Trade ouvert"""
        direction_fr = "LONG" if "long" in direction else "SHORT"
        message = f"📈 TRADE OUVERT | Direction: {direction_fr} | {amount:.6f} {token} | Prix: ${entry_price:.2f} | Z-score: {entry_z:.2f}"
        self._log(message, Colors.GREEN)
    
    def trade_closed(self, direction, token, exit_price, exit_z, pnl, pnl_percent):
        """Trade fermé"""
        direction_fr = "LONG" if "long" in direction else "SHORT"
        pnl_color = Colors.MAGENTA if pnl >= 0 else Colors.RED
        pnl_sign = "+" if pnl >= 0 else ""
        
        message = f"📉 TRADE FERMÉ | Direction: {direction_fr} | {token} | Prix sortie: ${exit_price:.2f} | Z-score: {exit_z:.2f}"
        self._log(message, Colors.BLUE)
        
        pnl_message = f"💰 PNL: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_percent:.2f}%)"
        self._log(pnl_message, pnl_color)
    
    def error(self, message):
        """Erreur"""
        self._log(f"❌ ERREUR: {message}", Colors.RED)
    
    def warning(self, message):
        """Warning"""
        self._log(f"⚠️ {message}", Colors.YELLOW)
    
    def info(self, message):
        """Information simple (désactivé par défaut, utilisez les méthodes spécifiques)"""
        # On ne log que dans le fichier, pas en console
        self.file_logger.info(message)
    
    def debug(self, message):
        """Debug (seulement dans le fichier)"""
        self.file_logger.debug(message)


def setup_simple_logger(name="arbitrage_bot"):
    """Configure un logger simplifié avec couleurs"""
    return SimpleLogger(name)

