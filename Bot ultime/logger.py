#!/usr/bin/env python3
"""
Système de logs détaillé pour le bot d'arbitrage
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Créer le dossier logs s'il n'existe pas
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name, log_level=logging.INFO):
    """
    Configure un logger avec sortie console et fichier
    
    Args:
        name: Nom du logger (ex: 'lighter_trader', 'paradex_trader', 'arbitrage_bot')
        log_level: Niveau de log (default: INFO)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Éviter les doublons de handlers
    if logger.handlers:
        return logger
    
    # Format des logs
    log_format = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour la console (avec couleurs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    
    # Handler pour le fichier avec flush immédiat
    log_filename = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8', delay=False)
    file_handler.setLevel(logging.DEBUG)  # Toujours DEBUG pour les fichiers
    file_handler.setFormatter(log_format)
    
    # Ajouter les handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Forcer le flush après chaque écriture
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    for handler in logger.handlers:
        if hasattr(handler, 'stream') and handler.stream:
            handler.stream.flush()
    
    return logger

def get_log_file_path(name):
    """Retourne le chemin du fichier de log pour un logger donné"""
    return LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

