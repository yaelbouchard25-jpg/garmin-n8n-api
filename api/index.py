from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if 'test' in self.path:
                self.send_json(200, {'status': '✅ API Working'})
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
        # SIMPLE : EMAIL + PASSWORD (comme GitHub)
        email = os.getenv('GARMIN_EMAIL')
        password = os.getenv('GARMIN_PASSWORD')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().isoformat())
        except:
            date_str = date.today().isoformat()
        
        if not email or not password:
            self.send_json(400, {
                'error': 'Missing GARMIN_EMAIL or GARMIN_PASSWORD',
                'help': 'Add these env variables in Vercel'
            })
            return
        
        try:
            from garminconnect import Garmin
            
            # SIMPLE LOGIN (comme tous les projets GitHub)
            api = Garmin(email, password)
            api.login()
            
            # Structure de base
            data = {
                'date': date_str,
                'status': 'success'
            }
            
            # RÉCUPÉRER LES DONNÉES
            data['steps'] = self.safe_get(lambda: api.get_steps_data(date_str))
            data['heart_rate'] = self.safe_get(lambda: api.get_heart_rates(date_str))
            data['sleep'] = self.safe_get(lambda: api.get_sleep_data(date_str))
            data['stress'] = self.safe_get(lambda: api.get_stress_data(date_str))
            data['body_battery'] = self.safe_get(lambda: api.get_body_battery(date_str, date_str))
            data['hrv'] = self.safe_get(lambda: api.get_hrv_data(date_str))
            data['respiration'] = self.safe_get(lambda: api.get_respiration_data(date_str))
            data['hydration'] = self.safe_get(lambda: api.get_hydration_data(date_str))
            data['spo2'] = self.safe_get(lambda: api.get_spo2_data(date_str))
            
            self.send_json(200, data)
            
        except Exception as e:
            import traceback
            self.send_json(500, {
                'error': str(e),
                'type': type(e).__name__,
                'trace': traceback.format_exc()
            })
    
    def safe_get(self, func):
        try:
            result = func()
            return result if result else None
        except Exception as e:
            return {'error': str(e)}
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_heade
