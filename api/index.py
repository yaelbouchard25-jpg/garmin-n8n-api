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
        oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
        oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
        display_name = os.getenv('GARMIN_DISPLAY_NAME')
        full_name = os.getenv('GARMIN_FULL_NAME')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().isoformat())
        except:
            date_str = date.today().isoformat()
        
        if not all([oauth1_str, oauth2_str, display_name]):
            self.send_json(400, {'error': 'Missing credentials'})
            return
        
        try:
            import garth
            from garminconnect import Garmin
            from garth.auth_tokens import OAuth1Token, OAuth2Token
            
            # Parser tokens
            oauth1_data = json.loads(oauth1_str)
            oauth2_data = json.loads(oauth2_str)
            oauth1_token = OAuth1Token(**oauth1_data)
            oauth2_token = OAuth2Token(**oauth2_data)
            
            # Créer client
            api = Garmin()
            api.garth.oauth1_token = oauth1_token
            api.garth.oauth2_token = oauth2_token
            api.display_name = display_name
            api.full_name = full_name if full_name else "User"
            
            # MODE DEBUG : Afficher les données brutes
            data = {
                'date': date_str,
                'status': 'debug_mode',
                'profile': {
                    'display_name': display_name,
                    'full_name': full_name
                },
                'raw_data': {}
            }
            
            # STEPS - DEBUG
            try:
                steps_raw = api.get_steps_data(date_str)
                data['raw_data']['steps'] = {
                    'type': str(type(steps_raw)),
                    'length': len(steps_raw) if isinstance(steps_raw, (list, dict)) else 'N/A',
                    'data': steps_raw
                }
            except Exception as e:
                data['raw_data']['steps'] = {'error': str(e)}
            
            # HEART RATE - DEBUG
            try:
                hr_raw = api.get_heart_rates(date_str)
                data['raw_data']['heart_rate'] = {
                    'type': str(type(hr_raw)),
                    'length': len(hr_raw) if isinstance(hr_raw, (list, dict)) else 'N/A',
                    'data': hr_raw
                }
            except Exception as e:
                data['raw_data']['heart_rate'] = {'error': str(e)}
            
            # SLEEP - DEBUG
            try:
                sleep_raw = api.get_sleep_data(date_str)
                data['raw_data']['sleep'] = {
                    'type': str(type(sleep_raw)),
                    'keys': list(sleep_raw.keys()) if isinstance(sleep_raw, dict) else 'N/A',
                    'data': sleep_raw
                }
            except Exception as e:
                data['raw_data']['sleep'] = {'error': str(e)}
            
            # BODY BATTERY - DEBUG
            try:
                bb_raw = api.get_body_battery(date_str, date_str)
                data['raw_data']['body_battery'] = {
                    'type': str(type(bb_raw)),
                    'length': len(bb_raw) if isinstance(bb_raw, (list, dict)) else 'N/A',
                    'data': bb_raw
                }
            except Exception as e:
                data['raw_data']['body_battery'] = {'error': str(e)}
            
            self.send_json(200, data)
            
        except Exception as e:
            import traceback
            self.send_json(500, {
                'error': str(e),
                'type': type(e).__name__,
                'trace': traceback.format_exc()
            })
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
