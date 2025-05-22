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
    DEFAULT_ORIGIN, MAX_RANGE_DAYS, DEFAULT_RANGE_DAYS, STATIONS, STATIONS_COORDS
)
from utils import (
    get_tgvmax_trains, filter_trains_by_time, format_single_trips,
    calculate_duration, handle_error, search_trains, format_duration
)

# Configuration de la page
st.set_page_config(
    page_title="TGV Max Explorer - L'ami des aventuriers",
    page_icon="🚅",
    layout="wide",
    menu_items={
        'Get Help': 'mailto:baptiste.cuchet@gmail.com',
        'Report a bug': 'mailto:baptiste.cuchet@gmail.com',
        'About': "Application développée par Baptiste Cuchet pour faciliter la recherche de trajets TGV Max."
    }
)

def main():
    # En-tête avec style
    st.markdown("""
        <h1 style='text-align: center; color: #1d1d1f; font-size: 3.2em; margin-bottom: 0.5em;'>
            🚅 TGV Max Explorer
            <br/>
            <small style='font-size: 0.4em; color: #666;'>L'ami des aventuriers TGV Max</small>
        </h1>
        """, unsafe_allow_html=True)

    # Message humoristique et bannière "Work in Progress"
    st.markdown("""
        <div style='text-align: center; padding: 1.5rem; margin: 2rem 0; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #1d1d1f; margin-bottom: 1rem;'>🎯 Notre Mission</h3>
            <p style='font-size: 1.2em; color: #444; margin-bottom: 1rem;'>
                <em>Fini de perdre 1h à chercher la destination de ton prochain week-end !</em>
            </p>
            <p style='color: #666; font-style: italic;'>
                Créé par des voyageurs frustrés, pour des voyageurs qui en ont marre de l'app SNCF Connect 😅
            </p>
        </div>

        <div style='background-color: #fff3cd; color: #856404; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 5px solid #ffeeba;'>
            <h4 style='color: #856404; margin-bottom: 0.5rem;'>🚧 Site en développement !</h4>
            <p>Comme un TGV en rodage, on peaufine encore quelques détails. Mais promis, ça va déjà plus vite que de trouver un Paris-Lyon un vendredi soir ! 😉</p>
        </div>
        """, unsafe_allow_html=True)

    # Sélection du mode de recherche
    search_mode = st.radio(
        "Choisis ton mode d'exploration 🎯",
        [SearchMode.ONE_WAY, SearchMode.ROUND_TRIP, SearchMode.ALL_DESTINATIONS],
        format_func=lambda x: {
            SearchMode.ONE_WAY: "🗺️ Mode Exploration (Aller Simple)",
            SearchMode.ROUND_TRIP: "🔄 Mode Week-end (Aller-Retour)",
            SearchMode.ALL_DESTINATIONS: "🎯 Mode Chasseur de Trains"
        }[x]
    )

    # Descriptions des modes avec style amélioré
    mode_descriptions = {
        SearchMode.ONE_WAY: """
            <div style='padding: 2rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #1d1d1f; margin-bottom: 1rem;'>🗺️ Mode Exploration (Aller Simple)</h3>
                <p style='font-size: 1.1em; color: #444; margin-bottom: 1rem;'>
                    Pour les âmes aventurières qui veulent s'évader ! Ce mode te montre TOUTES les destinations possibles depuis ta ville.
                </p>
                <ul style='color: #666; list-style-type: none; padding-left: 0;'>
                    <li style='margin: 0.5rem 0;'>✨ Découvre des destinations que tu n'aurais jamais imaginées</li>
                    <li style='margin: 0.5rem 0;'>🎯 Parfait pour les décisions spontanées</li>
                    <li style='margin: 0.5rem 0;'>🌍 Visualise toutes tes options en un clin d'œil</li>
                </ul>
                <p style='font-style: italic; color: #666; margin-top: 1rem;'>
                    Idéal pour les "Tiens, et si j'allais à Bordeaux ce week-end ?" 🤔
                </p>
            </div>
        """,
        SearchMode.ROUND_TRIP: """
            <div style='padding: 2rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #1d1d1f; margin-bottom: 1rem;'>🔄 Mode Week-end (Aller-Retour)</h3>
                <p style='font-size: 1.1em; color: #444; margin-bottom: 1rem;'>
                    Pour les planificateurs avisés ! Trouve le combo parfait aller-retour depuis ta ville.
                </p>
                <ul style='color: #666; list-style-type: none; padding-left: 0;'>
                    <li style='margin: 0.5rem 0;'>📅 Choisis tes dates idéales</li>
                    <li style='margin: 0.5rem 0;'>⚡ Trouve les meilleures correspondances en quelques secondes</li>
                    <li style='margin: 0.5rem 0;'>🎯 Fini les allers-retours entre les pages de recherche !</li>
                </ul>
                <p style='font-style: italic; color: #666; margin-top: 1rem;'>
                    PS : Si tu trouves un Paris-Lyon un vendredi soir, joue au loto ! 🎲
                </p>
            </div>
        """,
        SearchMode.ALL_DESTINATIONS: """
            <div style='padding: 2rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='color: #1d1d1f; margin-bottom: 1rem;'>🎯 Mode Chasseur de Trains</h3>
                <p style='font-size: 1.1em; color: #444; margin-bottom: 1rem;'>
                    Pour les opportunistes et les flexibles ! Explore TOUS les trajets disponibles sur une période.
                </p>
                <ul style='color: #666; list-style-type: none; padding-left: 0;'>
                    <li style='margin: 0.5rem 0;'>🔍 Trouve les pépites que personne n'a vues</li>
                    <li style='margin: 0.5rem 0;'>📊 Visualise toutes les options d'un coup d'œil</li>
                    <li style='margin: 0.5rem 0;'>⚡ Idéal pour les voyages de dernière minute</li>
                </ul>
                <p style='font-style: italic; color: #666; margin-top: 1rem;'>
                    Le mode préféré des chasseurs de bonnes occasions ! 🎯
                </p>
            </div>
        """
    }
    st.markdown(mode_descriptions[search_mode], unsafe_allow_html=True) 