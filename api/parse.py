from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.form_automation import MessageParser

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Parse the message
            parser = MessageParser()
            extracted = parser.extract_data(data.get('message', ''))
            
            # Return parsed data
            response = {
                'success': True,
                'data': {
                    'name': extracted.name,
                    'email': extracted.email,
                    'alternate_email': extracted.alternate_email,
                    'organization_name': extracted.organization_name,
                    'organization_sector': extracted.organization_sector,
                    'num_premium_users': extracted.num_premium_users,
                    'license_length_years': extracted.license_length_years,
                    'institution_name': extracted.institution_name,
                    'admin_name': extracted.admin_name,
                    'admin_email': extracted.admin_email,
                    'billing_name': extracted.billing_name,
                    'billing_email': extracted.billing_email,
                    'billing_address': extracted.billing_address,
                    'shipping_address': extracted.shipping_address,
                    'vat_tax_id': extracted.vat_tax_id
                }
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()