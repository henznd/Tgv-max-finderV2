import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import requests
from typing import List, Dict
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
    }
    
    /* En-tête */
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
        color: #1d1d1f;
        font-size: 48px;
        text-align: center;
        margin-bottom: 0;
        padding: 2rem 0 0.5rem;
    }
    
    .sub-header {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        color: #86868b;
        font-size: 24px;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f5f5f7;
        border-right: none;
    }
    
    /* Boutons */
    .stButton>button {
        background-color: #0071e3;
        color: white;
        border: none;
        border-radius: 980px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0077ED;
        transform: scale(1.02);
    }
    
    /* Cards */
    .trip-card {
        background-color: #fff;
        border-radius: 18px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #e5e5e5;
    }
    
    /* Signature */
    .signature {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        padding: 0.75rem 1.5rem;
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 980px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #1d1d1f;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid #e5e5e5;
        z-index: 1000;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #f5f5f7;
        border-radius: 14px;
        padding: 1rem;
        margin: 1rem 0;
        border: none;
    }
    
    /* DataFrames */
    .dataframe {
        border: none !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background-color: #f5f5f7 !important;
        color: #1d1d1f !important;
        font-weight: 600 !important;
    }
    
    .dataframe td {
        font-size: 0.9rem !important;
    }
    
    /* Radio buttons */
    .st-cc {
        border-radius: 980px !important;
        padding: 2px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 12px !important;
        background-color: #f5f5f7 !important;
        border: none !important;
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
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 16px;
        background-color: #f5f5f7;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0071e3;
        color: white;
    }

    /* Destinations disponibles */
    .destinations-chip {
        display: inline-block;
        background-color: #f5f5f7;
        border-radius: 980px;
        padding: 4px 12px;
        margin: 2px 4px;
        font-size: 0.9rem;
        color: #1d1d1f;
    }

    .destinations-container {
        background-color: #fff;
        border-radius: 14px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border: 1px solid #e5e5e5;
        font-size: 0.9rem;
    }

    .destinations-title {
        color: #86868b;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
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
               date_range_days: int = DEFAULT_RANGE_DAYS) -> pd.DataFrame:
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
        if not df.empty and depart_start and depart_end:
            return filter_trains_by_time(df, depart_start, depart_end, is_round_trip=False)
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
            
        if outbound_trains:
            destinations = sorted(set(t['destination'] for t in outbound_trains))
            st.markdown(
                f"""<div class="destinations-container">
                    <div class="destinations-title">Destinations possibles en aller-retour :</div>
                    {''.join(f'<span class="destinations-chip">{dest}</span>' for dest in destinations)}
                </div>""",
                unsafe_allow_html=True
            )
        
        with st.spinner('Recherche des trains retour...'):
            inbound_trains = get_tgvmax_trains(return_date.strftime("%Y-%m-%d"))
        
        if not outbound_trains or not inbound_trains:
            return pd.DataFrame()
        
        round_trips = []
        for outbound in outbound_trains:
            destination = outbound['destination']
            origin = outbound['origine']
            
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
        
        if round_trips:
            df = pd.DataFrame(round_trips)
            for prefix in ['Aller_', 'Retour_']:
                df[f'{prefix}Date'] = pd.to_datetime(df[f'{prefix}Date']).dt.strftime('%d/%m/%Y')
            
            df = df.sort_values('Aller_Heure')
            
            if depart_start and depart_end:
                df = filter_trains_by_time(df, depart_start, depart_end, return_start, return_end)
            
            if not df.empty:
                df['Duree_Aller'] = df.apply(lambda x: calculate_duration(x['Aller_Heure'], x['Aller_Arrivee']), axis=1)
                df['Duree_Retour'] = df.apply(lambda x: calculate_duration(x['Retour_Heure'], x['Retour_Arrivee']), axis=1)
            
            return df
        return pd.DataFrame()

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

