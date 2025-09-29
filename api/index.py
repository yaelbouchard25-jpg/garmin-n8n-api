from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handler principal"""
        
        try:
            # Route test
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': 'Garmin API working on Vercel',
                    'message': 'Ready to fetch Garmin data',
                    'endpoints': {
                        'test': '/api/index',
                        'garmin': '/api/index?garmin&date=YYYY-MM-DD'
                    },
                    'example': '/api/index?garmin&date=2024-09-28'
                })
                return
            
            # Route Garmin
            elif 'garmin' in self.path:
                self.handle_garmin()
                return
            
            else:
                self.send_json(404, {'error': 'Route not found', 'path': self.path})
                
        except Exception as e:
            self.send_json(500, {
                'error': str(e),
                'traceback': traceback.format_exc()
            })
    
    def handle_garmin(self):
        """Gère les requêtes Garmin"""
        
        debug_info = {}
        
        # Variables d'environnement
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        debug_info['email_configured'] = bool(GARMIN_EMAIL)
        debug_info['password_configured'] = bool(GARMIN_PASSWORD)
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
            debug_info['date_parsed'] = date_str
        except Exception as e:
            date_str = date.today().strftime('%Y-%m-%d')
            debug_info['date_parse_error'] = str(e)
        
        # Vérifier credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            self.send_json(400, {
                'error': 'Garmin credentials not configured in Vercel Environment Variables',
                'date': date_str,
                'debug': debug_info,
                'help': 'Go to Vercel Dashboard > Settings > Environment Variables'
            })
            return
        
        try:
            # Import garminconnect
            debug_info['import_step'] = 'attempting'
            from garminconnect import Garmin
            debug_info['import_step'] = 'success'
            
            # Connexion
            debug_info['login_step'] = 'attempting'
            api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            api.login()
            debug_info['login_step'] = 'success'
            
            # Test simple d'abord
            debug_info['data_fetch_step'] = 'attempting'
            test_stats = api.get_stats(date_str)
            debug_info['data_fetch_step'] = 'success'
            debug_info['has_stats'] = test_stats is not None
            
            # Récupération données complètes
            data = {
                'date': date_str,
                'status': 'success',
                'debug': debug_info,
                
                # DONNÉES ESSENTIELLES
                'sleep_data': self.safe(lambda: api.get_sleep_data(date_str)),
                'stress_data': self.safe(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe(lambda: api.get_body_battery(date_str, date_str)),
                'heart_rate': self.safe(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe(lambda: api.get_rhr_day(date_str)),
                'steps_data': self.safe(lambda: api.get_steps_data(date_str)),
                'stats_data': test_stats,
                'respiration': self.safe(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe(lambda: api.get_hydration_data(date_str)),
            }
            
            self.send_json(200, data)
            
        except Exception as e:
            debug_info['error_details'] = str(e)
            debug_info['error_type'] = type(e).__name__
            debug_info['traceback'] = traceback.format_exc()
            
            self.send_json(500, {
                'error': f'Garmin connection failed: {str(e)}',
                'date': date_str,
                'debug': debug_info
            })
    
    def safe(self, func):
        try:
            return func()
        except Exception as e:
            return {'error': str(e)}
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
