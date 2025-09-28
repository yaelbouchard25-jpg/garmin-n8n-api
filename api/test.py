import json
from datetime import datetime

def handler(request):
    """Test endpoint pour vérifier que l'API fonctionne"""
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'API working perfectly on Vercel',
            'message': 'Garmin N8N API ready',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'test': '/api/test',
                'garmin_data': '/api/garmin/YYYY-MM-DD',
                'example': '/api/garmin/2024-09-28'
            }
        })
    }
