import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.form_automation import MessageParser

def handler(request, response):
    """Handle POST requests to parse form data."""
    
    # Handle CORS
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS request
    if request.method == 'OPTIONS':
        return response
    
    # Only accept POST
    if request.method != 'POST':
        response.status_code = 405
        return json.dumps({'success': False, 'error': 'Method not allowed'})
    
    try:
        # Parse request body
        body = json.loads(request.body)
        message = body.get('message', '')
        
        # Parse the message
        parser = MessageParser()
        extracted = parser.extract_data(message)
        
        # Return parsed data
        result = {
            'success': True,
            'data': {
                'name': extracted.name or '',
                'email': extracted.email or '',
                'alternate_email': extracted.alternate_email or '',
                'organization_name': extracted.organization_name or '',
                'organization_sector': extracted.organization_sector or '',
                'num_premium_users': extracted.num_premium_users or 1,
                'license_length_years': extracted.license_length_years or 1,
                'institution_name': extracted.institution_name or '',
                'admin_name': extracted.admin_name or '',
                'admin_email': extracted.admin_email or '',
                'billing_name': extracted.billing_name or '',
                'billing_email': extracted.billing_email or '',
                'billing_address': extracted.billing_address or '',
                'shipping_address': extracted.shipping_address or '',
                'vat_tax_id': extracted.vat_tax_id or ''
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        response.status_code = 500
        return json.dumps({'success': False, 'error': str(e)})