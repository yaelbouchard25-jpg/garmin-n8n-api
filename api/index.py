from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handler principal"""
        
        try:
            # Route test
            if 'test' in self.path or self.path == '/api/index':
                self.send_json(200, {
                    'status': 'Garmin API working on Vercel',
                    'message': 'API folder structure SUCCESS',
                    'endpoints': {
                        'test': '/api/index',
                        'garmin': '/api/garmin?date=YYYY-MM-DD'
                    }
                })
                return
            
            # Route Garmin
            elif 'garmin' in self.path:
                self.handle_garmin()
                return
            
            else:
                self.send_json(404, {'error': 'Route not found'})
                
        except Exception as e:
            self.send_json(500, {'error': str(e)})
    
    def handle_garmin(self):
        """Gère les requêtes Garmin"""
        
        # Variables d'environnement
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        # Parse date depuis query string
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
        except:
            date_str = date.today().strftime('%Y-%m-%d')
        
        # Vérifier credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            self.send_json(400, {
                'error': 'Configure GARMIN_EMAIL and GARMIN_PASSWORD in Vercel',
                'date': date_str
            })
            return
        
        try:
            from garminconnect import Garmin
            
            api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            api.login()
            
            # Récupération données
            data = {
                'date': date_str,
                'status': 'success',
                'sleep_data': self.safe(lambda: api.get_sleep_data(date_str)),
                'stress_data': self.safe(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe(lambda: api.get_body_battery(date_str, date_str)),
                'heart_rate': self.safe(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe(lambda: api.get_rhr_day(date_str)),
                'steps_data': self.safe(lambda: api.get_steps_data(date_str)),
                'stats_data': self.safe(lambda: api.get_stats(date_str)),
                'respiration': self.safe(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe(lambda: api.get_hydration_data(date_str)),
            }
            
            self.send_json(200, data)
            
        except Exception as e:
            self.send_json(500, {
                'error': f'Garmin failed: {str(e)}',
                'date': date_str
            })
    
    def safe(self, func):
        try:
            return func()
        except:
            return None
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
