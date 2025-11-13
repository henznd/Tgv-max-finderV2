#!/bin/bash
# Script de déploiement du bot sur le VPS

# Configuration - Modifiez ces valeurs
VPS_IP="VOTRE_IP_VPS"
VPS_USER="root"  # ou votre utilisateur
VPS_PATH="/root/bot-arbitrage"  # ou ~/bot-arbitrage

set -e

echo "🚀 Déploiement du bot d'arbitrage sur le VPS"
echo "=============================================="

# Vérification que .env existe
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant ! Créez-le à partir de .env.example"
    exit 1
fi

echo "📦 Création de l'archive du projet..."
tar -czf bot-arbitrage.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*' \
    --exclude='.git' \
    --exclude='bot-arbitrage.tar.gz' \
    *.py *.html *.sh .env requirements.txt lighter/ paradex/ supabase/ 2>/dev/null || true

echo "📤 Envoi de l'archive sur le VPS..."
scp bot-arbitrage.tar.gz $VPS_USER@$VPS_IP:$VPS_PATH/

echo "🔧 Déploiement sur le VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
    cd ~/bot-arbitrage
    
    echo "📦 Extraction de l'archive..."
    tar -xzf bot-arbitrage.tar.gz
    rm bot-arbitrage.tar.gz
    
    echo "📦 Installation des dépendances..."
    python3.11 -m pip install -r requirements.txt --upgrade
    
    echo "✅ Validation de la configuration..."
    python3.11 config.py
    
    echo "🔄 Redémarrage du service..."
    sudo systemctl restart arbitrage-bot
    
    echo "📊 Statut du service..."
    sudo systemctl status arbitrage-bot --no-pager
ENDSSH

# Nettoyage local
rm bot-arbitrage.tar.gz

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "🌐 Interface web : http://$VPS_IP:8080"
echo "📊 Vérifier les logs : ssh $VPS_USER@$VPS_IP 'tail -f $VPS_PATH/logs/web_server_*.log'"
echo "🔧 Arrêter le bot : ssh $VPS_USER@$VPS_IP 'sudo systemctl stop arbitrage-bot'"
echo "🔧 Redémarrer le bot : ssh $VPS_USER@$VPS_IP 'sudo systemctl restart arbitrage-bot'"

