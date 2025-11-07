import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import requests
from typing import List, Dict, Union
from enum import Enum
import folium
from folium import plugins
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from streamlit_folium import folium_static
import json
from config import (
    MIN_DATE, MAX_DATE, DEFAULT_START_TIME, DEFAULT_END_TIME,
    DEFAULT_ORIGIN, MAX_RANGE_DAYS, DEFAULT_RANGE_DAYS
)
from utils import (
    get_tgvmax_trains, filter_trains_by_time, format_single_trips,
    calculate_duration, handle_error
)
import re

# Configuration de la page
st.set_page_config(
    page_title="TGV Max Finder",
    page_icon="🚄",
    layout="wide",
    menu_items={
        'Get Help': 'mailto:baptiste.cuchet@gmail.com',
        'Report a bug': 'mailto:baptiste.cuchet@gmail.com',
        'About': "Application développée par Baptiste Cuchet pour faciliter la recherche de trajets TGV Max."
    }
)

class SearchMode(str, Enum):
    SINGLE = "Aller simple"
    ROUND_TRIP = "Aller-retour"
    DATE_RANGE = "Plage de dates"

# Configuration des styles CSS personnalisés
st.markdown("""
    <style>
    /* Styles globaux */
    .stApp {
        background-color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* En-tête */
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 800;
        color: #1d1d1f;
        font-size: 52px;
        text-align: center;
        margin-bottom: 0;
        padding: 2rem 0 0.5rem;
        background: linear-gradient(45deg, #0071e3, #42a1ec);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeIn 1s ease-in;
    }
    
    .sub-header {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        color: #86868b;
        font-size: 24px;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        animation: slideUp 0.8s ease-out;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f5f5f7;
        border-right: none;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Boutons */
    .stButton>button {
        background: linear-gradient(45deg, #0071e3, #42a1ec);
        color: white;
        border: none;
        border-radius: 980px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
    }
    
    /* Cards */
    .trip-card {
        background-color: #fff;
        border-radius: 18px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e5e5;
        transition: all 0.3s ease;
        animation: slideUp 0.5s ease-out;
    }
    
    .trip-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
    }
    
    /* Signature */
    .signature {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        padding: 0.75rem 1.5rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 980px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #1d1d1f;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid #e5e5e5;
        z-index: 1000;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .signature:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(45deg, #f5f5f7, #ffffff);
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e5e5;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
        animation: fadeIn 0.5s ease-out;
    }
    
    /* DataFrames */
    .dataframe {
        border: none !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04) !important;
    }
    
    .dataframe th {
        background: linear-gradient(45deg, #f5f5f7, #ffffff) !important;
        color: #1d1d1f !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        font-size: 0.9rem !important;
        padding: 12px !important;
        transition: all 0.2s ease;
    }
    
    .dataframe tr:hover td {
        background-color: #f8f8f8 !important;
    }
    
    /* Radio buttons */
    .st-cc {
        border-radius: 980px !important;
        padding: 2px !important;
        background: #f5f5f7 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 12px !important;
        background: linear-gradient(45deg, #f5f5f7, #ffffff) !important;
        border: 1px solid #e5e5e5 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    
    /* Small text */
    .small-text {
        font-size: 0.9rem;
        color: #86868b;
        line-height: 1.5;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        padding: 4px;
        background: #f5f5f7;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 16px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #0071e3, #42a1ec);
        color: #1d1d1f;
        box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
    }

    /* Destinations disponibles */
    .destinations-chip {
        display: inline-block;
        background: linear-gradient(45deg, #f5f5f7, #ffffff);
        border-radius: 980px;
        padding: 6px 14px;
        margin: 4px;
        font-size: 0.9rem;
        color: #1d1d1f;
        border: 1px solid #e5e5e5;
        transition: all 0.3s ease;
    }

    .destinations-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    .destinations-container {
        background: linear-gradient(45deg, #ffffff, #f8f8f8);
        border-radius: 14px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #e5e5e5;
        font-size: 0.9rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
    }

    .destinations-title {
        color: #1d1d1f;
        font-size: 1rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Loading spinner */
    .stSpinner > div {
        border: 3px solid #f5f5f7;
        border-top: 3px solid #0071e3;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(45deg, #0071e3, #42a1ec);
    }

    @media (max-width: 600px) {
      .main-header { font-size: 24px !important; }
      .sub-header { font-size: 14px !important; }
      .trip-card { padding: 0.5rem !important; }
      .stButton>button { font-size: 13px !important; padding: 8px 8px !important; }
      .dataframe th, .dataframe td { font-size: 0.7rem !important; padding: 4px !important; }
      .stTabs [data-baseweb="tab-list"] { flex-direction: column !important; }
      .info-box { padding: 0.5rem !important; font-size: 0.8rem !important; }
      .destinations-chip { font-size: 0.6rem !important; padding: 3px 6px !important; }
    }
    </style>
    
    <div class="signature">
        Développé par Baptiste Cuchet 🚀
    </div>
    """, unsafe_allow_html=True)

