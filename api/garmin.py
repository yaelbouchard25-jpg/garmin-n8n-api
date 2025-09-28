from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Variables d'environnement
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        # Parse l'URL
        path = self.path
        
        try:
            # Extract date from path /api/garmin/2024-09-28
            if '/api/garmin/' in path:
                date_str = path.split('/api/garmin/')[-1]
            else:
                date_str = date.today().strftime('%Y-%m-%d')
            
            # Import et connexion Garmin
            from garminconnect import Garmin
            
            api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            api.login()
            
            # Récupération des données
            all_data = {
                'date': date_str,
                'status': 'success',
                
                # SOMMEIL
                'sleep_data': safe_api_call(lambda: api.get_sleep_data(date_str)),
                
                # STRESS & RÉCUPÉRATION  
                'stress_data': safe_api_call(lambda: api.get_stress_data(date_str)),
                'body_battery': safe_api_call(lambda: api.get_body_battery(date_str, date_str)),
                
                # FRÉQUENCE CARDIAQUE
                'heart_rate': safe_api_call(lambda: api.get_heart_rates(date_str)),
                'resting_hr': safe_api_call(lambda: api.get_rhr_day(date_str)),
                
                # ACTIVITÉ
                'steps_data': safe_api_call(lambda: api.get_steps_data(date_str)),
                'stats_data': safe_api_call(lambda: api.get_stats(date_str)),
                
                # AUTRES
                'respiration': safe_api_call(lambda: api.get_respiration_data(date_str)),
                'hydration': safe_api_call(lambda: api.get_hydration_data(date_str)),
            }
            
            # Réponse JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps(all_data)
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                'date': date_str if 'date_str' in locals() else 'unknown',
                'status': 'error',
                'error': str(e)
            }
            
            response = json.dumps(error_response)
            self.wfile.write(response.encode())

def safe_api_call(func):
    """Wrapper pour éviter les erreurs"""
    try:
        return func()
    except:
        return None
