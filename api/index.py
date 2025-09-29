from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse la date de l'URL
            query = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            target_date = params.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Connexion Garmin
            from garminconnect import Garmin
            
            email = os.getenv('GARMIN_EMAIL')
            password = os.getenv('GARMIN_PASSWORD')
            
            if not email or not password:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Missing credentials',
                    'help': 'Add GARMIN_EMAIL and GARMIN_PASSWORD in Vercel env variables'
                }).encode())
                return
            
            # Connexion
            client = Garmin(email, password)
            client.login()
            
            # RÉCUPÉRATION DES DONNÉES BRUTES
            raw_data = client.get_stats(target_date)
            
            # ENVOI DES DONNÉES BRUTES POUR DEBUG
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # On renvoie TOUT pour voir la structure
            debug_response = {
                'date': target_date,
                'status': 'debug_mode',
                'raw_data_type': str(type(raw_data)),
                'raw_data': raw_data,
                'raw_data_keys': list(raw_data.keys()) if isinstance(raw_data, dict) else 'NOT_A_DICT'
            }
            
            self.wfile.write(json.dumps(debug_response, indent=2, default=str).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc(),
                'date': target_date if 'target_date' in locals() else 'unknown'
            }, indent=2).encode())
