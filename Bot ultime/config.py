#!/usr/bin/env python3
"""
Gestion centralisée de la configuration avec variables d'environnement
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration Supabase
SUPABASE_HOST = os.getenv('SUPABASE_HOST', 'db.jlqdkbdmjuqjqhesxvjg.supabase.co')
SUPABASE_PORT = int(os.getenv('SUPABASE_PORT', '5432'))
SUPABASE_DB = os.getenv('SUPABASE_DB', 'postgres')
SUPABASE_USER = os.getenv('SUPABASE_USER', 'postgres')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD')

# Lighter Configuration
LIGHTER_PRIVATE_KEY = os.getenv('LIGHTER_PRIVATE_KEY')
LIGHTER_API_KEY_INDEX = int(os.getenv('LIGHTER_API_KEY_INDEX', '0'))
LIGHTER_ACCOUNT_INDEX = int(os.getenv('LIGHTER_ACCOUNT_INDEX', '0'))

# Paradex Configuration
PARADEX_L2_PRIVATE_KEY = os.getenv('PARADEX_L2_PRIVATE_KEY')
PARADEX_L1_ADDRESS = os.getenv('PARADEX_L1_ADDRESS')

# Web Server
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', '8080'))

# Validation des variables critiques
def validate_config():
    """Valide que toutes les variables critiques sont définies"""
    required_vars = {
        'SUPABASE_PASSWORD': SUPABASE_PASSWORD,
        'LIGHTER_PRIVATE_KEY': LIGHTER_PRIVATE_KEY,
        'PARADEX_L2_PRIVATE_KEY': PARADEX_L2_PRIVATE_KEY,
        'PARADEX_L1_ADDRESS': PARADEX_L1_ADDRESS,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}\n"
            f"Créez un fichier .env basé sur .env.example"
        )
    
    return True

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration validée avec succès")
    except ValueError as e:
        print(str(e))
        exit(1)

