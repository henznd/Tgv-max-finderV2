import pandas as pd
from datetime import datetime, time
from typing import List, Dict
import requests
import streamlit as st
from config import SNCF_API_URL, API_LIMIT, CACHE_TTL

@st.cache_data(ttl=CACHE_TTL)
def get_tgvmax_trains(date: str, origin: str = None, destination: str = None) -> List[Dict]:
    """
    Récupère les trains TGV Max disponibles pour une date donnée.
    Utilise le cache Streamlit pour optimiser les performances.
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
        st.error(f"Erreur lors de la requête API: {str(e)}")
        return []

def calculate_duration(departure: str, arrival: str) -> str:
    """
    Calcule la durée entre deux heures au format HH:MM.
    """
    dep = pd.to_datetime(departure, format='%H:%M')
    arr = pd.to_datetime(arrival, format='%H:%M')
    duration = arr - dep
    hours = duration.components.hours
    minutes = duration.components.minutes
    return f"{hours}h{minutes:02d}"

def filter_trains_by_time(df: pd.DataFrame, depart_start: time, depart_end: time, 
                         return_start: time = None, return_end: time = None, 
                         is_round_trip: bool = True) -> pd.DataFrame:
    """
    Filtre les trains selon les plages horaires spécifiées.
    """
    if df.empty:
        return df
        
    # Conversion des heures en objets time pour la comparaison
    if is_round_trip:
        df['Aller_Time'] = pd.to_datetime(df['Aller_Heure'], format='%H:%M').dt.time
        mask_aller = (df['Aller_Time'] >= depart_start) & (df['Aller_Time'] <= depart_end)
        
        if return_start and return_end:
            df['Retour_Time'] = pd.to_datetime(df['Retour_Heure'], format='%H:%M').dt.time
            mask_retour = (df['Retour_Time'] >= return_start) & (df['Retour_Time'] <= return_end)
            mask = mask_aller & mask_retour
        else:
            mask = mask_aller
    else:
        df['Depart_Time'] = pd.to_datetime(df['heure_depart'], format='%H:%M').dt.time
        mask = (df['Depart_Time'] >= depart_start) & (df['Depart_Time'] <= depart_end)
    
    filtered_df = df[mask].copy()
    # Suppression des colonnes temporaires
    cols_to_drop = ['Aller_Time', 'Retour_Time', 'Depart_Time']
    filtered_df.drop([col for col in cols_to_drop if col in filtered_df.columns], axis=1, inplace=True)
    return filtered_df

def format_single_trips(trains: List[Dict]) -> pd.DataFrame:
    """
    Formate les trajets simples en DataFrame.
    """
    if not trains:
        return pd.DataFrame()
    
    df = pd.DataFrame(trains)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
    df['duree'] = df.apply(lambda x: calculate_duration(x['heure_depart'], x['heure_arrivee']), axis=1)
    
    return df[['origine', 'destination', 'date', 'heure_depart', 'heure_arrivee', 'duree']]

def handle_error(func):
    """
    Décorateur pour gérer les erreurs de manière uniforme.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"Une erreur est survenue : {str(e)}")
            return pd.DataFrame()
    return wrapper 