def convert_duration_to_timedelta(duration_str: str) -> pd.Timedelta:
    """Convertit une chaîne de durée (ex: '2h15') en Timedelta."""
    if 'h' in duration_str:
        parts = duration_str.split('h')
        hours = int(parts[0])
        minutes = int(parts[1]) if parts[1] else 0
        return pd.Timedelta(hours=hours, minutes=minutes)
    return pd.Timedelta(minutes=int(duration_str))

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
                    🗓️ Réservations ouvertes jusqu'au {latest_date.strftime("%d/%m/%Y")}
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
        df = find_trips(
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
        
        if not df.empty:
            # Appliquer les filtres avancés
            if search_mode == SearchMode.ROUND_TRIP:
                # Conversion des durées en timedelta
                df['Duree_Aller_Timedelta'] = df['Duree_Aller'].apply(convert_duration_to_timedelta)
                df['Duree_Retour_Timedelta'] = df['Duree_Retour'].apply(convert_duration_to_timedelta)
                df['Duree_Totale'] = df['Duree_Aller_Timedelta'] + df['Duree_Retour_Timedelta']
                
                # Filtre par durée
                df = df[df['Duree_Totale'] <= pd.Timedelta(hours=max_duration)]
                
                # Tri des résultats
                if sort_by == "Heure de départ":
                    df = df.sort_values('Aller_Heure', ascending=(sort_order == "Croissant"))
                elif sort_by == "Durée":
                    df = df.sort_values('Duree_Totale', ascending=(sort_order == "Croissant"))
                else:  # Destination
                    df = df.sort_values('Aller_Destination', ascending=(sort_order == "Croissant"))
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
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Vue détaillée", "📈 Résumé par destination", "📈 Statistiques", "⭐ Favoris", "🗺️ Carte"])
            
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
            
            with tab3:
                st.markdown('<h3 style="color: #1d1d1f; font-size: 24px; margin-bottom: 1.5rem;">Statistiques des trajets</h3>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if search_mode == SearchMode.ROUND_TRIP:
                        avg_duration_aller = df['Duree_Aller'].mean() if not df.empty else "N/A"
                        avg_duration_retour = df['Duree_Retour'].mean() if not df.empty else "N/A"
                        st.metric("Durée moyenne aller", avg_duration_aller)
                        st.metric("Durée moyenne retour", avg_duration_retour)
                    else:
                        avg_duration = df['duree'].mean() if not df.empty else "N/A"
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

            with tab4:
                st.markdown("### ⭐ Gérer mes favoris")
                if search_mode == SearchMode.ROUND_TRIP:
                    for _, row in df.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"🚅 {row['Aller_Origine']} → {row['Aller_Destination']}")
                        with col2:
                            fav = {
                                'origin': row['Aller_Origine'],
                                'destination': row['Aller_Destination']
                            }
                            if fav not in st.session_state.favorites:
                                if st.button("⭐", key=f"add_{row['Aller_Origine']}_{row['Aller_Destination']}"):
                                    st.session_state.favorites.append(fav)
                                    st.rerun()
                else:
                    for _, row in df.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"🚅 {row['origine']} → {row['destination']}")
                        with col2:
                            fav = {
                                'origin': row['origine'],
                                'destination': row['destination']
                            }
                            if fav not in st.session_state.favorites:
                                if st.button("⭐", key=f"add_{row['origine']}_{row['destination']}"):
                                    st.session_state.favorites.append(fav)
                                    st.rerun()

            with tab5:
                st.markdown("### 🗺️ Visualisation des trajets")
                if not df.empty:
                    m = create_route_map(df, search_mode)
                    folium_static(m)
                    
                    st.markdown("""
                    <div class="info-box">
                        <h4>📍 Légende</h4>
                        <p>• 🔵 Gares de départ</p>
                        <p>• 🟢 Gares d'arrivée</p>
                        <p>• Les lignes bleues représentent les trajets</p>
                        <p>• Cliquez sur les marqueurs pour plus d'informations</p>
                    </div>
                    """, unsafe_allow_html=True)
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