#!/bin/bash
# Script pour redémarrer le serveur web automatiquement

echo "🛑 Arrêt de l'ancien serveur web..."
pkill -f "web_server.py" 2>/dev/null
sleep 1

echo "🧹 Nettoyage des processus..."
pkill -9 -f "web_server.py" 2>/dev/null
sleep 1

echo "🚀 Démarrage du nouveau serveur web..."
cd "/Users/baptistecuchet/Desktop/Bot ultime"
python3 web_server.py

echo "✅ Serveur redémarré avec succès !"
echo "📍 Ouvrez: http://localhost:8080/strategy"

