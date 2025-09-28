from flask import Flask, jsonify, request
import os
from datetime import date
import json

# Configuration pour Vercel
app = Flask(__name__)

def handler(request):
    """Fonction principale pour Vercel"""
    
    # Variables d'environnement Vercel
    GARMIN_EMAIL = os.getenv('bouchardyael@gmail.com')
    GARMIN_PASSWORD = os.getenv('Rosaza017)')
    
    # Parse l'URL pour extraire la date
    path = request.path
    if '/garmin-data/' in path:
        date_str = path.split('/garmin-data/')[-1]
    else:
        return jsonify({'error': 'Invalid endpoint'}), 400
    
    try:
        from garminconnect import Garmin
        
        # Connexion Garmin
        api = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        api.login()
        
        # Récupération COMPLÈTE des données
        all_data = {
            'date': date_str,
            'status': 'success',
            
            # SOMMEIL
            'sleep_data': safe_api_call(lambda: api.get_sleep_data(date_str)),
            
            # STRESS & RÉCUPÉRATION  
            'stress_data': safe_api_call(lambda: api.get_stress_data(date_str)),
            'body_battery': safe_api_call(lambda: api.get_body_battery(date_str, date_str)),
            'training_readiness': safe_api_call(lambda: api.get_training_readiness_data(date_str)),
            
            # FRÉQUENCE CARDIAQUE
            'heart_rate': safe_api_call(lambda: api.get_heart_rates(date_str)),
            'resting_hr': safe_api_call(lambda: api.get_rhr_day(date_str)),
            'hrv_data': safe_api_call(lambda: api.get_hrv_data(date_str)),
            
            # ACTIVITÉ QUOTIDIENNE
            'steps_data': safe_api_call(lambda: api.get_steps_data(date_str)),
            'floors_data': safe_api_call(lambda: api.get_floors(date_str)),
            'stats_data': safe_api_call(lambda: api.get_stats(date_str)),
            
            # RESPIRATION & AUTRES
            'respiration': safe_api_call(lambda: api.get_respiration_data(date_str)),
            'hydration': safe_api_call(lambda: api.get_hydration_data(date_str)),
            'spo2_data': safe_api_call(lambda: api.get_spo2_data(date_str)),
            
            # POIDS & COMPOSITION
            'weight_data': safe_api_call(lambda: api.get_weigh_ins(date_str)),
            'body_composition': safe_api_call(lambda: api.get_body_composition(date_str)),
            
            # ENTRAÎNEMENT
            'training_status': safe_api_call(lambda: api.get_training_status(date_str)),
            'activities': safe_api_call(lambda: api.get_activities_fordate(date_str)),
        }
        
        return jsonify(all_data)
        
    except Exception as e:
        return jsonify({
            'date': date_str,
            'status': 'error',
            'error': str(e)
        }), 500

def safe_api_call(func):
    """Wrapper pour éviter les erreurs sur APIs manquantes"""
    try:
        return func()
    except:
        return None

# Route de test
def test_handler(request):
    return jsonify({
        'status': 'API working on Vercel',
        'endpoints': ['/api/garmin/YYYY-MM-DD', '/api/test']
    })
