# TGV Max Finder

Application web pour rechercher facilement les trajets disponibles en TGV Max.

## Fonctionnalités

- Recherche d'allers simples et d'allers-retours
- Recherche sur plage de dates (jusqu'à 30 jours)
- Filtres horaires personnalisables
- Visualisation des trajets sur une carte interactive
- Statistiques sur les trajets trouvés

## Installation locale

1. Cloner le repository
```bash
git clone https://github.com/votre-username/tgvmax-finder.git
cd tgvmax-finder
```

2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/macOS
# ou
.\venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Lancer l'application
```bash
streamlit run tgvmax_app.py
```

## Déploiement

L'application est déployée sur Streamlit Cloud et accessible à l'adresse : [votre-lien-streamlit]

## Mise à jour

L'application se met à jour automatiquement à chaque push sur la branche principale.

## Développé par

Baptiste Cuchet

## Licence

MIT License 