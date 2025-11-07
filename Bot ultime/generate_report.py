#!/usr/bin/env python3
"""
Génère un rapport détaillé et des graphiques pour la stratégie d'arbitrage
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sys
from backtest_arbitrage import load_price_data, prepare_spread_data, run_backtest
from arbitrage_strategy import StrategyParams
from logger import setup_logger

logger = setup_logger("report")

def generate_report(filepath: str, params: StrategyParams = None):
    """Génère un rapport complet avec graphiques"""
    
    if params is None:
        params = StrategyParams()
    
    logger.info("📊 Génération du rapport...")
    
    # Charger et préparer les données
    df = load_price_data(filepath)
    spread_df = prepare_spread_data(df)
    
    # Exécuter le backtest
    result = run_backtest(spread_df, params)
    stats = result['stats']
    trades = result['trades']
    
    # Créer les graphiques
    logger.info("📈 Création des graphiques...")
    
    # Créer une figure avec plusieurs sous-graphiques
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)
    
    # 1. Évolution du spread dans le temps
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(spread_df['timestamp'], spread_df['spread'], alpha=0.6, linewidth=0.5, label='Spread net')
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Temps')
    ax1.set_ylabel('Spread (Paradex - Lighter)')
    ax1.set_title('Évolution du Spread dans le Temps', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Distribution des spreads
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.hist(spread_df['spread'], bins=50, alpha=0.7, edgecolor='black')
    ax2.axvline(x=spread_df['spread'].mean(), color='red', linestyle='--', linewidth=2, label=f'Moyenne: {spread_df["spread"].mean():.2f}')
    ax2.set_xlabel('Spread')
    ax2.set_ylabel('Fréquence')
    ax2.set_title('Distribution des Spreads', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Évolution du PnL cumulé
    ax3 = fig.add_subplot(gs[1, 1])
    closed_trades = [t for t in trades if t.status in ['closed', 'stopped']]
    if closed_trades:
        pnl_cumulative = []
        cumulative = 0
        trade_times = []
        for trade in closed_trades:
            if trade.pnl is not None:
                cumulative += trade.pnl
                pnl_cumulative.append(cumulative)
                trade_times.append(trade.exit_time)
        
        if pnl_cumulative:
            ax3.plot(trade_times, pnl_cumulative, linewidth=2, color='green')
            ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            ax3.set_xlabel('Temps')
            ax3.set_ylabel('PnL Cumulé')
            ax3.set_title(f'Évolution du PnL Cumulé (Total: {stats["total_pnl"]:.2f})', fontsize=12, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Distribution des PnL par trade
    ax4 = fig.add_subplot(gs[2, 0])
    pnl_values = [t.pnl for t in closed_trades if t.pnl is not None]
    if pnl_values:
        ax4.hist(pnl_values, bins=30, alpha=0.7, edgecolor='black', color='green')
        ax4.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax4.axvline(x=np.mean(pnl_values), color='blue', linestyle='--', linewidth=2, label=f'Moyenne: {np.mean(pnl_values):.2f}')
        ax4.set_xlabel('PnL par Trade')
        ax4.set_ylabel('Fréquence')
        ax4.set_title('Distribution des PnL par Trade', fontsize=12, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 5. Durée des positions
    ax5 = fig.add_subplot(gs[2, 1])
    durations = [getattr(t, 'duration_seconds', t.duration_obs) for t in closed_trades]
    if durations:
        ax5.hist(durations, bins=30, alpha=0.7, edgecolor='black', color='orange')
        ax5.axvline(x=np.mean(durations), color='red', linestyle='--', linewidth=2, label=f'Moyenne: {np.mean(durations):.1f}s')
        ax5.set_xlabel('Durée (secondes)')
        ax5.set_ylabel('Fréquence')
        ax5.set_title('Distribution de la Durée des Positions', fontsize=12, fontweight='bold')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
    
    # 6. Trades gagnants vs perdants
    ax6 = fig.add_subplot(gs[3, 0])
    winning = [t.pnl for t in closed_trades if t.pnl is not None and t.pnl > 0]
    losing = [t.pnl for t in closed_trades if t.pnl is not None and t.pnl <= 0]
    ax6.bar(['Gagnants', 'Perdants'], [len(winning), len(losing)], color=['green', 'red'], alpha=0.7, edgecolor='black')
    ax6.set_ylabel('Nombre de Trades')
    ax6.set_title(f'Trades Gagnants vs Perdants (Win Rate: {stats["win_rate"]*100:.2f}%)', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate([len(winning), len(losing)]):
        ax6.text(i, v + 1, str(v), ha='center', fontweight='bold')
    
    # 7. Z-score à l'entrée vs PnL
    ax7 = fig.add_subplot(gs[3, 1])
    entry_z_scores = [t.entry_z for t in closed_trades if t.pnl is not None]
    pnl_for_z = [t.pnl for t in closed_trades if t.pnl is not None]
    if entry_z_scores and pnl_for_z:
        ax7.scatter(entry_z_scores, pnl_for_z, alpha=0.5, s=30)
        ax7.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax7.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax7.set_xlabel('Z-score à l\'entrée')
        ax7.set_ylabel('PnL')
        ax7.set_title('Z-score à l\'Entrée vs PnL', fontsize=12, fontweight='bold')
        ax7.grid(True, alpha=0.3)
    
    # Ajouter un titre général
    fig.suptitle(f'Rapport de Backtest - Stratégie d\'Arbitrage\n'
                 f'Période: {spread_df["timestamp"].min().strftime("%Y-%m-%d %H:%M")} → {spread_df["timestamp"].max().strftime("%Y-%m-%d %H:%M")} '
                 f'({(spread_df["timestamp"].max() - spread_df["timestamp"].min()).total_seconds() / 3600:.2f}h)',
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Sauvegarder le graphique
    output_file = 'backtest_report.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    logger.info(f"   ✅ Graphique sauvegardé: {output_file}")
    
    # Générer un rapport texte
    report_file = 'backtest_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT DE BACKTEST - STRATÉGIE D'ARBITRAGE\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("📅 PÉRIODE D'ANALYSE\n")
        f.write("-" * 80 + "\n")
        f.write(f"Début: {spread_df['timestamp'].min()}\n")
        f.write(f"Fin: {spread_df['timestamp'].max()}\n")
        duration_hours = (spread_df['timestamp'].max() - spread_df['timestamp'].min()).total_seconds() / 3600
        f.write(f"Durée totale: {duration_hours:.2f} heures ({duration_hours/24:.2f} jours)\n")
        f.write(f"Nombre d'observations: {len(spread_df)}\n")
        f.write(f"Fréquence moyenne: {len(spread_df) / duration_hours:.2f} observations/heure\n\n")
        
        f.write("📊 PARAMÈTRES DE LA STRATÉGIE\n")
        f.write("-" * 80 + "\n")
        f.write(f"entry_z (seuil d'entrée): {params.entry_z}\n")
        f.write(f"exit_z (seuil de sortie): {params.exit_z}\n")
        f.write(f"stop_z (stop loss): {params.stop_z}\n")
        f.write(f"window (fenêtre glissante): {params.window} observations\n")
        f.write(f"min_duration_s (validation signal): {params.min_duration_s} secondes\n")
        f.write(f"max_hold (durée max position): {params.max_hold} observations\n")
        f.write(f"decay_factor (pondération exponentielle): {params.decay_factor}\n\n")
        
        f.write("💰 RÉSULTATS DE PERFORMANCE\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total trades: {stats['total_trades']}\n")
        f.write(f"Trades gagnants: {stats['winning_trades']}\n")
        f.write(f"Trades perdants: {stats['losing_trades']}\n")
        f.write(f"Taux de réussite: {stats['win_rate']*100:.2f}%\n")
        f.write(f"PnL total: {stats['total_pnl']:.2f}\n")
        f.write(f"PnL moyen: {stats['avg_pnl']:.2f}\n")
        f.write(f"Profit max: {stats['max_profit']:.2f}\n")
        f.write(f"Perte max: {stats['max_loss']:.2f}\n")
        f.write(f"Durée moyenne: {stats['avg_duration_obs']:.1f} observations ({stats['avg_duration_seconds']:.1f} secondes)\n\n")
        
        f.write("📈 ANALYSE DES SPREADS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Spread moyen: {spread_df['spread'].mean():.2f}\n")
        f.write(f"Spread médian: {spread_df['spread'].median():.2f}\n")
        f.write(f"Spread min: {spread_df['spread'].min():.2f}\n")
        f.write(f"Spread max: {spread_df['spread'].max():.2f}\n")
        f.write(f"Écart-type: {spread_df['spread'].std():.2f}\n\n")
        
        f.write("📊 ANALYSE DES TRADES\n")
        f.write("-" * 80 + "\n")
        if closed_trades:
            pnl_values = [t.pnl for t in closed_trades if t.pnl is not None]
            if pnl_values:
                f.write(f"PnL médian: {np.median(pnl_values):.2f}\n")
                f.write(f"Écart-type PnL: {np.std(pnl_values):.2f}\n")
                f.write(f"Ratio profit/perte: {abs(stats['max_profit'] / stats['max_loss']) if stats['max_loss'] != 0 else 0:.2f}\n")
                f.write(f"Sharpe ratio (approximatif): {np.mean(pnl_values) / np.std(pnl_values) if np.std(pnl_values) > 0 else 0:.2f}\n\n")
        
        f.write("🎯 RECOMMANDATIONS\n")
        f.write("-" * 80 + "\n")
        if stats['win_rate'] > 0.9:
            f.write("✅ Excellent taux de réussite (>90%)\n")
        elif stats['win_rate'] > 0.7:
            f.write("✅ Bon taux de réussite (>70%)\n")
        else:
            f.write("⚠️  Taux de réussite à améliorer\n")
        
        if stats['total_pnl'] > 0:
            f.write("✅ Stratégie profitable sur la période testée\n")
        else:
            f.write("⚠️  Stratégie non profitable, réviser les paramètres\n")
        
        if stats['avg_duration_seconds'] < 60:
            f.write("✅ Positions de courte durée (bon pour la liquidité)\n")
        else:
            f.write("⚠️  Positions de longue durée, risque de slippage accru\n")
    
    logger.info(f"   ✅ Rapport texte sauvegardé: {report_file}")
    
    # Afficher un résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DU RAPPORT")
    print("=" * 80)
    print(f"Période analysée: {duration_hours:.2f} heures ({duration_hours/24:.2f} jours)")
    print(f"Total trades: {stats['total_trades']}")
    print(f"Taux de réussite: {stats['win_rate']*100:.2f}%")
    print(f"PnL total: {stats['total_pnl']:.2f}")
    print(f"Fichiers générés:")
    print(f"  - {output_file} (graphiques)")
    print(f"  - {report_file} (rapport détaillé)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Génère un rapport de backtest avec graphiques')
    parser.add_argument('--file', type=str, 
                       default='/Users/baptistecuchet/Downloads/price_history-export-2025-11-07_16-57-27.csv',
                       help='Chemin vers le fichier CSV de prix')
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
    
    params = StrategyParams(
        entry_z=args.entry_z,
        exit_z=args.exit_z,
        stop_z=args.stop_z,
        window=args.window,
        min_duration_s=args.min_duration,
        decay_factor=args.decay
    )
    
    generate_report(args.file, params)

