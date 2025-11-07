# Trading Bot - Lighter & Paradex DEX

Scripts fonctionnels pour trader sur Lighter et Paradex DEX.

## ⚠️ IMPORTANT - Deux Versions Python Requises

Ce bot nécessite **DEUX versions différentes de Python** :
- **Python 3.9** pour Lighter DEX
- **Python 3.11** pour Paradex DEX

**Pourquoi ?** Les SDKs ont des incompatibilités de dépendances entre versions.

## 🚀 Scripts Disponibles

### Lighter DEX
- **Script** : `lighter/lighter_trader.py`
- **Python** : 3.9 (`/usr/bin/python3`)
- **Trade** : BTC avec levier 10x
- **Status** : ✅ Fonctionnel

### Paradex DEX  
- **Script** : `paradex/paradex_trader.py`
- **Python** : 3.11 (`python3.11`)
- **Trade** : ETH avec levier 50x
- **Status** : ✅ Fonctionnel

## 📋 Utilisation

### Lighter DEX
```bash
/usr/bin/python3 lighter/lighter_trader.py
```

### Paradex DEX
```bash
python3.11 paradex/paradex_trader.py
```

## ⚙️ Configuration

Les scripts utilisent les clés configurées dans les fichiers :
- Lighter : Clés hardcodées dans le script
- Paradex : Clés hardcodées dans le script

## 📊 Tests Réussis

- ✅ Lighter : Trade BTC 0.00001 (~$10) avec levier 10x
- ✅ Paradex : Trade ETH 0.03 (~$134) avec levier 50x

## 🔧 Installation

### Prérequis
Vérifiez que vous avez les deux versions Python :
```bash
/usr/bin/python3 --version  # Doit afficher Python 3.9.x
python3.11 --version         # Doit afficher Python 3.11.x
```

### Installation des dépendances

#### Pour Lighter (Python 3.9)
```bash
/usr/bin/python3 -m pip install lighter-sdk
```

#### Pour Paradex (Python 3.11)
```bash
python3.11 -m pip install paradex-py starknet-py
```

## 🤖 Bot d'Arbitrage

Pour lancer les deux scripts simultanément :
```bash
python3.11 arbitrage_bot.py
```

Le bot d'arbitrage utilise Python 3.11 mais lance automatiquement :
- Lighter avec Python 3.9
- Paradex avec Python 3.11