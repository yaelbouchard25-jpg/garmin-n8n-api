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
            
            # Récupérer les données avec gestion intelligente
            data = {
                'date': date_str,
                'status': 'success',
                'current_date': date.today().isoformat(),
            }
            
            # USER SUMMARY - peut être liste ou dict
            try:
                user_summary = api.get_user_summary(date_str)
                if isinstance(user_summary, list) and len(user_summary) > 0:
                    data['user_summary'] = user_summary[0]  # Prendre le 1er élément
                elif isinstance(user_summary, dict):
                    data['user_summary'] = user_summary
                else:
                    data['user_summary'] = None
            except Exception as e:
                data['user_summary'] = {'error': str(e)}
            
            # STATS - peut être liste ou dict
            try:
                stats = api.get_stats(date_str)
                if isinstance(stats, list) and len(stats) > 0:
                    data['stats'] = stats[0]  # Prendre le 1er élément
                elif isinstance(stats, dict):
                    data['stats'] = stats
                else:
                    data['stats'] = None
            except Exception as e:
                data['stats'] = {'error': str(e)}
            
            # STEPS
            try:
                steps_data = api.get_steps_data(date_str)
                if isinstance(steps_data, list) and len(steps_data) > 0:
                    data['steps'] = steps_data[0]
                elif isinstance(steps_data, dict):
                    # Extraire la valeur si c'est un dict avec une clé 'totalSteps' ou similaire
                    data['steps'] = steps_data.get('totalSteps') or steps_data.get('steps') or steps_data
                else:
                    data['steps'] = steps_data
            except Exception as e:
                data['steps'] = None
            
            # HEART RATE
            try:
                hr_data = api.get_heart_rates(date_str)
                if isinstance(hr_data, dict):
                    data['heart_rate'] = {
                        'resting': hr_data.get('restingHeartRate'),
                        'max': hr_data.get('maxHeartRate'),
                        'min': hr_data.get('minHeartRate')
                    }
                else:
                    data['heart_rate'] = hr_data
            except:
                data['heart_rate'] = None
            
            # RESTING HR
            try:
                data['resting_hr'] = api.get_rhr_day(date_str)
            except:
                data['resting_hr'] = None
            
            # HRV
            try:
                data['hrv'] = api.get_hrv_data(date_str)
            except:
                data['hrv'] = None
            
            # SLEEP
            try:
                sleep_data = api.get_sleep_data(date_str)
                if isinstance(sleep_data, dict) and 'dailySleepDTO' in sleep_data:
                    sleep_dto = sleep_data['dailySleepDTO']
                    data['sleep'] = {
                        'score': sleep_dto.get('sleepScores', {}).get('overall', {}).get('value'),
                        'duration_hours': sleep_dto.get('sleepTimeSeconds', 0) / 3600,
                        'deep_sleep_seconds': sleep_dto.get('deepSleepSeconds'),
                        'light_sleep_seconds': sleep_dto.get('lightSleepSeconds'),
                        'rem_sleep_seconds': sleep_dto.get('remSleepSeconds'),
                        'awake_seconds': sleep_dto.get('awakeSleepSeconds')
                    }
                else:
                    data['sleep'] = sleep_data
            except:
                data['sleep'] = None
            
            # STRESS
            try:
                stress_data = api.get_stress_data(date_str)
                if isinstance(stress_data, dict):
                    data['stress'] = {
                        'avg': stress_data.get('avgStressLevel'),
                        'max': stress_data.get('maxStressLevel'),
                        'rest_time': stress_data.get('restStressLevel')
                    }
                else:
                    data['stress'] = stress_data
            except:
                data['stress'] = None
            
            # BODY BATTERY
            try:
                bb_data = api.get_body_battery(date_str, date_str)
                if isinstance(bb_data, list) and len(bb_data) > 0:
                    data['body_battery'] = bb_data[0]
                else:
                    data['body_battery'] = bb_data
            except:
                data['body_battery'] = None
            
            # AUTRES DONNÉES
            data['floors'] = self.safe_call(lambda: api.get_floors(date_str))
            data['training_status'] = self.safe_call(lambda: api.get_training_status(date_str))
            data['respiration'] = self.safe_call(lambda: api.get_respiration_data(date_str))
            data['hydration'] = self.safe_call(lambda: api.get_hydration_data(date_str))
            data['spo2'] = self.safe_call(lambda: api.get_spo2_data(date_str))
            
            # Vérifier si on a des données
            has_data = any(
                v and v != [] and v != {} and 'error' not in str(v)
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
            # Si c'est une liste, prendre le 1er élément
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception as e:
            return None
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
