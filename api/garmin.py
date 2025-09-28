from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handler GET pour Vercel"""
        
        try:
            # Variables d'environnement
            GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
            GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
            
            # Debug info
            debug_info = {
                'step': 'env_check',
                'email_set': bool(GARMIN_EMAIL),
                'password_set': bool(GARMIN_PASSWORD),
                'path': self.path
            }
            
            # Vérifier credentials
            if not GARMIN_EMAIL or not GARMIN_PASSWORD:
                self.send_error_response(400, {
                    'error': 'Missing Garmin credentials',
                    'debug': debug_info
                })
                return
            
            # Parse date depuis URL
            if '/api/garmin/' in self.path:
                date_str = self.path.split('/api/garmin/')[-1]
            else:
                date_str = date.today().strftime('%Y-%m-%d')
            
            debug_info['date_parsed'] = date_str
            
            # Test import garminconnect
            try:
                from garminconnect import Garmin
                debug_info['import_success'] = True
            except Exception as e:
                self.send_error_response(500, {
                    'error': f'Import failed: {str(e)}',
                    'debug': debug_info
                })
                return
            
            # Test connexion Garmin
            try:
                api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
                api.login()
                debug_info['login_success'] = True
                
                # Test récupération données simple
                stats = api.get_stats(date_str)
                debug_info['data_success'] = True
                
                # Données basiques pour commencer
                simple_data = {
                    'date': date_str,
                    'status': 'success',
                    'debug': debug_info,
                    'has_stats': stats is not None,
                    'stats_type': str(type(stats)) if stats else None
                }
                
                self.send_success_response(simple_data)
                
            except Exception as e:
                debug_info['garmin_error'] = str(e)
                self.send_error_response(500, {
                    'error': f'Garmin connection failed: {str(e)}',
                    'debug': debug_info
                })
                
        except Exception as e:
            self.send_error_response(500, {
                'error': f'General error: {str(e)}',
                'error_type': type(e).__name__
            })
    
    def send_success_response(self, data):
        """Envoie une réponse de succès"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_response(self, status_code, data):
        """Envoie une réponse d'erreur"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
