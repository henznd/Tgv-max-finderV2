# 🌐 Interface Web - Configuration Bot d'Arbitrage

Interface web moderne pour configurer et lancer votre bot d'arbitrage Lighter + Paradex.

## 🚀 Démarrage Rapide

### Option 1 : Script Bash (Recommandé)
```bash
./start_web_interface.sh
```

### Option 2 : Direct
```bash
python3 web_server.py
```

### Option 3 : Python
```bash
python3 web_server.py
```

## 📋 Fonctionnalités

### ⚙️ Configuration en Temps Réel
- **Lighter DEX** : Token, montant, levier
- **Paradex DEX** : Token, montant, levier
- **Sauvegarde automatique** en JSON
- **Validation** des paramètres

### 🎯 Tokens Supportés
- **BTC** (Bitcoin) - Recommandé pour Lighter
- **ETH** (Ethereum) - Recommandé pour Paradex
- **SOL** (Solana)
- **USDC** (USD Coin)

### ⚡ Leviers Disponibles
- **Lighter** : 1x à 50x (recommandé: 10x)
- **Paradex** : 1x à 50x (recommandé: 50x)

## 🌐 Interface Web

### URL d'Accès
```
http://localhost:8080
```

### Fonctionnalités de l'Interface
1. **Configuration Lighter** : Token, montant, levier
2. **Configuration Paradex** : Token, montant, levier
3. **Sauvegarde** : Persistance des paramètres
4. **Lancement** : Bot avec configuration personnalisée
5. **Reset** : Retour aux valeurs par défaut

## 📁 Structure des Fichiers

```
Bot ultime/
├── web_interface.html          # Interface web (HTML/CSS/JS)
├── web_server.py              # Serveur web (Python)
├── trading_config.json         # Configuration JSON
├── arbitrage_bot_config.py     # Bot principal configurable
├── lighter/
│   └── lighter_trader_config.py # Script Lighter configurable
├── paradex/
│   └── paradex_trader_config.py # Script Paradex configurable
└── start_web_interface.sh      # Script de lancement
```

## 🔧 Utilisation

### 1. Démarrer l'Interface
```bash
./start_web_interface.sh
```

### 2. Ouvrir le Navigateur
- L'interface s'ouvre automatiquement sur `http://localhost:8080`
- Sinon, ouvrez manuellement cette URL

### 3. Configurer les Paramètres
- **Lighter** : Choisir token, montant, levier
- **Paradex** : Choisir token, montant, levier
- Cliquer sur "💾 Sauvegarder Configuration"

### 4. Lancer le Bot
- Cliquer sur "🚀 Lancer le Bot"
- Le bot utilise la configuration sauvegardée
- Les deux DEX s'exécutent en parallèle

## 📊 Exemple de Configuration

### Configuration Lighter
```json
{
  "lighter": {
    "token": "BTC",
    "amount": 0.00001,
    "leverage": 10
  }
}
```

### Configuration Paradex
```json
{
  "paradex": {
    "token": "ETH",
    "amount": 0.03,
    "leverage": 50
  }
}
```

## 🎨 Interface Utilisateur

### Design Moderne
- **Gradient** : Couleurs modernes
- **Responsive** : Mobile et desktop
- **Animations** : Transitions fluides
- **Feedback** : Messages de statut

### Sections
1. **Header** : Titre et description
2. **Configuration Lighter** : Paramètres Lighter DEX
3. **Configuration Paradex** : Paramètres Paradex DEX
4. **Contrôles** : Boutons d'action
5. **Statut** : Messages de retour

## 🔍 Dépannage

### Erreur "Port already in use"
```bash
# Changer le port dans web_server.py
# Ligne: start_server(port=8081)
```

### Erreur "File not found"
```bash
# Vérifier que tous les fichiers existent
ls -la web_interface.html web_server.py trading_config.json
```

### Erreur "Permission denied"
```bash
chmod +x start_web_interface.sh
chmod +x web_server.py
```

### Interface ne s'ouvre pas
- Ouvrir manuellement : `http://localhost:8080`
- Vérifier que le serveur est démarré
- Vérifier les logs du serveur

## 📈 Avantages

### ✅ Configuration Visuelle
- Interface intuitive
- Paramètres clairs
- Validation automatique

### ✅ Persistance
- Configuration sauvegardée
- Paramètres réutilisables
- Historique des configurations

### ✅ Sécurité
- Validation côté serveur
- Gestion d'erreurs
- Logs détaillés

### ✅ Performance
- Exécution parallèle
- Gestion des threads
- Interface responsive

## 🚀 Prochaines Étapes

1. **Configurer** vos paramètres via l'interface
2. **Tester** avec de petits montants
3. **Optimiser** selon vos besoins
4. **Monitorer** les performances

## 📞 Support

En cas de problème :
1. Vérifiez les logs du serveur
2. Vérifiez la configuration JSON
3. Testez les scripts individuels
4. Consultez la documentation des DEX

