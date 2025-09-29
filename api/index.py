from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import date, datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if 'test' in self.path:
                self.send_json(200, {
                    'status': '✅ Garmin API Working',
                    'current_date': date.today().isoformat()
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
        display_name = os.getenv('GARMIN_DISPLAY_NAME')
        full_name = os.getenv('GARMIN_FULL_NAME')
        
        # Parse date
        try:
            query = self.path.split('?')[-1]
            params = dict(x.split('=') for x in query.split('&') if '=' in x)
            date_str = params.get('date', date.today().isoformat())
        except:
            date_str = date.today().isoformat()
        
        # Validation
        if not all([oauth1_str, oauth2_str, display_name]):
            self.send_json(400, {
                'error': 'Missing credentials in Vercel',
                'has_oauth1': bool(oauth1_str),
                'has_oauth2': bool(oauth2_str),
                'has_display_name': bool(display_name)
            })
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
            
            # Structure de base
            data = {
                'date': date_str,
                'status': 'success',
                'profile': {
                    'display_name': display_name,
                    'full_name': full_name
                }
            }
            
            # STEPS DATA
            try:
                steps_raw = api.get_steps_data(date_str)
                if isinstance(steps_raw, list) and len(steps_raw) > 0:
                    # Extraire les steps totaux
                    total_steps = sum(item.get('steps', 0) for item in steps_raw if isinstance(item, dict))
                    data['steps'] = {
                        'total': total_steps,
                        'data': steps_raw[:5]  # Premiers 5 points
                    }
                elif isinstance(steps_raw, dict):
                    data['steps'] = steps_raw
                else:
                    data['steps'] = None
            except Exception as e:
                data['steps'] = {'error': str(e)}
            
            # HEART RATE
            try:
                hr_raw = api.get_heart_rates(date_str)
                if isinstance(hr_raw, dict):
                    data['heart_rate'] = {
                        'resting': hr_raw.get('restingHeartRate'),
                        'max': hr_raw.get('maxHeartRate'),
                        'min': hr_raw.get('minHeartRate'),
                        'avg': hr_raw.get('avgHeartRate')
                    }
                elif isinstance(hr_raw, list):
                    data['heart_rate'] = {'data': hr_raw[:5]}
                else:
                    data['heart_rate'] = None
            except Exception as e:
                data['heart_rate'] = {'error': str(e)}
            
            # RESTING HR
            try:
                rhr = api.get_rhr_day(date_str)
                if isinstance(rhr, dict):
                    data['resting_hr'] = rhr.get('restingHeartRate') or rhr.get('value')
                elif isinstance(rhr, list) and len(rhr) > 0:
                    data['resting_hr'] = rhr[0] if isinstance(rhr[0], (int, float)) else rhr[0].get('value')
                else:
                    data['resting_hr'] = rhr
            except Exception as e:
                data['resting_hr'] = {'error': str(e)}
            
            # SLEEP DATA
            try:
                sleep_raw = api.get_sleep_data(date_str)
                if isinstance(sleep_raw, dict):
                    # Extraire les infos importantes
                    sleep_dto = sleep_raw.get('dailySleepDTO', {})
                    data['sleep'] = {
                        'sleep_score': sleep_dto.get('sleepScores', {}).get('overall', {}).get('value'),
                        'total_hours': round(sleep_dto.get('sleepTimeSeconds', 0) / 3600, 2),
                        'deep_sleep_hours': round(sleep_dto.get('deepSleepSeconds', 0) / 3600, 2),
                        'light_sleep_hours': round(sleep_dto.get('lightSleepSeconds', 0) / 3600, 2),
                        'rem_sleep_hours': round(sleep_dto.get('remSleepSeconds', 0) / 3600, 2),
                        'awake_hours': round(sleep_dto.get('awakeSleepSeconds', 0) / 3600, 2)
                    }
                elif isinstance(sleep_raw, list):
                    data['sleep'] = sleep_raw[0] if len(sleep_raw) > 0 else None
                else:
                    data['sleep'] = None
            except Exception as e:
                data['sleep'] = {'error': str(e)}
            
            # STRESS
            try:
                stress_raw = api.get_stress_data(date_str)
                if isinstance(stress_raw, dict):
                    data['stress'] = {
                        'avg': stress_raw.get('avgStressLevel'),
                        'max': stress_raw.get('maxStressLevel'),
                        'rest': stress_raw.get('restStressLevel')
                    }
                elif isinstance(stress_raw, list):
                    data['stress'] = stress_raw[0] if len(stress_raw) > 0 else None
                else:
                    data['stress'] = None
            except Exception as e:
                data['stress'] = {'error': str(e)}
            
            # BODY BATTERY
            try:
                bb_raw = api.get_body_battery(date_str, date_str)
                if isinstance(bb_raw, list) and len(bb_raw) > 0:
                    # Prendre le premier élément
                    bb_first = bb_raw[0]
                    if isinstance(bb_first, dict):
                        data['body_battery'] = {
                            'charged': bb_first.get('charged'),
                            'drained': bb_first.get('drained'),
                            'highest': bb_first.get('highest'),
                            'lowest': bb_first.get('lowest')
                        }
                    else:
                        data['body_battery'] = bb_first
                elif isinstance(bb_raw, dict):
                    data['body_battery'] = bb_raw
                else:
                    data['body_battery'] = None
            except Exception as e:
                data['body_battery'] = {'error': str(e)}
            
            # HRV
            try:
                hrv = api.get_hrv_data(date_str)
                if isinstance(hrv, dict):
                    data['hrv'] = {
                        'weekly_avg': hrv.get('weeklyAvg'),
                        'last_night_avg': hrv.get('lastNightAvg'),
                        'status': hrv.get('status')
                    }
                elif isinstance(hrv, list) and len(hrv) > 0:
                    data['hrv'] = hrv[0]
                else:
                    data['hrv'] = hrv
            except Exception as e:
                data['hrv'] = {'error': str(e)}
            
            # AUTRES DONNÉES
            data['respiration'] = self.safe_call(lambda: api.get_respiration_data(date_str))
            data['hydration'] = self.safe_call(lambda: api.get_hydration_data(date_str))
            data['spo2'] = self.safe_call(lambda: api.get_spo2_data(date_str))
            
            # Vérifier si on a des données
            has_data = any(
                v and v != [] and v != {} and not (isinstance(v, dict) and 'error' in v)
                for k, v in data.items() 
                if k not in ['date', 'status', 'profile']
            )
            
            if not has_data:
                data['warning'] = '⚠️ Aucune donnée trouvée. Vérifie: 1) Tu as porté ta montre ce jour-là, 2) Les données sont synchronisées sur Garmin Connect'
            
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
            if isinstance(result, list) and len(result) > 0:
                return result[0] if isinstance(result[0], dict) else result
            return result
        except Exception as e:
            return None
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
