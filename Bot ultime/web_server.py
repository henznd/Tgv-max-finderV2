#!/usr/bin/env python3
"""
Serveur web pour l'interface de configuration du bot d'arbitrage
Avec logs en temps réel et état du compte
"""

import json
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import subprocess
import sys
import glob

# Import du bot d'arbitrage
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from arbitrage_bot_config import execute_simultaneous_trades, load_config
from logger import setup_logger
from trade_verification import TradeVerification

logger = setup_logger("web_server")

# État du bot (pour start/stop)
bot_running = False
bot_process = None
bot_thread = None
last_log_position = {}  # Pour suivre la position dans les fichiers de logs

class ArbitrageBotHandler(BaseHTTPRequestHandler):
    """Handler pour les requêtes HTTP"""
    
    def do_GET(self):
        """Gère les requêtes GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.serve_html()
        elif parsed_path.path == '/api/config':
            self.get_config()
        elif parsed_path.path == '/api/status':
            self.get_status()
        elif parsed_path.path == '/api/logs':
            self.get_logs()
        elif parsed_path.path == '/api/health':
            self.get_health()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Gère les requêtes POST"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/config':
            self.save_config()
        elif parsed_path.path == '/api/launch':
            self.launch_bot()
        elif parsed_path.path == '/api/stop':
            self.stop_bot()
        else:
            self.send_error(404, "Not Found")
    
    def serve_html(self):
        """Sert le fichier HTML de l'interface"""
        html_path = os.path.join(os.path.dirname(__file__), 'web_interface.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'interface: {e}")
            self.send_error(500, f"Erreur: {e}")
    
    def get_config(self):
        """Récupère la configuration actuelle"""
        try:
            config = load_config()
            self.send_json_response(config)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la config: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config = json.loads(post_data.decode('utf-8'))
            
            config_file = os.path.join(os.path.dirname(__file__), 'trading_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration sauvegardée: {config}")
            self.send_json_response({"success": True, "message": "Configuration sauvegardée"})
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def launch_bot(self):
        """Lance le bot d'arbitrage"""
        global bot_running, bot_thread
        
        if bot_running:
            self.send_json_response({"error": "Le bot est déjà en cours d'exécution"}, status=400)
            return
        
        try:
            bot_running = True
            
            # Lancer le bot dans un thread séparé
            bot_thread = threading.Thread(target=run_bot_async, daemon=True)
            bot_thread.start()
            
            logger.info("Bot d'arbitrage lancé")
            self.send_json_response({"success": True, "message": "Bot lancé avec succès"})
        except Exception as e:
            bot_running = False
            logger.error(f"Erreur lors du lancement: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def stop_bot(self):
        """Arrête le bot d'arbitrage"""
        global bot_running
        
        if not bot_running:
            self.send_json_response({"error": "Le bot n'est pas en cours d'exécution"}, status=400)
            return
        
        try:
            bot_running = False
            logger.info("Arrêt du bot demandé")
            self.send_json_response({"success": True, "message": "Arrêt du bot demandé"})
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def get_status(self):
        """Récupère le statut du bot"""
        global bot_running
        self.send_json_response({
            "running": bot_running,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_logs(self):
        """Récupère les logs en temps réel"""
        try:
            # Récupérer les logs du bot d'arbitrage
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            today = datetime.now().strftime('%Y%m%d')
            log_file = os.path.join(log_dir, f'arbitrage_bot_{today}.log')
            
            logs = []
            if os.path.exists(log_file):
                # Lire les dernières lignes du fichier
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Prendre les 100 dernières lignes
                        logs = [line.strip() for line in lines[-100:] if line.strip()]
                except Exception as e:
                    logger.warning(f"Erreur lecture fichier log: {e}")
                    logs = [f"Erreur lecture logs: {e}"]
            else:
                logs = ["Aucun fichier de log trouvé pour aujourd'hui"]
            
            self.send_json_response({
                "logs": logs,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des logs: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def get_health(self):
        """Récupère l'état de santé du compte"""
        try:
            # Lancer la récupération asynchrone dans un thread
            health_data = asyncio.run(get_health_async())
            self.send_json_response(health_data)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état: {e}")
            self.send_json_response({
                "lighter": {"status": "error", "error": str(e)},
                "paradex": {"status": "error", "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    def send_json_response(self, data, status=200):
        """Envoie une réponse JSON"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override pour utiliser notre logger"""
        logger.info(f"{self.address_string()} - {format % args}")

async def get_health_async():
    """Récupère l'état de santé des comptes de manière asynchrone"""
    health_data = {
        "lighter": None,
        "paradex": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Récupérer l'état Lighter
    try:
        verifier = TradeVerification()
        account_state = await verifier._get_lighter_account_state()
        
        if account_state:
            positions = account_state.get("positions", [])
            positions_info = []
            for pos in positions:
                pos_size = float(pos.get("size") or pos.get("base_amount") or pos.get("baseAmount") or 0)
                if abs(pos_size) > 0:
                    market_index = pos.get("market_index") or pos.get("marketIndex")
                    entry_price = float(pos.get("entry_price") or pos.get("entryPrice") or 0)
                    positions_info.append({
                        "market_index": market_index,
                        "size": pos_size,
                        "entry_price": entry_price
                    })
            
            health_data["lighter"] = {
                "status": "ok",
                "total_equity": account_state.get("total_equity"),
                "available_margin": account_state.get("available_margin"),
                "used_margin": account_state.get("used_margin"),
                "positions_count": len(positions_info),
                "positions": positions_info
            }
        else:
            health_data["lighter"] = {"status": "error", "error": "Impossible de récupérer l'état"}
    except Exception as e:
        health_data["lighter"] = {"status": "error", "error": str(e)}
    
    # Récupérer l'état Paradex
    try:
        from paradex_py import Paradex
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'paradex'))
        from paradex_trader_config import L2_PRIVATE_KEY, L1_ADDRESS
        
        paradex = Paradex(env='prod', l2_private_key=L2_PRIVATE_KEY)
        paradex.init_account(l1_address=L1_ADDRESS, l2_private_key=L2_PRIVATE_KEY)
        
        account_summary = paradex.api_client.fetch_account_summary()
        positions = paradex.api_client.fetch_positions()
        
        positions_info = []
        if positions and 'results' in positions:
            for pos in positions['results']:
                if pos.get('status') == 'OPEN':
                    size = float(pos.get('size', 0) or 0)
                    if abs(size) > 0:
                        positions_info.append({
                            "market": pos.get('market'),
                            "size": size,
                            "entry_price": float(pos.get('entry_price') or pos.get('entryPrice') or 0),
                            "liquidation_price": float(pos.get('liquidation_price') or pos.get('liquidationPrice') or 0)
                        })
        
        health_data["paradex"] = {
            "status": "ok",
            "total_equity": account_summary.get("total_equity") if account_summary else None,
            "available_balance": account_summary.get("available_balance") if account_summary else None,
            "margin_used": account_summary.get("margin_used") if account_summary else None,
            "positions_count": len(positions_info),
            "positions": positions_info
        }
    except Exception as e:
        health_data["paradex"] = {"status": "error", "error": str(e)}
    
    return health_data

def run_bot_async():
    """Fonction pour exécuter le bot de manière asynchrone dans un thread"""
    global bot_running
    
    try:
        # Exécuter le bot
        result = asyncio.run(execute_simultaneous_trades(load_config()))
        logger.info(f"Bot terminé: {result}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du bot: {e}")
    finally:
        bot_running = False

def start_server(port=8080):
    """Démarre le serveur web"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ArbitrageBotHandler)
    
    logger.info("=" * 60)
    logger.info("🌐 SERVEUR WEB DÉMARRÉ")
    logger.info("=" * 60)
    logger.info(f"📍 URL: http://localhost:{port}")
    logger.info(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    logger.info("Appuyez sur Ctrl+C pour arrêter le serveur")
    logger.info("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 Arrêt du serveur demandé")
        httpd.shutdown()
        logger.info("✅ Serveur arrêté")

if __name__ == "__main__":
    start_server(port=8080)
