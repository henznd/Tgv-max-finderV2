#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict
import json

def get_tgvmax_trains(date: str, origin: str = None, destination: str = None) -> List[Dict]:
    """
    Récupère les trains TGV Max disponibles pour une date donnée avec filtres optionnels
    sur l'origine et la destination.
    
    Args:
        date (str): Date au format YYYY-MM-DD
        origin (str, optional): Gare de départ
        destination (str, optional): Gare d'arrivée
        
    Returns:
        List[Dict]: Liste des trains disponibles
    """
    base_url = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/tgvmax/records"
    
    # Construction des paramètres de requête
    where_conditions = [f"date = date'{date}'", "od_happy_card = 'OUI'"]
    
    if origin:
        # Utilisation de LIKE pour une recherche plus souple sur les noms de gares
        where_conditions.append(f"origine LIKE '{origin}%'")
    if destination:
        where_conditions.append(f"destination LIKE '{destination}%'")
    
    params = {
        'where': ' AND '.join(where_conditions),
        'limit': 100,
        'order_by': 'heure_depart'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
        data = response.json()
        if 'results' not in data:
            print(f"Réponse API inattendue: {data}")
            return []
        return data['results']
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête API: {str(e)}")
        if hasattr(response, 'status_code') and response.status_code == 400:
            print(f"Détails de l'erreur: {response.text}")
            print(f"URL de la requête: {response.url}")
        return []

def find_round_trips(depart_date: str, return_date: str, origin_city: str) -> pd.DataFrame:
    """
    Trouve les trajets aller-retour disponibles en TGV Max pour un week-end donné.
    
    Args:
        depart_date (str): Date de départ au format YYYY-MM-DD
        return_date (str): Date de retour au format YYYY-MM-DD
        origin_city (str): Ville de départ
        
    Returns:
        pd.DataFrame: DataFrame contenant les trajets aller-retour trouvés
    """
    print(f"Recherche des trains aller pour le {depart_date}...")
    outbound_trains = get_tgvmax_trains(depart_date, origin=origin_city)
    
    if len(outbound_trains) > 0:
        destinations = sorted(set(t['destination'] for t in outbound_trains))
        print(f"Destinations disponibles au départ: {', '.join(destinations)}")
    
    print(f"\nRecherche des trains retour pour le {return_date}...")
    # On ne filtre plus sur la ville de retour pour trouver tous les trajets possibles
    inbound_trains = get_tgvmax_trains(return_date)
    
    if len(inbound_trains) > 0:
        print(f"Origines disponibles pour le retour: {', '.join(sorted(set(t['origine'] for t in inbound_trains)))}")
    
    print(f"\nTrains aller trouvés: {len(outbound_trains)}")
    print(f"Trains retour trouvés: {len(inbound_trains)}")
    
    if len(outbound_trains) == 0 or len(inbound_trains) == 0:
        return pd.DataFrame()
    
    # Création des listes pour stocker les résultats
    round_trips = []
    
    # Recherche des correspondances aller-retour
    for outbound in outbound_trains:
        destination = outbound['destination']
        origin = outbound['origine']
        
        # Cherche les trains retour qui partent de la destination de l'aller
        # ET qui retournent à l'origine de l'aller
        matching_returns = [
            train for train in inbound_trains
            if train['origine'] == destination and train['destination'] == origin
        ]
        
        for return_train in matching_returns:
            round_trips.append({
                'Aller_Origine': outbound['origine'],
                'Aller_Destination': outbound['destination'],
                'Aller_Date': outbound['date'],
                'Aller_Heure': outbound['heure_depart'],
                'Aller_Arrivee': outbound['heure_arrivee'],
                'Retour_Origine': return_train['origine'],
                'Retour_Destination': return_train['destination'],
                'Retour_Date': return_train['date'],
                'Retour_Heure': return_train['heure_depart'],
                'Retour_Arrivee': return_train['heure_arrivee']
            })
    
    # Création du DataFrame
    if round_trips:
        df = pd.DataFrame(round_trips)
        # Formatage des colonnes de date
        for prefix in ['Aller_', 'Retour_']:
            df[f'{prefix}Date'] = pd.to_datetime(df[f'{prefix}Date']).dt.strftime('%d/%m/%Y')
        
        # Tri par heure de départ
        df = df.sort_values('Aller_Heure')
        
        # Ajout d'une colonne pour la durée du trajet aller et retour
        df['Duree_Aller'] = pd.to_datetime(df['Aller_Arrivee']) - pd.to_datetime(df['Aller_Heure'])
        df['Duree_Retour'] = pd.to_datetime(df['Retour_Arrivee']) - pd.to_datetime(df['Retour_Heure'])
        
        # Formatage des durées en heures et minutes
        df['Duree_Aller'] = df['Duree_Aller'].apply(lambda x: f"{x.components.hours}h{x.components.minutes:02d}")
        df['Duree_Retour'] = df['Duree_Retour'].apply(lambda x: f"{x.components.hours}h{x.components.minutes:02d}")
        
        return df
    else:
        return pd.DataFrame()

def main():
    """
    Fonction principale pour exécuter la recherche de trajets.
    """
    # Exemple d'utilisation avec une date où des données sont disponibles
    depart_date = "2025-05-13"  # Un mardi
    return_date = "2025-05-15"  # Un jeudi
    origin_city = "PARIS"  # La recherche sera faite avec LIKE 'PARIS%'
    
    print(f"Recherche des trajets aller-retour depuis {origin_city}")
    print(f"Aller le {depart_date}, retour le {return_date}")
    print("\nRecherche en cours...")
    
    df = find_round_trips(depart_date, return_date, origin_city)
    
    if not df.empty:
        print("\nTrajets aller-retour trouvés :")
        # Définition de l'affichage pandas pour voir toutes les colonnes
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df[['Aller_Origine', 'Aller_Destination', 'Aller_Date', 'Aller_Heure', 
                 'Aller_Arrivee', 'Duree_Aller', 'Retour_Heure', 'Retour_Arrivee', 
                 'Duree_Retour']])
        print(f"\nNombre total de trajets aller-retour trouvés : {len(df)}")
    else:
        print("\nAucun trajet aller-retour trouvé pour ces dates.")
        print("Note: Les données sont disponibles uniquement pour certaines dates futures.")
        print("Essayez par exemple avec des dates en mai 2025.")

if __name__ == "__main__":
    main() 