@handle_error
def find_trips(mode: SearchMode,
               depart_date: datetime.date,
               return_date: datetime.date = None,
               origin_city: str = None,
               destination_city: str = None,
               depart_start: time = None,
               depart_end: time = None,
               return_start: time = None,
               return_end: time = None,
               date_range_days: int = DEFAULT_RANGE_DAYS) -> Union[pd.DataFrame, dict, List[dict]]:
    """
    Trouve les trajets disponibles en TGV Max selon le mode choisi.
    """
    if mode == SearchMode.DATE_RANGE:
        all_trains = []
        with st.spinner(f'Recherche des trains sur {date_range_days} jours...'):
            progress_bar = st.progress(0)
            for i in range(date_range_days):
                current_date = depart_date + timedelta(days=i)
                trains = get_tgvmax_trains(
                    current_date.strftime("%Y-%m-%d"),
                    origin=origin_city,
                    destination=destination_city
                )
                all_trains.extend(trains)
                progress_bar.progress((i + 1) / date_range_days)
            progress_bar.empty()
        df = format_single_trips(all_trains)
        if not df.empty:
            # S'assurer que la colonne 'date' est bien de type datetime pour le tri
            df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values(by=["date_dt", "heure_depart"]).reset_index(drop=True)
            df['date'] = df['date_dt'].dt.strftime('%d/%m/%Y')
            del df['date_dt']
        if not df.empty and depart_start and depart_end:
            df = filter_trains_by_time(df, depart_start, depart_end, is_round_trip=False)
        # Affichage groupé par date
        if mode == SearchMode.DATE_RANGE and not df.empty:
            for date_str in df['date'].unique():
                day_trips = df[df['date'] == date_str]
                with st.expander(f"🗓️ {date_str}", expanded=False):
                    for _, trip in day_trips.iterrows():
                        st.markdown(
                            f"""<div class="trip-card">
                                <p><strong>{trip['heure_depart']} → {trip['heure_arrivee']}</strong> ({trip['duree']})</p>
                                <p class="small-text">Date : {trip['date']}</p>
                            </div>""",
                            unsafe_allow_html=True
                        )
            return pd.DataFrame()
        return df
    
    elif mode == SearchMode.SINGLE:
        with st.spinner('Recherche des trains...'):
            trains = get_tgvmax_trains(
                depart_date.strftime("%Y-%m-%d"),
                origin=origin_city
            )
            
        if trains:
            with st.expander("🎯 Voir les destinations disponibles", expanded=False):
                st.markdown(
                    f"""<div class="destinations-container">
                        <div class="destinations-title">Destinations disponibles :</div>
                        {''.join(f'<span class="destinations-chip">{dest}</span>' for dest in sorted(set(t['destination'] for t in trains)))}
                    </div>""",
                    unsafe_allow_html=True
                )
            
        df = format_single_trips(trains)
        if not df.empty and depart_start and depart_end:
            return filter_trains_by_time(df, depart_start, depart_end, is_round_trip=False)
        return df
    
    else:  # mode == SearchMode.ROUND_TRIP
        with st.spinner('Recherche des trains aller...'):
            outbound_trains = get_tgvmax_trains(
                depart_date.strftime("%Y-%m-%d"),
                origin=origin_city
            )
        # On récupère toutes les destinations atteignables à l'aller
        destinations_aller = sorted(set(t['destination'] for t in outbound_trains))
        all_results = []
        for dest in destinations_aller:
            try:
                with st.spinner(f'Recherche des trains retour pour {dest}...'):
                    inbound_trains = get_tgvmax_trains(
                        return_date.strftime("%Y-%m-%d"),
                        origin=dest,
                        destination=origin_city
                    )
            except Exception as e:
                # On ignore l'erreur API pour cette destination
                inbound_trains = []
            df_aller = format_single_trips([t for t in outbound_trains if t['destination'] == dest])
            df_retour = format_single_trips(inbound_trains)
            # Filtrage horaire
            if not df_aller.empty and depart_start and depart_end:
                df_aller = filter_trains_by_time(df_aller, depart_start, depart_end, is_round_trip=False)
            if not df_retour.empty and return_start and return_end:
                df_retour = filter_trains_by_time(df_retour, return_start, return_end, is_round_trip=False)
            if not df_aller.empty and not df_retour.empty:
                all_results.append({"destination": dest, "aller": df_aller, "retour": df_retour})
        return all_results

