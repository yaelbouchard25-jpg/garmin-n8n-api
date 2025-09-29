from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date
import traceback
import sys
import logging

# Configuration logging ultra-détaillé
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override pour capturer les logs HTTP"""
        logger.info(f"HTTP: {format % args}")
    
    def do_GET(self):
        try:
            # Route test
            if 'test' in self.path or (self.path == '/api/index' and 'garmin' not in self.path):
                self.send_json(200, {
                    'status': '✅ API Ready - Ultra Debug Mode',
                    'version': 'GITHUB-BASED-v1.0',
                    'python_version': sys.version,
                    'tokens_configured': {
                        'oauth1': bool(os.getenv('GARMIN_OAUTH1_TOKEN')),
                        'oauth2': bool(os.getenv('GARMIN_OAUTH2_TOKEN')),
                        'oauth1_length': len(os.getenv('GARMIN_OAUTH1_TOKEN', '')) if os.getenv('GARMIN_OAUTH1_TOKEN') else 0,
                        'oauth2_length': len(os.getenv('GARMIN_OAUTH2_TOKEN', '')) if os.getenv('GARMIN_OAUTH2_TOKEN') else 0
                    },
                    'endpoints': {
                        'test': '/api/index',
                        'garmin': '/api/index?garmin&date=2024-09-29'
                    }
                })
                return
            
            elif 'garmin' in self.path:
                self.handle_garmin_detailed()
                return
            
            else:
                self.send_json(404, {'error': 'Route not found', 'path': self.path})
                
        except Exception as e:
            logger.exception("Fatal error in do_GET")
            self.send_json(500, {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
    
    def handle_garmin_detailed(self):
        """Récupère données Garmin avec logging ultra-détaillé"""
        
        log_entries = []
        
        def add_log(level, message, data=None):
            """Helper pour logger avec niveau"""
            entry = {
                'level': level,
                'message': message,
                'timestamp': date.today().isoformat()
            }
            if data:
                entry['data'] = data
            log_entries.append(entry)
            
            if level == 'ERROR':
                logger.error(f"{message}: {data}")
            elif level == 'INFO':
                logger.info(f"{message}: {data}")
            else:
                logger.debug(f"{message}: {data}")
        
        try:
            add_log('INFO', '🚀 Starting Garmin data fetch')
            
            # ÉTAPE 1: Récupérer tokens
            add_log('INFO', 'STEP 1: Retrieving OAuth tokens from environment')
            oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
            oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
            
            tokens_status = {
                'oauth1_exists': oauth1_str is not None,
                'oauth2_exists': oauth2_str is not None,
                'oauth1_length': len(oauth1_str) if oauth1_str else 0,
                'oauth2_length': len(oauth2_str) if oauth2_str else 0,
                'oauth1_first_chars': oauth1_str[:50] if oauth1_str else None,
                'oauth2_first_chars': oauth2_str[:50] if oauth2_str else None
            }
            add_log('INFO', 'Tokens status', tokens_status)
            
            # Parse date
            try:
                query = self.path.split('?')[-1]
                params = dict(x.split('=') for x in query.split('&') if '=' in x)
                date_str = params.get('date', date.today().strftime('%Y-%m-%d'))
                add_log('INFO', f'Date parsed: {date_str}')
            except Exception as e:
                date_str = date.today().strftime('%Y-%m-%d')
                add_log('ERROR', 'Date parsing failed, using today', str(e))
            
            if not oauth1_str or not oauth2_str:
                add_log('ERROR', 'Tokens missing in environment variables')
                self.send_json(400, {
                    'error': 'OAuth tokens not configured',
                    'debug_log': log_entries,
                    'tokens_status': tokens_status
                })
                return
            
            # ÉTAPE 2: Importer bibliothèques
            add_log('INFO', 'STEP 2: Importing libraries')
            try:
                import garth
                add_log('INFO', f'✅ garth imported - version: {garth.__version__ if hasattr(garth, "__version__") else "unknown"}')
            except Exception as e:
                add_log('ERROR', 'garth import failed', str(e))
                raise
            
            try:
                from garminconnect import Garmin
                add_log('INFO', '✅ Garmin imported successfully')
            except Exception as e:
                add_log('ERROR', 'Garmin import failed', str(e))
                raise
            
            # ÉTAPE 3: Parser les tokens JSON
            add_log('INFO', 'STEP 3: Parsing OAuth token JSONs')
            try:
                oauth1_data = json.loads(oauth1_str)
                add_log('INFO', 'OAuth1 parsed', {
                    'keys': list(oauth1_data.keys()),
                    'has_token': 'token' in oauth1_data or 'oauth_token' in oauth1_data
                })
            except Exception as e:
                add_log('ERROR', 'OAuth1 JSON parsing failed', str(e))
                self.send_json(500, {
                    'error': 'Invalid OAuth1 token JSON',
                    'debug_log': log_entries,
                    'oauth1_preview': oauth1_str[:200] if oauth1_str else None
                })
                return
            
            try:
                oauth2_data = json.loads(oauth2_str)
                add_log('INFO', 'OAuth2 parsed', {
                    'keys': list(oauth2_data.keys()),
                    'has_access_token': 'access_token' in oauth2_data
                })
            except Exception as e:
                add_log('ERROR', 'OAuth2 JSON parsing failed', str(e))
                self.send_json(500, {
                    'error': 'Invalid OAuth2 token JSON',
                    'debug_log': log_entries
                })
                return
            
            # ÉTAPE 4: Créer objets Token (méthode GitHub)
            add_log('INFO', 'STEP 4: Creating token objects')
            try:
                from garth.auth_tokens import OAuth1Token, OAuth2Token
                add_log('INFO', '✅ Token classes imported')
                
                # Créer tokens selon structure GitHub
                oauth1_token = OAuth1Token(**oauth1_data)
                oauth2_token = OAuth2Token(**oauth2_data)
                add_log('INFO', '✅ Token objects created successfully')
                
            except Exception as e:
                add_log('ERROR', 'Token object creation failed', {
                    'error': str(e),
                    'oauth1_keys': list(oauth1_data.keys()),
                    'oauth2_keys': list(oauth2_data.keys())
                })
                raise
            
            # ÉTAPE 5: Configurer garth client (méthode officielle GitHub)
            add_log('INFO', 'STEP 5: Configuring garth client')
            try:
                garth.client.oauth1_token = oauth1_token
                garth.client.oauth2_token = oauth2_token
                add_log('INFO', '✅ Garth client configured with tokens')
                
                # Vérifier que garth a bien les tokens
                has_oauth1 = garth.client.oauth1_token is not None
                has_oauth2 = garth.client.oauth2_token is not None
                add_log('INFO', 'Garth client verification', {
                    'has_oauth1_token': has_oauth1,
                    'has_oauth2_token': has_oauth2
                })
                
            except Exception as e:
                add_log('ERROR', 'Garth client configuration failed', str(e))
                raise
            
            # ÉTAPE 6: Créer client Garmin (sans login comme sur GitHub!)
            add_log('INFO', 'STEP 6: Creating Garmin API client')
            try:
                # Comme dans example.py: Garmin() sans paramètres utilise garth.client
                api = Garmin()
                add_log('INFO', '✅ Garmin API client created (no login needed with tokens)')
                
            except Exception as e:
                add_log('ERROR', 'Garmin client creation failed', str(e))
                raise
            
            # ÉTAPE 7: Tester les appels API individuellement
            add_log('INFO', f'STEP 7: Fetching Garmin data for {date_str}')
            
            results = {}
            errors_detail = {}
            
            # Liste des appels à tester
            api_calls = {
                'get_stats': lambda: api.get_stats(date_str),
                'get_steps_data': lambda: api.get_steps_data(date_str),
                'get_heart_rates': lambda: api.get_heart_rates(date_str),
                'get_rhr_day': lambda: api.get_rhr_day(date_str),
                'get_sleep_data': lambda: api.get_sleep_data(date_str),
                'get_stress_data': lambda: api.get_stress_data(date_str),
                'get_body_battery': lambda: api.get_body_battery(date_str, date_str),
                'get_respiration_data': lambda: api.get_respiration_data(date_str),
                'get_hydration_data': lambda: api.get_hydration_data(date_str),
            }
            
            for call_name, call_func in api_calls.items():
                try:
                    add_log('INFO', f'Calling {call_name}...')
                    result = call_func()
                    results[call_name] = result
                    
                    # Analyse du résultat
                    if result is None:
                        add_log('INFO', f'⚠️ {call_name}: returned None (no data for this date?)')
                    elif isinstance(result, dict):
                        add_log('INFO', f'✅ {call_name}: dict with {len(result)} keys')
                    elif isinstance(result, list):
                        add_log('INFO', f'✅ {call_name}: list with {len(result)} items')
                    else:
                        add_log('INFO', f'✅ {call_name}: {type(result).__name__}')
                    
                except Exception as e:
                    error_info = {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'traceback': traceback.format_exc()
                    }
                    errors_detail[call_name] = error_info
                    add_log('ERROR', f'❌ {call_name} failed', error_info)
            
            # RÉSULTAT FINAL
            add_log('INFO', '✅ Garmin data fetch completed')
            
            response = {
                'status': 'success',
                'date': date_str,
                'summary': {
                    'successful_calls': len(results),
                    'failed_calls': len(errors_detail),
                    'total_calls': len(api_calls)
                },
                'debug_log': log_entries,
                'data': results,
                'errors': errors_detail if errors_detail else None
            }
            
            self.send_json(200, response)
            
        except Exception as e:
            add_log('ERROR', 'Fatal exception', {
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            })
            
            self.send_json(500, {
                'status': 'fatal_error',
                'error': str(e),
                'error_type': type(e).__name__,
                'debug_log': log_entries,
                'traceback': traceback.format_exc()
            })
    
    def send_json(self, code, data):
        """Envoie réponse JSON avec headers CORS"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))
