# Bot de Trading DEX - Authentification

Un bot de trading automatisé pour les DEX (Decentralized Exchanges) avec un focus sur l'authentification sécurisée.

## 🚀 Fonctionnalités

- **Authentification sécurisée** avec signature cryptographique
- **Support Lighter DEX** avec API complète
- **Gestion des signatures** EIP-712 et messages standards
- **Configuration flexible** via variables d'environnement
- **Interface modulaire** pour ajouter d'autres DEX

## 📋 Prérequis

- Python 3.8+
- Clé privée Ethereum
- Adresse de wallet Ethereum
- Accès à l'API du DEX (Lighter, etc.)

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd Bot\ arbitrage
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
```bash
# Copier le fichier de configuration
cp config.env.example .env

# Éditer .env avec vos vraies clés
nano .env
```

## ⚙️ Configuration

Créez un fichier `.env` avec vos paramètres :

```env
# Lighter DEX
LIGHTER_API_URL=https://api.lighter.xyz/v1
LIGHTER_PRIVATE_KEY=your_private_key_here
LIGHTER_WALLET_ADDRESS=your_wallet_address_here

# Configuration réseau
NETWORK=mainnet
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your_api_key
GAS_PRICE_MULTIPLIER=1.1

# Options
DEBUG=false
MAX_RETRIES=3
TIMEOUT=30
```

## 🚀 Utilisation

### Script principal
```bash
python trading_bot.py
```

### Exemples d'utilisation
```bash
python example_usage.py
```

### Utilisation programmatique
```python
from trading_bot import TradingBot

# Créer le bot
bot = TradingBot()

# Initialiser Lighter
bot.initialize_lighter()

# S'authentifier
bot.authenticate()

# Tester la connexion
bot.test_connection()

# Récupérer le solde
balance = bot.get_balance()

# Placer un ordre
order_data = {
    "type": "limit",
    "side": "buy",
    "symbol": "ETH-USDC",
    "price": 1500.0,
    "size": 0.1,
    "time_in_force": "GTC"
}
result = bot.authenticator.place_order(order_data)
```

## 🔐 Authentification

Le bot utilise plusieurs méthodes d'authentification :

### 1. Signature de messages
```python
from auth.signature_manager import SignatureManager

sig_manager = SignatureManager(private_key, wallet_address)
signature = sig_manager.sign_message("Hello DEX!")
```

### 2. Signature EIP-712
```python
# Pour les données structurées
signature = sig_manager.sign_structured_data(
    domain=domain,
    types=types,
    primary_type="Order",
    message=message
)
```

### 3. Signature de payload
```python
# Pour les requêtes API
signed_payload = sig_manager.sign_payload(payload)
```

## 📊 Types d'ordres supportés

- **Market orders** : Exécution immédiate
- **Limit orders** : Prix fixe
- **Stop-loss** : Protection contre les pertes
- **Take-profit** : Sécurisation des gains
- **TWAP** : Exécution sur une période

## 🛡️ Sécurité

- **Clés privées** : Stockées localement, jamais exposées
- **Signatures** : Vérification cryptographique de chaque requête
- **Nonce** : Protection contre les attaques de replay
- **Timestamp** : Validation temporelle des requêtes

## 🔧 Architecture

```
Bot arbitrage/
├── auth/                    # Module d'authentification
│   ├── __init__.py
│   ├── dex_auth.py         # Interface DEX abstraite
│   ├── lighter_auth.py     # Implémentation Lighter
│   └── signature_manager.py # Gestion des signatures
├── config.py               # Configuration
├── trading_bot.py          # Script principal
├── example_usage.py        # Exemples d'utilisation
├── requirements.txt        # Dépendances
└── README.md              # Documentation
```

## 🚨 Avertissements

- **Testez d'abord** sur des montants faibles
- **Sécurisez vos clés** privées
- **Vérifiez** les paramètres avant l'exécution
- **Surveillez** les transactions en temps réel

## 📝 Logs et Debug

Activez le mode debug dans `.env` :
```env
DEBUG=true
```

Les logs incluent :
- Authentification
- Signatures
- Requêtes API
- Erreurs détaillées

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la documentation de l'API
- Vérifier les logs de debug
