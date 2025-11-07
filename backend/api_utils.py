import pandas as pd
from datetime import datetime, time
from typing import List, Dict, Optional
import requests
from api_config import SNCF_API_URL, API_LIMIT

# Cache removed for API version, was @st.cache_data(ttl=CACHE_TTL)
def get_tgvmax_trains(date: str, origin: Optional[str] = None, destination: Optional[str] = None) -> List[Dict]:
    """
    Récupère les trains TGV Max disponibles pour une date donnée.
    """
    where_conditions = [f"date = date'{date}'", "od_happy_card = 'OUI'"]
    
    if origin:
        where_conditions.append(f"origine LIKE '{origin}%'")
    if destination:
        where_conditions.append(f"destination LIKE '{destination}%'")
    
    params = {
        'where': ' AND '.join(where_conditions),
        'limit': API_LIMIT,
        'order_by': 'heure_depart'
    }
    
    try:
        response = requests.get(SNCF_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Erreur API: {str(e)}")
        return []

def calculate_duration(departure: str, arrival: str) -> str:
    """
    Calcule la durée entre deux heures au format HH:MM.
    """
    dep = pd.to_datetime(departure, format='%H:%M')
    arr = pd.to_datetime(arrival, format='%H:%M')
    duration = arr - dep
    seconds = duration.total_seconds()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h{minutes:02d}"

def format_single_trips(trains: List[Dict]) -> pd.DataFrame:
    """
    Formate les trajets simples en DataFrame.
    """
    if not trains:
        return pd.DataFrame()
    
    df = pd.DataFrame(trains)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
    df['duree'] = df.apply(lambda x: calculate_duration(x['heure_depart'], x['heure_arrivee']), axis=1)
    
    # S'assurer que les colonnes existent avant de les retourner
    cols = ['origine', 'destination', 'date', 'heure_depart', 'heure_arrivee', 'duree']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    return df[cols]

def group_trains_by_destination(trains: List[Dict]) -> List[Dict]:
    """
    Groupe les trains par destination et les trie chronologiquement.
    """
    if not trains:
        return []
    
    df = pd.DataFrame(trains)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
    df['duree'] = df.apply(lambda x: calculate_duration(x['heure_depart'], x['heure_arrivee']), axis=1)
    
    # S'assurer que les colonnes existent
    cols = ['origine', 'destination', 'date', 'heure_depart', 'heure_arrivee', 'duree']
    for col in cols:
        if col not in df.columns:
            df[col] = None
    
    # Grouper par destination et trier par heure de départ
    grouped_results = []
    
    for destination in df['destination'].unique():
        if pd.isna(destination):
            continue
            
        destination_trains = df[df['destination'] == destination].copy()
        
        # Trier par heure de départ
        destination_trains = destination_trains.sort_values(by='heure_depart')
        
        # Formater les trains pour cette destination
        trains_for_destination = []
        for _, train in destination_trains.iterrows():
            trains_for_destination.append({
                'origine': train['origine'],
                'destination': train['destination'],
                'date': train['date'],
                'heure_depart': train['heure_depart'],
                'heure_arrivee': train['heure_arrivee'],
                'duree': train['duree']
            })
        
        grouped_results.append({
            'destination': destination,
            'trains': trains_for_destination,
            'count': len(trains_for_destination)
        })
    
    # Trier les destinations par nombre de trains (décroissant)
    grouped_results.sort(key=lambda x: x['count'], reverse=True)
    
    return grouped_results

def handle_error(func):
    """
    Décorateur pour gérer les erreurs de manière uniforme.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Erreur: {str(e)}")
            return pd.DataFrame()
    return wrapper 