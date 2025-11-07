#!/usr/bin/env python3
"""
Bot d'arbitrage simple - Lance Lighter et Paradex simultanément
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime

def run_lighter():
    """Lance le script Lighter avec Python 3.9"""
    print("🚀 [LIGHTER] Démarrage du script Lighter...")
    try:
        result = subprocess.run([
            "/usr/bin/python3", 
            "lighter/lighter_trader.py"
        ], capture_output=True, text=True, cwd=".")
        
        print("✅ [LIGHTER] Script terminé")
        print(f"📊 [LIGHTER] Sortie: {result.stdout[-200:]}")  # Dernières 200 caractères
        if result.stderr:
            print(f"⚠️ [LIGHTER] Erreurs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ [LIGHTER] Erreur: {e}")

def run_paradex():
    """Lance le script Paradex avec Python 3.11"""
    print("🚀 [PARADEX] Démarrage du script Paradex...")
    try:
        result = subprocess.run([
            "python3.11", 
            "paradex/paradex_trader.py"
        ], capture_output=True, text=True, cwd=".")
        
        print("✅ [PARADEX] Script terminé")
        print(f"📊 [PARADEX] Sortie: {result.stdout[-200:]}")  # Dernières 200 caractères
        if result.stderr:
            print(f"⚠️ [PARADEX] Erreurs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ [PARADEX] Erreur: {e}")

async def run_both_async():
    """Lance les deux scripts en parallèle"""
    print("=" * 60)
    print("🤖 BOT D'ARBITRAGE - LIGHTER + PARADEX")
    print("=" * 60)
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Créer les tâches asynchrones
    loop = asyncio.get_event_loop()
    
    # Exécuter les deux scripts en parallèle
    lighter_task = loop.run_in_executor(None, run_lighter)
    paradex_task = loop.run_in_executor(None, run_paradex)
    
    # Attendre que les deux se terminent
    await asyncio.gather(lighter_task, paradex_task)
    
    print("=" * 60)
    print("🏁 ARBITRAGE TERMINÉ")
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def main():
    """Fonction principale"""
    try:
        asyncio.run(run_both_async())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    main()
