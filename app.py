from flask import Flask, jsonify, request
import os
from datetime import date
from garminconnect import Garmin
from garth.auth_tokens import OAuth1Token, OAuth2Token
import json

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'Garmin API Working'})

@app.route('/garmin')
def garmin():
    try:
        # Récupérer les tokens
        oauth1_str = os.getenv('GARMIN_OAUTH1_TOKEN')
        oauth2_str = os.getenv('GARMIN_OAUTH2_TOKEN')
        
        if not oauth1_str or not oauth2_str:
            return jsonify({'error': 'Missing tokens'}), 400
        
        # Date
        date_str = request.args.get('date', date.today().isoformat())
        
        # Parser tokens
        oauth1_data = json.loads(oauth1_str)
        oauth2_data = json.loads(oauth2_str)
        oauth1_token = OAuth1Token(**oauth1_data)
        oauth2_token = OAuth2Token(**oauth2_data)
        
        # Créer client
        api = Garmin()
        api.garth.oauth1_token = oauth1_token
        api.garth.oauth2_token = oauth2_token
        
        # Récupérer username
        try:
            user_settings = api.garth.connectapi("/userprofile-service/userprofile")
            api.display_name = user_settings.get('userName')
            api.full_name = user_settings.get('fullName', 'User')
        except:
            api.display_name = 'unknown'
            api.full_name = 'User'
        
        # Récupérer données
        data = {
            'date': date_str,
            'status': 'success',
            'username': api.display_name,
            'steps': safe_get(lambda: api.get_steps_data(date_str)),
            'heart_rate': safe_get(lambda: api.get_heart_rates(date_str)),
            'sleep': safe_get(lambda: api.get_sleep_data(date_str)),
            'stress': safe_get(lambda: api.get_stress_data(date_str)),
            'body_battery': safe_get(lambda: api.get_body_battery(date_str, date_str))
        }
        
        return jsonify(data)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

def safe_get(func):
    try:
        result = func()
        return result if result else None
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
