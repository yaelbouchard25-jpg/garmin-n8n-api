from flask import jsonify

def handler(request):
    return jsonify({
        'status': 'API working on Vercel',
        'message': 'Garmin API ready',
        'endpoints': ['/api/garmin/YYYY-MM-DD', '/api/test']
    })
