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

# État du bot stratégie (pour start/stop)
strategy_bot_running = False
strategy_bot_process = None
strategy_bot_thread = None
session_reset_timestamp = None  # Timestamp du dernier reset de session
strategy_last_log_position = {}  # Pour suivre la position dans les fichiers de logs

class ArbitrageBotHandler(BaseHTTPRequestHandler):
    """Handler pour les requêtes HTTP"""
    
    def do_GET(self):
        """Gère les requêtes GET"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/' or parsed_path.path == '/index.html':
                self.serve_html()
            elif parsed_path.path == '/strategy' or parsed_path.path == '/strategy.html':
                self.serve_strategy_html()
            elif parsed_path.path == '/api/config':
                self.get_config()
            elif parsed_path.path == '/api/status':
                self.get_status()
            elif parsed_path.path == '/api/logs':
                self.get_logs()
            elif parsed_path.path == '/api/health':
                self.get_health()
            elif parsed_path.path == '/api/strategy-status' or parsed_path.path == '/api/status-strategy':
                self.get_strategy_status()
            elif parsed_path.path == '/api/strategy/logs' or parsed_path.path == '/api/logs-strategy':
                self.get_strategy_logs()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Erreur dans do_GET: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def do_OPTIONS(self):
        """Gère les requêtes OPTIONS pour CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Gère les requêtes POST"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/api/config':
                self.save_config()
            elif parsed_path.path == '/api/launch':
                self.launch_bot()
            elif parsed_path.path == '/api/stop':
                self.stop_bot()
            elif parsed_path.path == '/api/launch-strategy':
                self.launch_strategy_bot()
            elif parsed_path.path == '/api/stop-strategy':
                self.stop_strategy_bot()
            elif parsed_path.path == '/api/strategy/reset':
                self.reset_strategy_session()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Erreur dans do_POST: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
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
    
    def serve_strategy_html(self):
        """Sert le fichier HTML de l'interface stratégie"""
        html_path = os.path.join(os.path.dirname(__file__), 'web_interface_strategy.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'interface stratégie: {e}")
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
            # Récupérer les logs du bot d'arbitrage - utiliser le chemin absolu
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(script_dir, 'logs')
            
            # FORCER l'affichage pour debug
            print(f"[DEBUG] 📂 Recherche logs dans: {log_dir}", flush=True)
            logger.info(f"📂 Recherche logs dans: {log_dir}")
            
            # Chercher les fichiers de log les plus récents (aujourd'hui et hier)
            import glob
            log_pattern = os.path.join(log_dir, 'arbitrage_bot_*.log')
            log_files = sorted(glob.glob(log_pattern), reverse=True)
            
            print(f"[DEBUG] 📁 Fichiers trouvés: {len(log_files)}", flush=True)
            logger.info(f"📁 Fichiers trouvés: {len(log_files)}")
            for f in log_files[:3]:
                size = os.path.getsize(f)
                print(f"[DEBUG]    - {os.path.basename(f)} ({size} bytes)", flush=True)
                logger.info(f"   - {os.path.basename(f)} ({size} bytes)")
            
            logs = []
            if log_files:
                # Lire les logs des fichiers les plus récents (max 2 derniers jours)
                all_lines = []
                for log_file in log_files[:2]:
                    try:
                        file_size = os.path.getsize(log_file)
                        print(f"[DEBUG] 📖 Lecture {os.path.basename(log_file)}: {file_size} bytes", flush=True)
                        logger.info(f"📖 Lecture {os.path.basename(log_file)}: {file_size} bytes")
                        if file_size > 0:
                            with open(log_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                # Filtrer les lignes vides et ajouter seulement celles qui ont du contenu
                                valid_lines = [line.rstrip('\n\r') for line in lines if line.strip()]
                                print(f"[DEBUG]    ✅ {len(valid_lines)} lignes valides", flush=True)
                                logger.info(f"   ✅ {len(valid_lines)} lignes valides")
                                if valid_lines:
                                    # Ajouter le nom du fichier comme séparateur si on lit plusieurs fichiers
                                    if len(log_files) > 1 and log_file != log_files[0] and all_lines:
                                        all_lines.append(f"--- {os.path.basename(log_file)} ---")
                                    all_lines.extend(valid_lines)
                    except Exception as e:
                        import traceback
                        logger.error(f"❌ Erreur lecture fichier log {log_file}: {e}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                
                if all_lines:
                    # Prendre les 200 dernières lignes au total
                    logs = all_lines[-200:]
                    print(f"[DEBUG] 📊 Logs récupérés: {len(logs)} lignes depuis {len(log_files)} fichiers", flush=True)
                    logger.info(f"📊 Logs récupérés: {len(logs)} lignes depuis {len(log_files)} fichiers")
                else:
                    # Vérifier si le fichier d'aujourd'hui existe mais est vide
                    today = datetime.now().strftime('%Y%m%d')
                    today_file = os.path.join(log_dir, f'arbitrage_bot_{today}.log')
                    if os.path.exists(today_file) and os.path.getsize(today_file) == 0:
                        logs = ["⚠️ Le fichier de log d'aujourd'hui existe mais est vide. Le bot est peut-être en cours d'exécution..."]
                    else:
                        logs = ["ℹ️ Aucun log disponible pour le moment."]
                    logger.warning(f"⚠️ Aucune ligne valide trouvée dans les fichiers de log")
            else:
                logs = ["ℹ️ Aucun fichier de log trouvé. Le bot n'a peut-être pas encore été lancé."]
                logger.warning("⚠️ Aucun fichier de log trouvé")
            
            print(f"[DEBUG] 📤 Envoi de {len(logs)} lignes de logs au client", flush=True)
            logger.info(f"📤 Envoi de {len(logs)} lignes de logs au client")
            self.send_json_response({
                "logs": logs,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des logs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_json_response({"error": str(e), "logs": []}, status=500)
    
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
    
    def launch_strategy_bot(self):
        """Lance le bot stratégie"""
        global strategy_bot_running, strategy_bot_thread
        
        if strategy_bot_running:
            self.send_json_response({"error": "Le bot stratégie est déjà en cours d'exécution"}, status=400)
            return
        
        try:
            # Lire les paramètres depuis le body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            params = json.loads(body.decode('utf-8'))
            
            strategy_bot_running = True
            
            # Lancer le bot dans un thread séparé
            strategy_bot_thread = threading.Thread(
                target=run_strategy_bot_async,
                args=(params,),
                daemon=True
            )
            strategy_bot_thread.start()
            
            logger.info(f"Bot stratégie lancé avec paramètres: {params}")
            self.send_json_response({"success": True, "message": "Bot stratégie lancé avec succès"})
        except Exception as e:
            strategy_bot_running = False
            logger.error(f"Erreur lors du lancement du bot stratégie: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_json_response({"error": str(e)}, status=500)
    
    def stop_strategy_bot(self):
        """Arrête le bot stratégie"""
        global strategy_bot_running, strategy_bot_process
        
        if not strategy_bot_running:
            self.send_json_response({"error": "Le bot stratégie n'est pas en cours d'exécution"}, status=400)
            return
        
        try:
            strategy_bot_running = False
            
            # Arrêter le processus si il existe
            if strategy_bot_process:
                try:
                    strategy_bot_process.terminate()
                    strategy_bot_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    strategy_bot_process.kill()
                except Exception as e:
                    logger.warning(f"Erreur lors de l'arrêt du processus: {e}")
                strategy_bot_process = None
            
            # Aussi tuer le processus via pkill au cas où
            try:
                subprocess.run(['pkill', '-f', 'arbitrage_bot_strategy.py'], 
                             capture_output=True, timeout=5)
            except:
                pass
            
            logger.info("Arrêt du bot stratégie demandé")
            self.send_json_response({"success": True, "message": "Arrêt du bot stratégie demandé"})
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du bot stratégie: {e}")
            self.send_json_response({"error": str(e)}, status=500)
    
    def get_strategy_status(self):
        """Récupère le statut du bot stratégie"""
        global strategy_bot_running
        self.send_json_response({
            "running": strategy_bot_running,
            "timestamp": datetime.now().isoformat()
        })
    
    def reset_strategy_session(self):
        """Réinitialise la session : archive les logs et reset les stats"""
        global session_reset_timestamp
        try:
            from datetime import datetime
            import shutil
            import os
            
            # Enregistrer le timestamp du reset
            session_reset_timestamp = datetime.now()
            
            logger.info("=" * 80)
            logger.info("🔄 RESET DE SESSION")
            logger.info("=" * 80)
            logger.info(f"⏰ Timestamp: {session_reset_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("📊 Les statistiques ont été réinitialisées")
            logger.info("📝 Les anciens logs sont toujours accessibles mais ne seront plus affichés")
            logger.info("✨ Nouvelle session démarrée")
            logger.info("=" * 80)
            logger.info("")
            
            # Optionnel : archiver les anciens logs
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(script_dir, 'logs')
            archive_dir = os.path.join(log_dir, 'archives')
            
            # Créer le dossier archives si nécessaire
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
            
            # Copier (pas déplacer) les logs actuels dans archives avec timestamp
            import glob
            log_files = glob.glob(os.path.join(log_dir, 'arbitrage_bot_strategy_*.log'))
            archived_count = 0
            if log_files:
                archive_timestamp = session_reset_timestamp.strftime('%Y%m%d_%H%M%S')
                for log_file in log_files:
                    if os.path.getsize(log_file) > 0:  # Seulement si non vide
                        base_name = os.path.basename(log_file)
                        archive_name = f"archived_{archive_timestamp}_{base_name}"
                        archive_path = os.path.join(archive_dir, archive_name)
                        try:
                            shutil.copy2(log_file, archive_path)
                            logger.info(f"📦 Archivé: {archive_name}")
                            archived_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Impossible d'archiver {base_name}: {e}")
            
            self.send_json_response({
                "success": True,
                "message": "Session réinitialisée avec succès",
                "reset_timestamp": session_reset_timestamp.isoformat(),
                "archived_logs": archived_count
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du reset de session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    def get_strategy_logs(self):
        """Récupère les logs filtrés du bot stratégie (événements importants uniquement)"""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            if not os.path.exists(log_dir):
                self.send_json_response({
                    "logs": [],
                    "stats": {"positions": 0, "trades": 0, "entries": 0, "exits": 0},
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Chercher les fichiers de log du bot stratégie
            log_files = sorted(glob.glob(os.path.join(log_dir, 'arbitrage_bot_strategy_*.log')), reverse=True)
            
            if not log_files:
                self.send_json_response({
                    "logs": ["ℹ️ Aucun log disponible pour le moment."],
                    "stats": {"positions": 0, "trades": 0, "entries": 0, "exits": 0},
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Lire les 2 fichiers les plus récents
            log_files = log_files[:2]
            all_lines = []
            
            for log_file in log_files:
                try:
                    if os.path.getsize(log_file) > 0:
                        # Utiliser tail pour lire les dernières lignes efficacement
                        import subprocess
                        try:
                            # Lire les 2000 dernières lignes avec tail (plus efficace pour gros fichiers)
                            result = subprocess.run(
                                ['tail', '-n', '2000', log_file],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if result.returncode == 0:
                                lines = result.stdout.split('\n')
                                valid_lines = [line.rstrip('\n\r') for line in lines if line.strip()]
                                all_lines.extend(valid_lines)
                            else:
                                # Fallback: lire normalement
                                with open(log_file, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    recent_lines = lines[-2000:] if len(lines) > 2000 else lines
                                    valid_lines = [line.rstrip('\n\r') for line in recent_lines if line.strip()]
                                    all_lines.extend(valid_lines)
                        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                            # Fallback: lire normalement si tail n'est pas disponible
                            with open(log_file, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                recent_lines = lines[-2000:] if len(lines) > 2000 else lines
                                valid_lines = [line.rstrip('\n\r') for line in recent_lines if line.strip()]
                                all_lines.extend(valid_lines)
                except Exception as e:
                    logger.error(f"Erreur lecture fichier log {log_file}: {e}")
            
            # Filtrer les logs APRÈS le reset de session si un reset a eu lieu
            if session_reset_timestamp is not None:
                import re
                from datetime import datetime
                
                filtered_by_reset = []
                for line in all_lines:
                    # Extraire le timestamp de la ligne
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        try:
                            line_timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                            # Garder seulement les lignes APRÈS le reset
                            if line_timestamp >= session_reset_timestamp:
                                filtered_by_reset.append(line)
                        except (ValueError, AttributeError):
                            # Si on ne peut pas parser le timestamp, garder la ligne par défaut
                            filtered_by_reset.append(line)
                    else:
                        # Pas de timestamp, garder la ligne par défaut
                        filtered_by_reset.append(line)
                
                all_lines = filtered_by_reset
                logger.debug(f"🔄 Filtrage post-reset: {len(all_lines)} lignes gardées après {session_reset_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Calculer les statistiques
            stats = {
                "positions": 0,
                "trades": 0,
                "entries": 0,
                "exits": 0
            }
            
            # Compter les entrées et sorties
            for line in all_lines:
                if 'TRADES EXÉCUTÉS AVEC SUCCÈS' in line or 'SIGNAL D\'ENTRÉE DÉTECTÉ' in line:
                    stats["entries"] += 1
                    stats["trades"] += 1
                elif 'POSITION FERMÉE' in line or 'POSITION EXISTANTE FERMÉE' in line:
                    stats["exits"] += 1
            
            # Vérifier s'il y a une position ouverte actuellement
            # En cherchant dans les logs récents si une entrée a été suivie d'une sortie
            recent_lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
            has_open_position = False
            last_entry_index = -1
            for i, line in enumerate(recent_lines):
                if 'TRADES EXÉCUTÉS AVEC SUCCÈS' in line:
                    last_entry_index = i
                    has_open_position = True
                elif 'POSITION FERMÉE' in line and last_entry_index >= 0:
                    has_open_position = False
            
            stats["positions"] = 1 if has_open_position else 0
            
            # Extraire le dernier Z-score depuis les logs (nouvelle version avec 2 Z-scores)
            current_z_score = None
            import re
            from datetime import datetime
            
            # Chercher les nouveaux patterns: "Z-scores: short=X.XX, long=Y.YY"
            lines_with_z = []
            for line in all_lines:
                # Nouveau pattern: "Z-scores: short=X.XX, long=Y.YY"
                z_match = re.search(r'Z-scores:\s*short=([+-]?\d+\.?\d*),\s*long=([+-]?\d+\.?\d*)', line)
                if z_match:
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        try:
                            timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                            z_short = float(z_match.group(1))
                            z_long = float(z_match.group(2))
                            # Utiliser le Z-score le plus élevé pour l'affichage
                            z_value = max(abs(z_short), abs(z_long))
                            lines_with_z.append((timestamp, z_value, line, z_short, z_long))
                        except (ValueError, AttributeError):
                            continue
                else:
                    # Anciens patterns pour rétrocompatibilité
                    z_match = re.search(r'Z-score:\s*([+-]?\d+\.?\d*)', line)
                    if not z_match:
                        z_match = re.search(r'z=([+-]?\d+\.?\d*)', line)
                    if z_match:
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            try:
                                timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                z_value = float(z_match.group(1))
                                lines_with_z.append((timestamp, z_value, line, None, None))
                            except (ValueError, AttributeError):
                                continue
            
            # Si on a trouvé des lignes avec Z-score, prendre la plus récente
            if lines_with_z:
                lines_with_z.sort(key=lambda x: x[0], reverse=True)  # Trier par timestamp décroissant
                most_recent = lines_with_z[0]
                current_z_score = most_recent[1]
                if len(most_recent) > 3 and most_recent[3] is not None:
                    logger.debug(f"📊 Z-scores extraits: short={most_recent[3]:.2f}, long={most_recent[4]:.2f} (max={current_z_score:.2f})")
                else:
                    logger.debug(f"📊 Z-score extrait: {current_z_score} (timestamp: {most_recent[0]})")
            
            if all_lines:
                # Filtrer pour garder UNIQUEMENT les événements critiques
                # L'utilisateur veut juste savoir : bot lancé, entrée, sortie, PnL
                # Filtrer uniquement les événements CRITIQUES (très restreint)
                critical_keywords = [
                '🤖 BOT D\'ARBITRAGE STRATÉGIE',  # Démarrage du bot
                '✅ TRADES EXÉCUTÉS AVEC SUCCÈS',  # Entrée en position confirmée
                '📉 POSITION FERMÉE',  # Sortie de position
                'Direction:',  # Direction du trade (contexte entrée/sortie)
                'PnL:',  # PnL réalisé (contexte sortie)
                'Raison:',  # Raison de sortie (contexte sortie)
                'Z-score entrée:',  # Z-score d'entrée (contexte)
                'Z-score sortie:',  # Z-score de sortie (contexte)
                'Spread entrée:',  # Spread d'entrée (contexte)
                'Spread sortie:',  # Spread de sortie (contexte)
            ]
                
                filtered_logs = []
                current_block = []
                in_important_block = False
                
                for i, line in enumerate(all_lines):
                    # Détecter le début d'un bloc important
                    if any(keyword in line for keyword in ['🤖 BOT', '🎯 SIGNAL D\'ENTRÉE', '📉 POSITION FERMÉE', '✅ TRADES']):
                        # Si on était déjà dans un bloc, l'ajouter avant de commencer le nouveau
                        if current_block:
                            filtered_logs.extend(current_block)
                            current_block = []
                        in_important_block = True
                        current_block.append(line)
                    # Si on est dans un bloc important
                    elif in_important_block:
                        # Continuer à ajouter des lignes jusqu'à trouver une ligne vide ou un séparateur
                        if line.strip() == '' or line.startswith('='):
                            current_block.append(line)
                            # Si c'est un séparateur de fin, arrêter le bloc
                            if line.startswith('=') and len(current_block) > 3:
                                filtered_logs.extend(current_block)
                                current_block = []
                                in_important_block = False
                        else:
                            # Garder les détails importants (Direction, PnL, Z-score, etc.)
                            if any(keyword in line for keyword in critical_keywords):
                                current_block.append(line)
                
                # Ajouter le dernier bloc si nécessaire
                if current_block:
                    filtered_logs.extend(current_block)
                
                # Prendre les 150 dernières lignes filtrées pour avoir assez de contexte
                logs = filtered_logs[-150:] if len(filtered_logs) > 150 else filtered_logs
                
                # Debug: logger le nombre de logs trouvés
                logger.debug(f"📊 Logs filtrés: {len(filtered_logs)} lignes, retournant les {len(logs)} dernières")
            else:
                logs = ["ℹ️ Aucun log disponible pour le moment."]
            
            # Ajouter un timestamp pour éviter le cache du navigateur
            response = {
                "logs": logs,
                "stats": stats,
                "z_score": current_z_score,
                "timestamp": datetime.now().isoformat(),
                "cache_buster": datetime.now().timestamp()
            }
            self.send_json_response(response)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des logs stratégie: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.send_json_response({"error": str(e), "logs": []}, status=500)
    
    def send_json_response(self, data, status=200):
        """Envoie une réponse JSON"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        try:
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            self.wfile.write(json_data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erreur sérialisation JSON: {e}")
            error_data = json.dumps({"error": "Erreur de sérialisation", "details": str(e)}, ensure_ascii=False)
            self.wfile.write(error_data.encode('utf-8'))
    
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
                # AccountApi utilise 'position' (string) pour la taille, mappé aussi à 'size' et 'base_amount'
                pos_size = float(pos.get("position") or pos.get("size") or pos.get("base_amount") or pos.get("baseAmount") or 0)
                if abs(pos_size) > 0:
                    # AccountApi utilise 'market_id' (mappé à 'market_index' dans _get_lighter_account_state)
                    market_index = pos.get("market_index") or pos.get("market_id") or pos.get("marketIndex")
                    # AccountApi utilise 'avg_entry_price' (mappé à 'entry_price' dans _get_lighter_account_state)
                    entry_price = float(pos.get("entry_price") or pos.get("avg_entry_price") or pos.get("entryPrice") or 0)
                    # Prix de liquidation depuis additional_properties
                    liquidation_price = float(pos.get("liquidation_price") or 0)
                    # Symbol pour identifier le token
                    symbol = pos.get("symbol")
                    
                    positions_info.append({
                        "market_index": market_index,
                        "market_id": market_index,  # Alias pour compatibilité
                        "size": pos_size,
                        "position": pos_size,  # Alias pour compatibilité
                        "entry_price": entry_price,
                        "avg_entry_price": entry_price,  # Alias pour compatibilité
                        "liquidation_price": liquidation_price,
                        "symbol": symbol
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
            health_data["lighter"] = {
                "status": "error", 
                "error": "L'API Lighter ne fournit pas d'endpoint public pour récupérer l'état du compte (positions, balances). Vérifiez votre compte directement sur l'interface Lighter."
            }
    except Exception as e:
        import traceback
        error_msg = str(e)
        # Si c'est une erreur de connexion, donner plus de détails
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            error_msg = f"Erreur de connexion à l'API Lighter: {error_msg}"
        health_data["lighter"] = {"status": "error", "error": error_msg}
    
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
        
        # AccountSummary peut être un objet ou un dict, gérer les deux cas
        total_equity = None
        available_balance = None
        margin_used = None
        
        if account_summary:
            if isinstance(account_summary, dict):
                # Paradex utilise account_value pour l'equity totale
                total_equity = account_summary.get("account_value") or account_summary.get("total_equity")
                # Paradex utilise free_collateral pour la balance disponible
                available_balance = account_summary.get("free_collateral") or account_summary.get("available_balance")
                # Paradex utilise initial_margin_requirement pour la marge utilisée
                margin_used = account_summary.get("initial_margin_requirement") or account_summary.get("margin_used")
            else:
                # C'est un objet, utiliser getattr avec les bons noms d'attributs Paradex
                total_equity = getattr(account_summary, 'account_value', None) or getattr(account_summary, 'total_equity', None)
                available_balance = getattr(account_summary, 'free_collateral', None) or getattr(account_summary, 'available_balance', None)
                margin_used = getattr(account_summary, 'initial_margin_requirement', None) or getattr(account_summary, 'margin_used', None)
            
            # Convertir les strings en float (Paradex retourne des strings)
            try:
                if total_equity is not None:
                    total_equity = float(total_equity) if isinstance(total_equity, str) else total_equity
            except (ValueError, TypeError):
                total_equity = None
            
            try:
                if available_balance is not None:
                    available_balance = float(available_balance) if isinstance(available_balance, str) else available_balance
            except (ValueError, TypeError):
                available_balance = None
            
            try:
                if margin_used is not None:
                    margin_used = float(margin_used) if isinstance(margin_used, str) else margin_used
            except (ValueError, TypeError):
                margin_used = None
        
        health_data["paradex"] = {
            "status": "ok",
            "total_equity": total_equity,
            "available_balance": available_balance,
            "margin_used": margin_used,
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
        # S'assurer que le logger est initialisé dans ce thread
        from logger import setup_logger
        bot_logger = setup_logger("arbitrage_bot")
        bot_logger.info("=" * 60)
        bot_logger.info("🤖 BOT D'ARBITRAGE - DÉMARRAGE")
        bot_logger.info("=" * 60)
        
        # Exécuter le bot
        result = asyncio.run(execute_simultaneous_trades(load_config()))
        bot_logger.info(f"Bot terminé: {result}")
        
        # Forcer le flush des logs
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        for handler in bot_logger.handlers:
            if hasattr(handler, 'stream') and handler.stream:
                handler.stream.flush()
    except Exception as e:
        from logger import setup_logger
        bot_logger = setup_logger("arbitrage_bot")
        bot_logger.error(f"Erreur lors de l'exécution du bot: {e}")
        import traceback
        bot_logger.error(traceback.format_exc())
        # Forcer le flush
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        bot_running = False

def run_strategy_bot_async(params):
    """Fonction pour exécuter le bot stratégie de manière asynchrone"""
    global strategy_bot_running, strategy_bot_process
    
    try:
        from logger import setup_logger
        bot_logger = setup_logger("arbitrage_bot_strategy")
        
        # Construire la commande
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'arbitrage_bot_strategy.py'),
            '--token', params['token'],
            '--margin', str(params['margin']),
            '--leverage', str(params['leverage']),
            '--entry-z', str(params['entry_z']),
            '--exit-z', str(params['exit_z']),
            '--stop-z', str(params['stop_z'])
        ]
        
        bot_logger.info(f"🚀 Lancement du bot stratégie avec: {params}")
        
        # Lancer le processus
        strategy_bot_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Lire la sortie en temps réel
        for line in strategy_bot_process.stdout:
            if not strategy_bot_running:
                break
            if line.strip():
                bot_logger.info(line.strip())
        
        strategy_bot_process.wait()
        
    except Exception as e:
        from logger import setup_logger
        bot_logger = setup_logger("arbitrage_bot_strategy")
        bot_logger.error(f"Erreur lors de l'exécution du bot stratégie: {e}")
        import traceback
        bot_logger.error(traceback.format_exc())
    finally:
        strategy_bot_running = False
        strategy_bot_process = None

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
