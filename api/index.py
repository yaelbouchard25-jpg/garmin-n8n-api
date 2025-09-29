from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date, datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': '✅ Garmin API Working',
                    'current_date': date.today().isoformat(),
                    'endpoints': {
                        'test': '/api/index',
                        'garmin_today': f'/api/index?garmin&date={date.today().isoformat()}',
                        'garmin_custom': '/api/index?garmin&date=YYYY-MM-DD'
                    }
                })
                return
            
            elif 'garmin' in self.path:
                self.handle_garmin()
                return
            
            else:
                self.send_json(404, {'error': 'Not found'})
                
        except Exception as e:
            import traceback
            self.send_json(500, {'error': str(e), 'trace': traceback.format_exc()})
    
    def handle_garmin(self):
        oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
        oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().isoformat())
        except:
            date_str = date.today().isoformat()
        
        # Validation date
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if parsed_date > date.today():
                self.send_json(400, {
                    'error': 'Future date requested',
                    'requested_date': date_str,
                    'current_date': date.today().isoformat(),
                    'message': 'Cannot fetch data for future dates. Garmin has no data yet!'
                })
                return
        except:
            pass
        
        if not oauth1_str or not oauth2_str:
            self.send_json(400, {'error': 'Tokens not configured'})
            return
        
        try:
            import garth
            from garminconnect import Garmin
            from garth.auth_tokens import OAuth1Token, OAuth2Token
            
            # Parser et créer tokens
            oauth1_data = json.loads(oauth1_str)
            oauth2_data = json.loads(oauth2_str)
            oauth1_token = OAuth1Token(**oauth1_data)
            oauth2_token = OAuth2Token(**oauth2_data)
            
            # Créer client et assigner tokens
            api = Garmin()
            api.garth.oauth1_token = oauth1_token
            api.garth.oauth2_token = oauth2_token
            
            # Récupérer TOUTES les données
            data = {
                'date': date_str,
                'status': 'success',
                'current_date': date.today().isoformat(),
                
                # Stats générales
                'user_summary': self.safe_call(lambda: api.get_user_summary(date_str)),
                'stats': self.safe_call(lambda: api.get_stats(date_str)),
                
                # Activité
                'steps': self.safe_call(lambda: api.get_steps_data(date_str)),
                'floors': self.safe_call(lambda: api.get_floors(date_str)),
                
                # Coeur
                'heart_rate': self.safe_call(lambda: api.get_heart_rates(date_str)),
                'resting_hr': self.safe_call(lambda: api.get_rhr_day(date_str)),
                'hrv': self.safe_call(lambda: api.get_hrv_data(date_str)),
                
                # Sommeil
                'sleep': self.safe_call(lambda: api.get_sleep_data(date_str)),
                
                # Stress & Récupération
                'stress': self.safe_call(lambda: api.get_stress_data(date_str)),
                'body_battery': self.safe_call(lambda: api.get_body_battery(date_str, date_str)),
                'training_status': self.safe_call(lambda: api.get_training_status(date_str)),
                
                # Respiration & Hydratation
                'respiration': self.safe_call(lambda: api.get_respiration_data(date_str)),
                'hydration': self.safe_call(lambda: api.get_hydration_data(date_str)),
                'spo2': self.safe_call(lambda: api.get_spo2_data(date_str)),
            }
            
            # Vérifier si on a des données
            has_data = any(
                v and v != [] and 'error' not in str(v)
                for k, v in data.items() 
                if k not in ['date', 'status', 'current_date']
            )
            
            if not has_data:
                data['warning'] = 'No data returned. Check: 1) Date is not in future, 2) You wore Garmin watch that day, 3) Data synced to Garmin Connect'
            
            self.send_json(200, data)
            
        except Exception as e:
            import traceback
            self.send_json(500, {
                'error': str(e),
                'type': type(e).__name__,
                'trace': traceback.format_exc()
            })
    
    def safe_call(self, func):
        try:
            result = func()
            if result is None or result == [] or result == {}:
                return None
            return result
        except Exception as e:
            return {'error': str(e), 'type': type(e).__name__}
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
