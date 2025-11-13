#!/bin/bash
# Script de configuration initiale du VPS pour le bot d'arbitrage

set -e  # Arrêter en cas d'erreur

echo "🚀 Configuration du VPS pour le bot d'arbitrage"
echo "================================================"

# Mise à jour du système
echo "📦 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# Installation de Python 3.11
echo "🐍 Installation de Python 3.11..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Installation de dépendances système
echo "📚 Installation des dépendances système..."
sudo apt install -y git curl wget build-essential libpq-dev

# Configuration de Python 3.11 par défaut
echo "🔧 Configuration de Python 3.11..."
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Création du répertoire de l'application
echo "📁 Création du répertoire de l'application..."
mkdir -p ~/bot-arbitrage
cd ~/bot-arbitrage

# Installation de pip pour Python 3.11
echo "📦 Installation de pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Installation des dépendances Python
echo "📦 Installation des dépendances Python..."
python3.11 -m pip install --upgrade pip
python3.11 -m pip install lighter-sdk aiohttp paradex-py starknet-py supabase psycopg2-binary python-dotenv numpy

# Configuration du firewall
echo "🔥 Configuration du firewall..."
sudo ufw allow 8080/tcp  # Port de l'interface web
sudo ufw allow 22/tcp    # SSH
sudo ufw --force enable

# Création d'un service systemd pour le bot
echo "⚙️  Création du service systemd..."
sudo tee /etc/systemd/system/arbitrage-bot.service > /dev/null <<EOF
[Unit]
Description=Bot d'arbitrage Lighter/Paradex
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/bot-arbitrage
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 $HOME/bot-arbitrage/web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Rechargement de systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Configuration du VPS terminée !"
echo ""
echo "📋 Prochaines étapes :"
echo "1. Uploadez votre code dans ~/bot-arbitrage"
echo "2. Créez le fichier .env avec vos credentials"
echo "3. Démarrez le bot avec : sudo systemctl start arbitrage-bot"
echo "4. Vérifiez le statut avec : sudo systemctl status arbitrage-bot"
echo "5. Activez le démarrage automatique : sudo systemctl enable arbitrage-bot"
echo ""
echo "🌐 L'interface web sera accessible sur : http://VOTRE_IP_VPS:8080"

