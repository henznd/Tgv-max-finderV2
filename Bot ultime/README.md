# Bot d'Arbitrage - Lighter & Paradex

Bot d'arbitrage pour trader simultanément sur Lighter et Paradex.

## 📁 Structure du projet

### Bot d'arbitrage
- `arbitrage_bot_config.py` - Bot principal d'exécution
- `arbitrage_strategy.py` - Stratégie d'arbitrage
- `trade_verification.py` - Vérification des trades
- `logger.py` - Configuration du logging
- `trading_config.json` - Configuration des trades

### Traders
- `lighter/lighter_trader_config.py` - Trader Lighter
- `paradex/paradex_trader_config.py` - Trader Paradex

### Interface web
- `web_server.py` - Serveur web (port 8080)
- `web_interface.html` - Interface utilisateur
- `start_web_interface.sh` - Script de démarrage

### Collecte Supabase
- `supabase/functions/get-dex-prices/` - Edge Function pour récupérer les prix
- `supabase/functions/collect-prices/` - Edge Function pour collecter et stocker
- `supabase/setup_simple.sql` - Script SQL de configuration

### Utilitaires
- `execute_sql_direct.py` - Exécution SQL sur Supabase
- `requirements.txt` - Dépendances Python

## 🚀 Utilisation

### Démarrer l'interface web
```bash
./start_web_interface.sh
```
Puis ouvrez http://localhost:8080

### Configuration
Modifiez `trading_config.json` ou utilisez l'interface web.

### Collecte des prix
La collecte est automatique via Supabase (cron job).

## 📊 Collecte des prix

Les prix sont collectés automatiquement toutes les secondes dans Supabase :
- Table : `price_history`
- Tokens : BTC, ETH
- Exchanges : Lighter, Paradex

