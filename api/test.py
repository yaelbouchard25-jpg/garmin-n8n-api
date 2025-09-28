from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test endpoint simple"""
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {
            'status': 'API working perfectly on Vercel',
            'message': 'Garmin N8N API ready with BaseHTTPRequestHandler',
            'timestamp': datetime.now().isoformat(),
            'path': self.path,
            'endpoints': {
                'test': '/api/test',
                'garmin_data': '/api/garmin/YYYY-MM-DD',
                'example': '/api/garmin/2024-09-28'
            }
        }
        
        response = json.dumps(response_data, indent=2)
        self.wfile.write(response.encode('utf-8'))
