from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handler principal - gère toutes les routes"""
        
        try:
            # Route test simple
            if self.path == '/test' or self.path == '/':
                self.send_json_response(200, {
                    'status': 'API Garmin working on Vercel',
                    'message': 'Single file at root - SUCCESS',
                    'endpoints': {
                        'test': '/test',
                        'garmin': '/garmin/YYYY-MM-DD',
                        'example': '/garmin/2024-09-28'
                    },
                    'path_received': self.path
                })
                return
            
            # Route Garmin data
            elif self.path.startswith('/garmin/'):
                self.handle_garmin_request()
                return
            
            # Route inconnue
            else:
                self.send_json_response(404, {
                    'error': 'Route not found',
                    'path': self.path,
                    'available_routes': ['/test', '/garmin/YYYY-MM-DD']
                })
                
        except Exception as e:
            self.send_json_response(500, {
                'error': f'Server error: {str(e)}',
                'error_type': type(e).__name__,
                'path': self.path
            })
    
    def handle_garmin_request(self):
        """Gère les requêtes Garmin"""
        
        # Variables d'environnement
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        # Extraire la date de l'URL
        try:
            date_str = self.path.split('/garmin/')[-1]
            if not date_str or len(date_str) != 10:
                date_str = date.today().strftime('%Y-%m-%d')
        except:
            date_str = date.today().strftime('%Y-%m-%d')
        
        # Vérifier credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            self.send_json_response(400, {
                'error': 'Garmin credentials not configured',
                'date': date_str,
                'help': 'Configure GARMIN_EMAIL and GARMIN_PASSWORD in Vercel environment variables'
            })
            return
        
        try:
            # Import et connexion Garmin
            from garminconnect import Garmin
            
            api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            api.login()
            
            # Récupération des données essentielles
            garmin_data = {
                'date': date_str,
                'status': 'success',
                'timestamp': date.today().isoformat(),
                
                # DONNÉES PRINCIPALES
                'sleep_data': self.safe_call(lambda: api.get_sleep_data(date_str)),
                'stress_data': self.safe_call(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe_call(lambda: api.get_body_battery(date_str, date_str)),
                'heart_rate': self.safe_call(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe_call(lambda: api.get_rhr_day(date_str)),
                'steps_data': self.safe_call(lambda: api.get_steps_data(date_str)),
                'stats_data': self.safe_call(lambda: api.get_stats(date_str)),
                
                # DONNÉES SUPPLÉMENTAIRES
                'respiration': self.safe_call(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe_call(lambda: api.get_hydration_data(date_str)),
                'training_status': self.safe_call(lambda: api.get_training_status(date_str)),
            }
            
            self.send_json_response(200, garmin_data)
            
        except Exception as e:
            self.send_json_response(500, {
                'error': f'Garmin connection failed: {str(e)}',
                'date': date_str,
                'error_type': type(e).__name__
            })
    
    def safe_call(self, func):
        """Wrapper sécurisé pour appels API"""
        try:
            return func()
        except Exception as e:
            return {'error': str(e)}
    
    def send_json_response(self, status_code, data):
        """Envoie une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2, default=str)
        self.wfile.write(response.encode('utf-8'))
