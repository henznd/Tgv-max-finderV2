from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, List

from api_utils import get_tgvmax_trains, format_single_trips, group_trains_by_destination

app = FastAPI()

# Configuration CORS pour autoriser les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou l'URL de votre frontend Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/trains/single")
async def find_single_trip(
    date: str,
    origin: str,
    destination: Optional[str] = None,
):
    """
    Endpoint pour trouver des trajets aller simple.
    """
    trains = get_tgvmax_trains(date, origin, destination)
    if destination:
        # Si une destination spécifique est demandée, retourner la liste simple
        df = format_single_trips(trains)
        return df.to_dict(orient="records")
    else:
        # Sinon, grouper par destination
        return group_trains_by_destination(trains)

@app.get("/api/trains/round-trip")
async def find_round_trip(
    depart_date: str,
    return_date: str,
    origin: str,
):
    """
    Endpoint pour trouver des trajets aller-retour.
    """
    # Récupérer les trains aller
    outbound_trains = get_tgvmax_trains(depart_date, origin)
    
    # Récupérer toutes les destinations atteignables à l'aller
    destinations_aller = sorted(set(t['destination'] for t in outbound_trains))
    
    all_results = []
    for dest in destinations_aller:
        try:
            # Récupérer les trains retour pour cette destination
            inbound_trains = get_tgvmax_trains(return_date, dest, origin)
            
            # Formater les résultats
            df_aller = format_single_trips([t for t in outbound_trains if t['destination'] == dest])
            df_retour = format_single_trips(inbound_trains)
            
            # Si on a des trains aller et retour, on ajoute le résultat
            if not df_aller.empty and not df_retour.empty:
                all_results.append({
                    "destination": dest,
                    "aller": df_aller.to_dict(orient="records"),
                    "retour": df_retour.to_dict(orient="records")
                })
        except Exception as e:
            # On ignore l'erreur API pour cette destination
            continue
    
    return all_results

@app.get("/api/trains/range")
async def find_date_range_trips(
    start_date: str,
    days: int,
    origin: str,
    destination: Optional[str] = None,
):
    """
    Endpoint pour trouver des trajets sur une plage de dates.
    """
    all_trains = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    for i in range(days):
        date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
        trains = get_tgvmax_trains(date_str, origin, destination)
        all_trains.extend(trains)
    
    if destination:
        # Si une destination spécifique est demandée, retourner la liste simple
        df = format_single_trips(all_trains)
        return df.to_dict(orient="records")
    else:
        # Sinon, grouper par destination
        return group_trains_by_destination(all_trains)

@app.get("/")
def read_root():
    return {"message": "Welcome to TGVmax Finder API"} 