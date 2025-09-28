from flask import Flask, jsonify
import json
import os
from datetime import date

# Configuration Flask pour Vercel
app = Flask(__name__)

def handler(request):
    """Handler principal pour Vercel Serverless Functions"""
    
    # Variables d'environnement
    GARMIN_EMAIL = os.getenv('GARMIN_EMAIL')
    GARMIN_PASSWORD = os.getenv('GARMIN_PASSWORD')
    
    if not GARMIN_EMAIL or not GARMIN_PASSWORD:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing Garmin credentials'})
        }
    
    # Parse l'URL pour récupérer la date
    path = request.get('path', '')
    
    if '/api/garmin/' in path:
        date_str = path.split('/api/garmin/')[-1]
    else:
        date_str = date.today().strftime('%Y-%m-%d')
    
    try:
        # Import garminconnect
        from garminconnect import Garmin
        
        # Connexion
        api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        api.login()
        
        # Récupération des données
        garmin_data = {
            'date': date_str,
            'status': 'success',
            'timestamp': date.today().isoformat(),
            
            # DONNÉES ESSENTIELLES
            'sleep_data': safe_api_call(lambda: api.get_sleep_data(date_str)),
            'stress_data': safe_api_call(lambda: api.get_stress_data(date_str)),
            'body_battery': safe_api_call(lambda: api.get_body_battery(date_str, date_str)),
            'heart_rate': safe_api_call(lambda: api.get_heart_rates(date_str)),
            'resting_hr': safe_api_call(lambda: api.get_rhr_day(date_str)),
            'steps_data': safe_api_call(lambda: api.get_steps_data(date_str)),
            'stats_data': safe_api_call(lambda: api.get_stats(date_str)),
            'respiration': safe_api_call(lambda: api.get_respiration_data(date_str)),
            'hydration': safe_api_call(lambda: api.get_hydration_data(date_str)),
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(garmin_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'date': date_str,
                'status': 'error',
                'error': str(e)
            })
        }

def safe_api_call(func):
    """Wrapper sécurisé pour les appels API"""
    try:
        result = func()
        return result
    except Exception:
        return None

# Pour les tests locaux
if __name__ == '__main__':
    # Test local
    test_request = {'path': '/api/garmin/2024-09-28'}
    result = handler(test_request)
    print(json.dumps(result, indent=2))
