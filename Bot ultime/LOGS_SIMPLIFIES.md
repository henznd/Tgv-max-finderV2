# Système de Logs Simplifié avec Couleurs

## 🎨 Nouveau système de logs

Le bot d'arbitrage utilise maintenant un **système de logs simplifié** avec des **codes couleur** pour une meilleure lisibilité en console.

### Ce qui s'affiche en console (logs simples)

✅ **Bot lancé** - En CYAN
```
🤖 BOT LANCÉ | Token: BTC | Marge: $20 | Levier: 50x
```

✅ **Trade ouvert** - En VERT
```
📈 TRADE OUVERT | Direction: LONG | 0.001000 BTC | Prix: $98500.50 | Z-score: 2.50
```

✅ **Trade fermé** - En BLEU
```
📉 TRADE FERMÉ | Direction: SHORT | BTC | Prix sortie: $98650.25 | Z-score: 0.80
```

✅ **PNL positif** - En MAGENTA (rose)
```
💰 PNL: +$15.50 (+2.30%)
```

✅ **PNL négatif** - En ROUGE
```
💰 PNL: $-8.25 (-1.20%)
```

⚠️ **Warnings** - En JAUNE
```
⚠️ Historique insuffisant - Attente de données...
```

❌ **Erreurs** - En ROUGE
```
❌ ERREUR: Échec de la connexion à l'exchange
```

---

## 📁 Logs détaillés dans les fichiers

Tous les logs **détaillés et techniques** continuent d'être enregistrés dans le dossier `logs/` :
- `logs/arbitrage_bot_strategy_YYYYMMDD.log` - Logs détaillés du bot principal
- `logs/lighter_trader_YYYYMMDD.log` - Logs détaillés des trades Lighter
- etc.

Les fichiers contiennent **toutes** les informations techniques :
- Timestamps précis
- Prix bid/ask/mid
- Spreads exploitables (PL et LP)
- Z-scores détaillés
- Informations de débogage
- Traces d'erreurs complètes

---

## 🚀 Utilisation

### Bot principal
```bash
python3 arbitrage_bot_strategy.py --token BTC --margin 20 --leverage 50
```

**Console** : Affichage simplifié avec couleurs (bot lancé, trades, PNL)  
**Fichier log** : Informations complètes et détaillées

### Test du système de logs
```bash
python3 test_simple_logs.py
```

Affiche une démonstration de tous les types de logs avec leurs couleurs.

---

## 🎯 Avantages

✅ **Console claire** : Seulement l'essentiel (bot lancé, trade ouvert/fermé, PNL)  
✅ **Couleurs distinctes** : Facile de repérer les gains (magenta), pertes (rouge), erreurs (rouge)  
✅ **Logs détaillés préservés** : Toutes les infos techniques dans les fichiers  
✅ **Compatible** : Fonctionne avec tous les terminaux supportant les couleurs ANSI  

---

## 📊 Code couleur

| Événement | Couleur | Code ANSI |
|-----------|---------|-----------|
| Bot lancé | Cyan | `\033[96m` |
| Trade ouvert | Vert | `\033[92m` |
| Trade fermé | Bleu | `\033[94m` |
| PNL positif | Magenta | `\033[95m` |
| PNL négatif | Rouge | `\033[91m` |
| Warning | Jaune | `\033[93m` |
| Erreur | Rouge | `\033[91m` |

---

## 🔧 Fichiers modifiés

- **`simple_logger.py`** : Nouveau module de logs simplifié avec couleurs
- **`arbitrage_bot_strategy.py`** : Utilise le nouveau système pour les événements importants
- **`lighter/lighter_trader_config.py`** : Logs simplifiés pour les trades Lighter
- **`test_simple_logs.py`** : Script de démonstration

---

## 💡 Pour aller plus loin

Si vous souhaitez **personnaliser** les logs :

1. Modifier les couleurs dans `simple_logger.py` (classe `Colors`)
2. Modifier les messages dans les méthodes `bot_started()`, `trade_opened()`, etc.
3. Ajouter de nouveaux types de logs selon vos besoins

Le système est **flexible** et peut être étendu facilement !

