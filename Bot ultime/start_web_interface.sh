#!/bin/bash
# Script de démarrage de l'interface web

echo "🚀 Démarrage de l'interface web du bot d'arbitrage..."
echo ""

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que le fichier web_server.py existe
if [ ! -f "web_server.py" ]; then
    echo "❌ Fichier web_server.py non trouvé"
    exit 1
fi

# Démarrer le serveur
echo "🌐 Démarrage du serveur web sur http://localhost:8080"
echo "📝 Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python3 web_server.py


# Script de démarrage de l'interface web

echo "🚀 Démarrage de l'interface web du bot d'arbitrage..."
echo ""

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que le fichier web_server.py existe
if [ ! -f "web_server.py" ]; then
    echo "❌ Fichier web_server.py non trouvé"
    exit 1
fi

# Démarrer le serveur
echo "🌐 Démarrage du serveur web sur http://localhost:8080"
echo "📝 Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python3 web_server.py


