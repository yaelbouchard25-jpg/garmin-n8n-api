from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
import traceback
import time

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handler principal"""
        
        try:
            # Route test
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': 'Garmin API working on Vercel',
                    'message': 'Ready to fetch Garmin data',
                    'version': '2.0-auth-fixed',
                    'endpoints': {
                        'test': '/api/index',
                        'garmin': '/api/index?garmin&date=YYYY-MM-DD',
                        'test_credentials': '/api/index?test_auth'
                    }
                })
                return
            
            # Route test auth
            elif 'test_auth' in self.path:
                self.test_credentials()
                return
            
            # Route Garmin
            elif 'garmin' in self.path:
                self.handle_garmin()
                return
            
            else:
                self.send_json(404, {'error': 'Route not found'})
                
        except Exception as e:
            self.send_json(500, {'error': str(e), 'traceback': traceback.format_exc()})
    
    def test_credentials(self):
        """Test uniquement les credentials"""
        
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        result = {
            'email_configured': bool(GARMIN_EMAIL),
            'password_configured': bool(GARMIN_PASSWORD),
            'email_length': len(GARMIN_EMAIL) if GARMIN_EMAIL else 0,
            'password_length': len(GARMIN_PASSWORD) if GARMIN_PASSWORD else 0,
            'email_preview': GARMIN_EMAIL[:3] + '***' + GARMIN_EMAIL[-3:] if GARMIN_EMAIL else None,
        }
        
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            result['status'] = 'credentials_missing'
            self.send_json(400, result)
            return
        
        try:
            from garminconnect import Garmin
            result['import_success'] = True
            
            # Tentative de connexion
            api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
            result['garmin_object_created'] = True
            
            # Login avec gestion d'erreur détaillée
            try:
                api.login()
                result['login_success'] = True
                result['display_name'] = api.display_name
                result['status'] = 'credentials_valid'
                
            except AssertionError as e:
                result['login_success'] = False
                result['error_type'] = 'AssertionError'
                result['status'] = 'credentials_invalid_or_2fa_enabled'
                result['help'] = 'Check: 1) Email/password correct, 2) No 2FA enabled, 3) Account not locked'
                
            except Exception as e:
                result['login_success'] = False
                result['error'] = str(e)
                result['error_type'] = type(e).__name__
                result['status'] = 'login_failed'
            
            self.send_json(200, result)
            
        except Exception as e:
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
            self.send_json(500, result)
    
    def handle_garmin(self):
        """Gère les requêtes Garmin"""
        
        GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
        GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
        except:
            date_str = date.today().strftime('%Y-%m-%d')
        
        # Vérifier credentials
        if not GARMIN_EMAIL or not GARMIN_PASSWORD:
            self.send_json(400, {
                'error': 'Credentials not configured',
                'help': 'Add GARMIN_EMAIL and GARMIN_PASSWORD in Vercel Environment Variables'
            })
            return
        
        try:
            from garminconnect import Garmin
            
            # Connexion avec retry
            max_retries = 3
            api = None
            
            for attempt in range(max_retries):
                try:
                    api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
                    api.login()
                    break  # Success
                except AssertionError:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        raise Exception("Login failed: Invalid credentials or 2FA enabled. Please check your Garmin email/password and disable 2FA.")
            
            if not api:
                raise Exception("Could not create Garmin API connection")
            
            # Récupération données
            data = {
                'date': date_str,
                'status': 'success',
                'display_name': getattr(api, 'display_name', None),
                
                # DONNÉES
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
                'error': str(e),
                'date': date_str,
                'error_type': type(e).__name__,
                'help': 'If AssertionError: check credentials and disable 2FA on Garmin account'
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