@st.cache_data(ttl=3600)  # Cache pour 1 heure
def find_latest_train_date():
    """Trouve la date du dernier train disponible dans l'API."""
    # On part de la date maximale possible
    current_date = MAX_DATE
    
    # On teste chaque jour en reculant jusqu'à trouver des trains
    while current_date >= MIN_DATE:
        try:
            # On teste avec Paris qui a toujours des trains
            trains = get_tgvmax_trains(
                current_date.strftime("%Y-%m-%d"),
                origin="PARIS"
            )
            if trains:
                return current_date
        except:
            pass
        current_date -= timedelta(days=1)
    
    return MIN_DATE

def init_session_state():
    """Initialise les variables de session."""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'

def toggle_theme():
    """Bascule entre le mode clair et sombre."""
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Cache pour les coordonnées des villes
@st.cache_data
def get_city_coordinates(city: str) -> tuple:
    """Récupère les coordonnées d'une ville."""
    try:
        geolocator = Nominatim(user_agent="tgvmax_finder")
        location = geolocator.geocode(f"{city}, France")
        if location:
            return (location.latitude, location.longitude)
    except GeocoderTimedOut:
        pass
    return None

def create_route_map(df: pd.DataFrame, search_mode: SearchMode) -> folium.Map:
    """Crée une carte avec les trajets."""
    # Centrer la carte sur la France
    france_center = [46.603354, 1.888334]
    m = folium.Map(location=france_center, zoom_start=6)
    
    # Créer un groupe de marqueurs pour le clustering
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Dictionnaire pour stocker les coordonnées des villes
    city_coords = {}
    
    if search_mode == SearchMode.ROUND_TRIP:
        origins = df['Aller_Origine'].unique()
        destinations = df['Aller_Destination'].unique()
    else:
        origins = df['origine'].unique()
        destinations = df['destination'].unique()
    
    # Récupérer les coordonnées de toutes les villes
    all_cities = set(list(origins) + list(destinations))
    for city in all_cities:
        coords = get_city_coordinates(city)
        if coords:
            city_coords[city] = coords
    
    # Ajouter les marqueurs et les lignes
    for _, row in df.iterrows():
        if search_mode == SearchMode.ROUND_TRIP:
            origin = row['Aller_Origine']
            destination = row['Aller_Destination']
            depart_time = row['Aller_Heure']
            arrival_time = row['Aller_Arrivee']
        else:
            origin = row['origine']
            destination = row['destination']
            depart_time = row['heure_depart']
            arrival_time = row['heure_arrivee']
        
        if origin in city_coords and destination in city_coords:
            # Ajouter les marqueurs
            origin_coords = city_coords[origin]
            dest_coords = city_coords[destination]
            
            # Marqueur de départ
            folium.CircleMarker(
                location=origin_coords,
                radius=8,
                color='#0071e3',
                fill=True,
                popup=f"🚉 {origin}",
            ).add_to(marker_cluster)
            
            # Marqueur d'arrivée
            folium.CircleMarker(
                location=dest_coords,
                radius=8,
                color='#2ecc71',
                fill=True,
                popup=f"🏁 {destination}",
            ).add_to(marker_cluster)
            
            # Ligne du trajet
            folium.PolyLine(
                locations=[origin_coords, dest_coords],
                color='#0071e3',
                weight=2,
                opacity=0.8,
                popup=f"{origin} → {destination}<br>{depart_time} - {arrival_time}",
            ).add_to(m)
    
    return m

