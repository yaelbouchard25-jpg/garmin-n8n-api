from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Route test
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': '✅ Garmin API - OAuth Tokens (2FA Compatible)',
                    'version': 'FINAL',
                    'tokens_configured': {
                        'oauth1': bool(os.getenv('GARMIN_OAUTH1_TOKEN')),
                        'oauth2': bool(os.getenv('GARMIN_OAUTH2_TOKEN'))
                    },
                    'endpoints': {
                        'test': '/api/index',
                        'garmin': '/api/index?garmin&date=2024-09-28'
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
        """Récupère les données Garmin avec OAuth tokens"""
        
        # Récupérer les tokens depuis variables d'environnement
        oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
        oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
        except:
            date_str = date.today().strftime('%Y-%m-%d')
        
        # Vérifier que les tokens existent
        if not oauth1_str or not oauth2_str:
            self.send_json(400, {
                'error': 'OAuth tokens not configured',
                'help': 'Add GARMIN_OAUTH1_TOKEN and GARMIN_OAUTH2_TOKEN in Vercel',
                'oauth1_set': bool(oauth1_str),
                'oauth2_set': bool(oauth2_str)
            })
            return
        
        try:
            import garth
            from garminconnect import Garmin
            
            # Parser les tokens JSON
            oauth1_token = json.loads(oauth1_str)
            oauth2_token = json.loads(oauth2_str)
            
            # Créer objets token pour garth
            from garth.auth_tokens import OAuth1Token, OAuth2Token
            
            garth.client.oauth1_token = OAuth1Token(**oauth1_token)
            garth.client.oauth2_token = OAuth2Token(**oauth2_token)
            
            # Créer client Garmin (pas besoin de login!)
            api = Garmin()
            
            # Récupérer TOUTES les données
            data = {
                'date': date_str,
                'status': 'success',
                'auth_method': 'oauth_tokens',
                
                # DONNÉES COMPLÈTES
                'sleep_data': self.safe(lambda: api.get_sleep_data(date_str)),
                'stress_data': self.safe(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe(lambda: api.get_body_battery(date_str, date_str)),
                'heart_rate': self.safe(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe(lambda: api.get_rhr_day(date_str)),
                'hrv_data': self.safe(lambda: api.get_hrv_data(date_str)),
                'steps_data': self.safe(lambda: api.get_steps_data(date_str)),
                'stats_data': self.safe(lambda: api.get_stats(date_str)),
                'respiration': self.safe(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe(lambda: api.get_hydration_data(date_str)),
                'training_status': self.safe(lambda: api.get_training_status(date_str)),
            }
            
            self.send_json(200, data)
            
        except Exception as e:
            import traceback
            self.send_json(500, {
                'error': f'Garmin API failed: {str(e)}',
                'date': date_str,
                'traceback': traceback.format_exc()
            })
    
    def safe(self, func):
        """Wrapper pour éviter les erreurs"""
        try:
            return func()
        except:
            return None
    
    def send_json(self, code, data):
        """Envoie une réponse JSON"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
