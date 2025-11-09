#!/usr/bin/env python3
"""
Backtest de la stratégie d'arbitrage sur données historiques
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import sys
from arbitrage_strategy import ArbitrageStrategy, StrategyParams
from logger import setup_logger

logger = setup_logger("backtest")

def load_price_data(filepath: str) -> pd.DataFrame:
    """Charge les données de prix depuis le CSV"""
    logger.info(f"📂 Chargement des données depuis {filepath}")
    
    # Lire le CSV (séparateur = ;)
    df = pd.read_csv(filepath, sep=';')
    
    # Convertir created_at en datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Trier par timestamp
    df = df.sort_values('created_at').reset_index(drop=True)
    
    logger.info(f"   ✅ {len(df)} lignes chargées")
    logger.info(f"   📅 Période: {df['created_at'].min()} → {df['created_at'].max()}")
    logger.info(f"   🪙 Token: {df['token'].unique()}")
    logger.info(f"   📊 Exchanges: {df['exchange'].unique()}")
    
    return df

def prepare_spread_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare les données de spread
    Calcule les spreads exploitables réels :
    - spread_PL = bid_paradex - ask_lighter (vendre Paradex / acheter Lighter)
    - spread_LP = bid_lighter - ask_paradex (vendre Lighter / acheter Paradex)
    """
    logger.info("📊 Préparation des données de spread...")
    
    # Grouper par timestamp pour avoir les paires lighter/paradex
    spread_data = []
    
    for timestamp in df['created_at'].unique():
        tick_data = df[df['created_at'] == timestamp]
        
        lighter = tick_data[tick_data['exchange'] == 'lighter']
        paradex = tick_data[tick_data['exchange'] == 'paradex']
        
        if len(lighter) > 0 and len(paradex) > 0:
            lighter_row = lighter.iloc[0]
            paradex_row = paradex.iloc[0]
            
            # Spreads exploitables réels
            spread_PL = paradex_row['bid'] - lighter_row['ask']  # Vendre Paradex, acheter Lighter (short spread)
            spread_LP = lighter_row['bid'] - paradex_row['ask']  # Vendre Lighter, acheter Paradex (long spread)
            
            # Spread net pour le z-score : différence entre les prix moyens
            # spread = prix_paradex - prix_lighter (positif si Paradex > Lighter)
            spread_net = paradex_row['mid'] - lighter_row['mid']
            
            spread_data.append({
                'timestamp': timestamp,
                'lighter_bid': lighter_row['bid'],
                'lighter_ask': lighter_row['ask'],
                'lighter_mid': lighter_row['mid'],
                'paradex_bid': paradex_row['bid'],
                'paradex_ask': paradex_row['ask'],
                'paradex_mid': paradex_row['mid'],
                'spread_PL': spread_PL,  # Spread exploitable pour short (vendre P, acheter L)
                'spread_LP': spread_LP,  # Spread exploitable pour long (vendre L, acheter P)
                'spread': spread_net,  # Spread net pour le z-score (mid prices)
            })
    
    spread_df = pd.DataFrame(spread_data)
    spread_df = spread_df.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"   ✅ {len(spread_df)} observations de spread préparées")
    logger.info(f"   📊 Spread moyen: {spread_df['spread'].mean():.2f}")
    logger.info(f"   📊 Spread min: {spread_df['spread'].min():.2f}")
    logger.info(f"   📊 Spread max: {spread_df['spread'].max():.2f}")
    
    return spread_df

def run_backtest(spread_df: pd.DataFrame, params: StrategyParams) -> Dict:
    """
    Exécute le backtest avec les paramètres donnés
    """
    logger.info("🚀 Démarrage du backtest...")
    logger.info(f"   📋 Paramètres:")
    logger.info(f"      entry_z: {params.entry_z}")
    logger.info(f"      exit_z: {params.exit_z}")
    logger.info(f"      stop_z: {params.stop_z}")
    logger.info(f"      window: {params.window}")
    logger.info(f"      min_duration_s: {params.min_duration_s}")
    logger.info(f"      decay_factor: {params.decay_factor}")
    logger.info("")
    
    strategy = ArbitrageStrategy(params)
    spread_history = np.array([])
    
    # Traiter chaque tick
    prev_timestamp = None
    for idx, row in spread_df.iterrows():
        timestamp = row['timestamp']
        spread = row['spread']
        spread_PL = row['spread_PL']
        spread_LP = row['spread_LP']
        
        # Ajouter au historique
        spread_history = np.append(spread_history, spread)
        
        # Traiter le tick
        strategy.process_tick(spread, timestamp, spread_history, spread_PL, spread_LP)
        
        # Mettre à jour la durée réelle de la position ouverte (en secondes)
        if strategy.current_position is not None:
            if not hasattr(strategy.current_position, 'duration_seconds'):
                strategy.current_position.duration_seconds = 0
            if prev_timestamp is not None:
                time_diff = (timestamp - prev_timestamp).total_seconds()
                strategy.current_position.duration_seconds += time_diff
            else:
                # Première observation, initialiser à 0
                strategy.current_position.duration_seconds = 0
        
        prev_timestamp = timestamp
        
        # Log périodique
        if (idx + 1) % 1000 == 0:
            logger.info(f"   📊 Traité {idx + 1}/{len(spread_df)} observations...")
    
    # Fermer les positions ouvertes à la fin
    if strategy.current_position is not None:
        last_row = spread_df.iloc[-1]
        last_spread = last_row['spread']
        last_timestamp = last_row['timestamp']
        last_spread_PL = last_row['spread_PL']
        last_spread_LP = last_row['spread_LP']
        entry_spread_PL = getattr(strategy.current_position, 'entry_spread_PL', last_spread_PL)
        entry_spread_LP = getattr(strategy.current_position, 'entry_spread_LP', last_spread_LP)
        strategy.exit_position(
            strategy.calculate_z_score(last_spread, spread_history),
            last_spread,
            last_timestamp,
            "end_of_data",
            last_spread_PL,
            last_spread_LP,
            entry_spread_PL,
            entry_spread_LP
        )
    
    # Calculer les stats
    stats = strategy.get_performance_stats()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 RÉSULTATS DU BACKTEST")
    logger.info("=" * 60)
    logger.info(f"   Total trades: {stats['total_trades']}")
    logger.info(f"   Trades gagnants: {stats['winning_trades']}")
    logger.info(f"   Trades perdants: {stats['losing_trades']}")
    logger.info(f"   Taux de réussite: {stats['win_rate']*100:.2f}%")
    logger.info(f"   PnL total: {stats['total_pnl']:.2f}")
    logger.info(f"   PnL moyen: {stats['avg_pnl']:.2f}")
    logger.info(f"   Profit max: {stats['max_profit']:.2f}")
    logger.info(f"   Perte max: {stats['max_loss']:.2f}")
    logger.info(f"   Durée moyenne: {stats['avg_duration_obs']:.1f} observations ({stats['avg_duration_seconds']:.1f} secondes)")
    logger.info("")
    
    return {
        'stats': stats,
        'trades': strategy.trades,
        'params': params
    }