def convert_duration_to_minutes(duration_str: str) -> int:
    """Convertit une durée au format '1h30' en minutes."""
    if not isinstance(duration_str, str):
        return 0
    try:
        hours = 0
        minutes = 0
        if 'h' in duration_str:
            parts = duration_str.split('h')
            hours = int(parts[0])
            minutes = int(parts[1]) if parts[1] else 0
        else:
            minutes = int(duration_str)
        return hours * 60 + minutes
    except:
        return 0

def format_minutes_to_duration(minutes: int) -> str:
    """Convertit un nombre de minutes en format '1h30'."""
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h{mins:02d}"

def calculate_average_duration(durations: pd.Series) -> str:
    """Calcule la moyenne d'une série de durées."""
    if durations.empty:
        return "N/A"
    minutes_list = [convert_duration_to_minutes(d) for d in durations]
    if not minutes_list:
        return "N/A"
    avg_minutes = sum(minutes_list) / len(minutes_list)
    return format_minutes_to_duration(int(avg_minutes))

def test_june_dates():
    """Fonction temporaire pour tester les dates de juin."""
    june_dates = []
    for day in range(1, 31):
        date = datetime(2024, 6, day).date()
        try:
            trains = get_tgvmax_trains(date.strftime("%Y-%m-%d"), origin="PARIS")
            if trains:
                june_dates.append(date)
        except:
            continue
    return june_dates

def convert_duration_to_timedelta(duration_str: str) -> pd.Timedelta:
    """Convertit une chaîne de durée (ex: '2h15') en Timedelta."""
    if 'h' in duration_str:
        parts = duration_str.split('h')
        hours = int(parts[0])
        minutes = int(parts[1]) if parts[1] else 0
        return pd.Timedelta(hours=hours, minutes=minutes)
    return pd.Timedelta(minutes=int(duration_str))

