from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': '✅ FIXED - Tokens assigned to Garmin instance',
                    'version': 'v2.0-WORKING',
                    'tokens': {
                        'oauth1': bool(os.getenv('GARMIN_OAUTH1_TOKEN')),
                        'oauth2': bool(os.getenv('GARMIN_OAUTH2_TOKEN'))
                    }
                })
                return
            
            elif 'garmin' in self.path:
                self.handle_garmin_fixed()
                return
            
            else:
                self.send_json(404, {'error': 'Not found'})
                
        except Exception as e:
            import traceback
            self.send_json(500, {'error': str(e), 'trace': traceback.format_exc()})
    
    def handle_garmin_fixed(self):
        """Version CORRIGÉE avec tokens assignés à l'instance Garmin"""
        
        # Récupérer tokens
        oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
        oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
        except:
            date_str = date.today().strftime('%Y-%m-%d')
        
        if not oauth1_str or not oauth2_str:
            self.send_json(400, {'error': 'Tokens not configured'})
            return
        
        try:
            import garth
            from garminconnect import Garmin
            from garth.auth_tokens import OAuth1Token, OAuth2Token
            
            # Parser tokens
            oauth1_data = json.loads(oauth1_str)
            oauth2_data = json.loads(oauth2_str)
            
            # Créer objets token
            oauth1_token = OAuth1Token(**oauth1_data)
            oauth2_token = OAuth2Token(**oauth2_data)
            
            # ✅ FIX: Créer client Garmin PUIS assigner tokens à SON instance garth
            api = Garmin()
            
            # CRITIQUE: Assigner tokens à l'instance garth du client Garmin
            api.garth.oauth1_token = oauth1_token
            api.garth.oauth2_token = oauth2_token
            
            # Maintenant les appels vont marcher !
            data = {
                'date': date_str,
                'status': 'success',
                
                # DONNÉES COMPLÈTES
                'stats': self.safe(lambda: api.get_stats(date_str)),
                'steps': self.safe(lambda: api.get_steps_data(date_str)),
                'heart_rate': self.safe(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe(lambda: api.get_rhr_day(date_str)),
                'sleep': self.safe(lambda: api.get_sleep_data(date_str)),
                'stress': self.safe(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe(lambda: api.get_body_battery(date_str, date_str)),
                'respiration': self.safe(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe(lambda: api.get_hydration_data(date_str)),
                'hrv': self.safe(lambda: api.get_hrv_data(date_str)),
                'training_status': self.safe(lambda: api.get_training_status(date_str)),
            }
            
            self.send_json(200, data)
            
        except Exception as e:
            import traceback
            self.send_json(500, {
                'error': str(e),
                'type': type(e).__name__,
                'trace': traceback.format_exc()
            })
    
    def safe(self, func):
        try:
            result = func()
            return result if result is not None else {'note': 'no data for this date'}
        except Exception as e:
            return {'error': str(e)}
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