def test_multiple_configs(spread_df: pd.DataFrame) -> List[Dict]:
    """
    Teste plusieurs configurations de paramètres
    """
    logger.info("🧪 Test de plusieurs configurations...")
    logger.info("")
    
    configs = [
        StrategyParams(entry_z=1.0, exit_z=0.5, stop_z=4.0, window=60, min_duration_s=4, decay_factor=0.95),
        StrategyParams(entry_z=1.5, exit_z=0.5, stop_z=4.0, window=60, min_duration_s=4, decay_factor=0.95),
        StrategyParams(entry_z=1.0, exit_z=0.3, stop_z=4.0, window=60, min_duration_s=4, decay_factor=0.95),
        StrategyParams(entry_z=1.0, exit_z=0.5, stop_z=3.0, window=60, min_duration_s=4, decay_factor=0.95),
        StrategyParams(entry_z=1.0, exit_z=0.5, stop_z=4.0, window=120, min_duration_s=4, decay_factor=0.95),
        StrategyParams(entry_z=1.0, exit_z=0.5, stop_z=4.0, window=60, min_duration_s=2, decay_factor=0.95),
        StrategyParams(entry_z=1.0, exit_z=0.5, stop_z=4.0, window=60, min_duration_s=4, decay_factor=0.98),  # Plus de poids aux récents
    ]
    
    results = []
    
    for i, params in enumerate(configs, 1):
        logger.info(f"📋 Configuration {i}/{len(configs)}")
        result = run_backtest(spread_df, params)
        results.append(result)
        logger.info("")
    
    # Afficher le classement
    logger.info("=" * 60)
    logger.info("🏆 CLASSEMENT DES CONFIGURATIONS")
    logger.info("=" * 60)
    
    sorted_results = sorted(results, key=lambda x: x['stats']['total_pnl'], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        stats = result['stats']
        params = result['params']
        logger.info(f"{i}. PnL: {stats['total_pnl']:.2f} | Win rate: {stats['win_rate']*100:.1f}% | Trades: {stats['total_trades']}")
        logger.info(f"   entry_z={params.entry_z}, exit_z={params.exit_z}, stop_z={params.stop_z}, window={params.window}, decay={params.decay_factor}")
    
    return results

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backtest de stratégie d\'arbitrage')
    parser.add_argument('--file', type=str, 
                       default='/Users/baptistecuchet/Downloads/price_history-export-2025-11-07_16-57-27.csv',
                       help='Chemin vers le fichier CSV de prix')
    parser.add_argument('--test-multiple', action='store_true',
                       help='Tester plusieurs configurations')
    parser.add_argument('--entry-z', type=float, default=1.0,
                       help='Seuil d\'entrée (z-score)')
    parser.add_argument('--exit-z', type=float, default=0.5,
                       help='Seuil de sortie (z-score)')
    parser.add_argument('--stop-z', type=float, default=4.0,
                       help='Stop loss (z-score)')
    parser.add_argument('--window', type=int, default=60,
                       help='Fenêtre glissante (observations)')
    parser.add_argument('--min-duration', type=int, default=4,
                       help='Durée minimale de confirmation (secondes)')
    parser.add_argument('--decay', type=float, default=0.95,
                       help='Facteur de décroissance exponentielle')
    
    args = parser.parse_args()
    
    # Charger les données
    df = load_price_data(args.file)
    
    # Préparer les spreads
    spread_df = prepare_spread_data(df)
    
    if args.test_multiple:
        # Tester plusieurs configurations
        results = test_multiple_configs(spread_df)
    else:
        # Tester une seule configuration
        params = StrategyParams(
            entry_z=args.entry_z,
            exit_z=args.exit_z,
            stop_z=args.stop_z,
            window=args.window,
            min_duration_s=args.min_duration,
            decay_factor=args.decay
        )
        result = run_backtest(spread_df, params)

if __name__ == "__main__":
    main()