def main():
    init_session_state()
    
    # En-tête stylisé
    st.markdown('<h1 class="main-header">TGV Max Finder</h1>', unsafe_allow_html=True)
    
    # Calcul simple de la date limite (aujourd'hui + 30 jours)
    latest_date = datetime.now().date() + timedelta(days=30)
    
    # Test temporaire des dates de juin
    june_dates = test_june_dates()
    if june_dates:
        st.sidebar.write("Dates trouvées en juin:", june_dates)
    
    # Affichage de la date limite en haut de page
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p class="sub-header">Trouvez vos trajets en TGV Max en quelques clics</p>
            <div style="
                background-color: #f5f5f7;
                padding: 1rem;
                border-radius: 10px;
                margin: 1rem auto;
                max-width: 600px;
                text-align: center;
            ">
                <span style="
                    font-size: 1.1em;
                    color: #1d1d1f;
                ">
                    🎫 Les billets TGV Max sont disponibles jusqu'au {latest_date.strftime("%d/%m/%Y")}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sidebar pour les filtres
    with st.sidebar:
        st.markdown('<h2 style="color: #1d1d1f; font-size: 24px; margin-bottom: 1.5rem;">Paramètres de recherche</h2>', unsafe_allow_html=True)
        
        # Sélection du mode de recherche
        search_mode = st.radio(
            "Mode de recherche",
            options=[mode.value for mode in SearchMode],
            format_func=lambda x: x,
            help="Choisissez votre mode de recherche"
        )
        search_mode = SearchMode(search_mode)
        
        # Paramètres de recherche selon le mode
        if search_mode == SearchMode.DATE_RANGE:
            st.markdown(
                '<div class="info-box">📅 Explorez les trains disponibles sur une période donnée</div>',
                unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                origin_city = st.text_input("Ville de départ", help="Exemple: PARIS, LYON, MARSEILLE...")
            with col2:
                destination_city = st.text_input("Ville d'arrivée", help="Exemple: MARSEILLE, BORDEAUX...")
            
            date_range_days = st.slider(
                "Nombre de jours à explorer",
                min_value=1,
                max_value=MAX_RANGE_DAYS,
                value=DEFAULT_RANGE_DAYS,
                help="Choisissez sur combien de jours vous souhaitez rechercher"
            )
        else:
            origin_city = st.text_input("Ville de départ", DEFAULT_ORIGIN, help="Exemple: PARIS, LYON, MARSEILLE...")
            destination_city = None
            date_range_days = DEFAULT_RANGE_DAYS
        
        if search_mode == SearchMode.ROUND_TRIP:
            st.markdown(
                '<div class="info-box">🔄 Trouvez des trajets aller-retour depuis votre ville</div>',
                unsafe_allow_html=True
            )
            col1, col2 = st.columns(2)
            with col1:
                depart_date = st.date_input(
                    "Date aller",
                    min_value=MIN_DATE,
                    max_value=MAX_DATE,
                    value=MIN_DATE + timedelta(days=1)
                )
            with col2:
                return_date = st.date_input(
                    "Date retour",
                    min_value=depart_date,
                    max_value=MAX_DATE,
                    value=depart_date + timedelta(days=2)
                )
        else:
            if search_mode == SearchMode.SINGLE:
                st.markdown(
                    '<div class="info-box">🎯 Explorez toutes les destinations accessibles</div>',
                    unsafe_allow_html=True
                )
            depart_date = st.date_input(
                "Date de départ",
                min_value=MIN_DATE,
                max_value=MAX_DATE,
                value=MIN_DATE + timedelta(days=1)
            )
            return_date = None
        
        # Plages horaires
        st.markdown("### ⏰ Plages horaires")
        
        # Aller
        st.write("Horaires de départ" + (" (Aller)" if search_mode == SearchMode.ROUND_TRIP else ""))
        col3, col4 = st.columns(2)
        with col3:
            depart_start = st.time_input("Début", DEFAULT_START_TIME)
        with col4:
            depart_end = st.time_input("Fin", DEFAULT_END_TIME)
        
        # Retour (uniquement pour aller-retour)
        if search_mode == SearchMode.ROUND_TRIP:
            st.write("Horaires de départ (Retour)")
            col5, col6 = st.columns(2)
            with col5:
                return_start = st.time_input("Début ", DEFAULT_START_TIME)
            with col6:
                return_end = st.time_input("Fin ", DEFAULT_END_TIME)
        else:
            return_start = return_end = None
        
        # Paramètres avancés dans un expander
        with st.expander("⚙️ Paramètres avancés", expanded=False):
            st.markdown("#### 🎯 Filtres")
            
            # Filtre de durée maximale
            max_duration = st.slider(
                "Durée maximale (heures)",
                min_value=1,
                max_value=12,
                value=12,
                help="Filtrer les trajets par durée maximale"
            )
            
            # Tri des résultats
            sort_by = st.selectbox(
                "Trier par",
                options=["Heure de départ", "Durée", "Destination"],
                help="Choisir le critère de tri des résultats"
            )
            
            # Ordre de tri
            sort_order = st.radio(
                "Ordre",
                options=["Croissant", "Décroissant"],
                horizontal=True
            )
        
        search_button = st.button("Rechercher les trains", type="primary", use_container_width=True)

    # Affichage des résultats
    if search_button:
        result = find_trips(
            mode=search_mode,
            depart_date=depart_date,
            return_date=return_date,
            origin_city=origin_city,
            destination_city=destination_city,
            depart_start=depart_start,
            depart_end=depart_end,
            return_start=return_start,
            return_end=return_end,
            date_range_days=date_range_days
        )
        if search_mode == SearchMode.ROUND_TRIP:
            all_results = result
            if not all_results:
                st.error("Aucun aller-retour disponible pour ces dates.")
            else:
                st.markdown(
                    f'<div style="text-align: center; padding: 2rem;"><h2 style="color: #1d1d1f; font-size: 32px;">✨ {len(all_results)} destination(s) avec aller-retour disponible !</h2></div>',
                    unsafe_allow_html=True
                )
                for res in all_results:
                    dest = res["destination"]
                    df_aller = res["aller"]
                    df_retour = res["retour"]
                    with st.expander(f"🚄 {dest}"):
                        st.markdown('<h4>Allers possibles</h4>', unsafe_allow_html=True)
                        for _, trip in df_aller.iterrows():
                            st.markdown(
                                f"""<div class="trip-card">
                                    <p><strong>{trip['heure_depart']} → {trip['heure_arrivee']}</strong> ({trip['duree']})</p>
                                    <p class="small-text">Date : {trip['date']}</p>
                                </div>""",
                                unsafe_allow_html=True
                            )
                        st.markdown('<h4>Retours possibles</h4>', unsafe_allow_html=True)
                        for _, trip in df_retour.iterrows():
                            st.markdown(
                                f"""<div class="trip-card">
                                    <p><strong>{trip['heure_depart']} → {trip['heure_arrivee']}</strong> ({trip['duree']})</p>
                                    <p class="small-text">Date : {trip['date']}</p>
                                </div>""",
                                unsafe_allow_html=True
                            )
        else:
            df = result
            if not df.empty:
                # Appliquer les filtres avancés
                if search_mode == SearchMode.ROUND_TRIP:
                    # Conversion des durées en timedelta
                    df['Duree_Timedelta'] = df['duree'].apply(convert_duration_to_timedelta)
                    
                    # Filtre par durée
                    df = df[df['Duree_Timedelta'] <= pd.Timedelta(hours=max_duration)]
                    
                    # Tri des résultats
                    if sort_by == "Heure de départ":
                        df = df.sort_values('heure_depart', ascending=(sort_order == "Croissant"))
                    elif sort_by == "Durée":
                        df = df.sort_values('Duree_Timedelta', ascending=(sort_order == "Croissant"))
                    else:  # Destination
                        df = df.sort_values('destination', ascending=(sort_order == "Croissant"))
                else:
                    # Conversion des durées en timedelta
                    df['Duree_Timedelta'] = df['duree'].apply(convert_duration_to_timedelta)
                    
                    # Filtre par durée
                    df = df[df['Duree_Timedelta'] <= pd.Timedelta(hours=max_duration)]
                    
                    # Tri des résultats
                    if sort_by == "Heure de départ":
                        df = df.sort_values('heure_depart', ascending=(sort_order == "Croissant"))
                    elif sort_by == "Durée":
                        df = df.sort_values('Duree_Timedelta', ascending=(sort_order == "Croissant"))
                    else:  # Destination
                        df = df.sort_values('destination', ascending=(sort_order == "Croissant"))
                
                st.markdown(
                    f'<div style="text-align: center; padding: 2rem;"><h2 style="color: #1d1d1f; font-size: 32px;">✨ {len(df)} trajet{"s" if len(df) > 1 else ""} trouvé{"s" if len(df) > 1 else ""} !</h2></div>',
                    unsafe_allow_html=True
                )
                
                # Création d'onglets pour différentes vues
                tab2, tab1, tab3 = st.tabs(["📈 Résumé par destination", "📊 Vue détaillée", "📈 Statistiques"])
                
                with tab2:
                    # Résumé par destination
                    st.markdown('<h3 style="color: #1d1d1f; font-size: 24px; margin-bottom: 1.5rem;">Résumé par destination</h3>', unsafe_allow_html=True)
                    if search_mode == SearchMode.ROUND_TRIP:
                        destinations = df['Aller_Destination'].unique()
                        for dest in sorted(destinations):
                            dest_trips = df[df['Aller_Destination'] == dest]
                            with st.expander(f"🎯 {dest} ({len(dest_trips)} trajets)"):
                                for _, trip in dest_trips.iterrows():
                                    st.markdown(
                                        f"""<div class="trip-card">
                                            <p><strong>Aller :</strong> {trip['Aller_Heure']} → {trip['Aller_Arrivee']} ({trip['Duree_Aller']})</p>
                                            <p><strong>Retour :</strong> {trip['Retour_Heure']} → {trip['Retour_Arrivee']} ({trip['Duree_Retour']})</p>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                    else:
                        destinations = df['destination'].unique()
                        for dest in sorted(destinations):
                            dest_trips = df[df['destination'] == dest]
                            with st.expander(f"🎯 {dest} ({len(dest_trips)} trajets)"):
                                for _, trip in dest_trips.iterrows():
                                    st.markdown(
                                        f"""<div class="trip-card">
                                            <p><strong>{trip['heure_depart']} → {trip['heure_arrivee']}</strong> ({trip['duree']})</p>
                                            <p class="small-text">Date : {trip['date']}</p>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                
                with tab1:
                    # Vue détaillée
                    if search_mode == SearchMode.ROUND_TRIP:
                        st.dataframe(
                            df[['Aller_Destination', 'Aller_Heure', 'Aller_Arrivee', 'Duree_Aller',
                                'Retour_Heure', 'Retour_Arrivee', 'Duree_Retour']],
                            hide_index=True,
                            column_config={
                                'Aller_Destination': 'Destination',
                                'Aller_Heure': 'Départ Aller',
                                'Aller_Arrivee': 'Arrivée Aller',
                                'Duree_Aller': 'Durée Aller',
                                'Retour_Heure': 'Départ Retour',
                                'Retour_Arrivee': 'Arrivée Retour',
                                'Duree_Retour': 'Durée Retour'
                            }
                        )
                    else:
                        st.dataframe(
                            df,
                            hide_index=True,
                            column_config={
                                'origine': 'Départ',
                                'destination': 'Arrivée',
                                'date': 'Date',
                                'heure_depart': 'Heure départ',
                                'heure_arrivee': 'Heure arrivée',
                                'duree': 'Durée'
                            }
                        )
                
                with tab3:
                    st.markdown('<h3 style="color: #1d1d1f; font-size: 24px; margin-bottom: 1.5rem;">Statistiques des trajets</h3>', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if search_mode == SearchMode.ROUND_TRIP:
                            avg_duration_aller = calculate_average_duration(df['Duree_Aller'])
                            avg_duration_retour = calculate_average_duration(df['Duree_Retour'])
                            st.metric("Durée moyenne aller", avg_duration_aller)
                            st.metric("Durée moyenne retour", avg_duration_retour)
                        else:
                            avg_duration = calculate_average_duration(df['duree'])
                            st.metric("Durée moyenne", avg_duration)

                    with col2:
                        if search_mode == SearchMode.ROUND_TRIP:
                            n_destinations = len(df['Aller_Destination'].unique()) if not df.empty else 0
                        else:
                            n_destinations = len(df['destination'].unique()) if not df.empty else 0
                        st.metric("Nombre de destinations", n_destinations)
                        
                        earliest_departure = df['Aller_Heure'].min() if search_mode == SearchMode.ROUND_TRIP else df['heure_depart'].min() if not df.empty else "N/A"
                        latest_departure = df['Aller_Heure'].max() if search_mode == SearchMode.ROUND_TRIP else df['heure_depart'].max() if not df.empty else "N/A"
                        st.metric("Premier départ", earliest_departure)
                        st.metric("Dernier départ", latest_departure)

                    with col3:
                        if search_mode == SearchMode.ROUND_TRIP:
                            trips_per_dest = df.groupby('Aller_Destination').size()
                        else:
                            trips_per_dest = df.groupby('destination').size() if not df.empty else pd.Series()
                        
                        if not trips_per_dest.empty:
                            most_frequent_dest = trips_per_dest.idxmax()
                            n_trips_most_frequent = trips_per_dest.max()
                            st.metric("Destination la plus desservie", f"{most_frequent_dest} ({n_trips_most_frequent} trajets)")

                        # Graphique des trajets par heure si pertinent
                        if not df.empty:
                            st.markdown("### 📈 Répartition des trajets par heure")
                            if search_mode == SearchMode.ROUND_TRIP:
                                hour_dist = pd.to_datetime(df['Aller_Heure']).dt.hour.value_counts().sort_index()
                            else:
                                hour_dist = pd.to_datetime(df['heure_depart']).dt.hour.value_counts().sort_index()
                            st.bar_chart(hour_dist)
            else:
                # Trouver la date la plus éloignée disponible dans l'API
                future_date = MAX_DATE
                st.markdown(
                    f'''<div class="info-box" style="text-align: center; padding: 2rem;">
                        <h3 style="color: #1d1d1f;">Aucun trajet trouvé pour ces critères</h3>
                        <p class="small-text">Les données sont disponibles jusqu'au {future_date.strftime("%d/%m/%Y")}</p>
                    </div>''',
                    unsafe_allow_html=True
                )

    # Footer avec des informations supplémentaires
    st.markdown("---")
    st.markdown("""
    <div class="small-text" style="background-color: #f5f5f7; padding: 2rem; border-radius: 18px; margin-top: 2rem;">
        <h4 style="color: #1d1d1f; margin-bottom: 1rem;">💡 Conseils d'utilisation</h4>
        <ul style="list-style-type: none; padding: 0;">
            <li style="margin-bottom: 0.5rem;">• Le mode "Aller simple" est parfait pour explorer toutes les destinations disponibles depuis votre ville</li>
            <li style="margin-bottom: 0.5rem;">• Le mode "Aller-retour" vous aide à trouver les meilleures correspondances</li>
            <li style="margin-bottom: 0.5rem;">• Le mode "Plage de dates" est idéal quand vous êtes flexible sur les dates</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 
