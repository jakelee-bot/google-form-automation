import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Optional normalizer import with safe fallback
try:
    from src.normalizer import normalize_email_text
except Exception:
    def normalize_email_text(text: str) -> str:
        return text

def handler(request):
    """Simple parser without external dependencies."""
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    try:
        body = json.loads(request.body)
        message = body.get('message', '')
        # Pre-normalize when available
        message = normalize_email_text(message)
        
        # Simple extraction logic
        data = {}
        lines = message.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'name' in key and 'admin' not in key and 'billing' not in key:
                    data['name'] = value
                elif 'email' in key and 'admin' not in key and 'billing' not in key and 'alternate' not in key:
                    data['email'] = value
                elif 'organization name' in key:
                    data['organization_name'] = value
                elif 'sector' in key:
                    data['organization_sector'] = value
                elif 'how many' in key or 'number' in key:
                    try:
                        num = int(''.join(filter(str.isdigit, value)))
                        # Coerce 3-4 license requests to 5
                        if 3 <= num <= 4:
                            num = 5
                        data['num_premium_users'] = num
                    except:
                        data['num_premium_users'] = 1
                elif 'length' in key and 'license' in key:
                    try:
                        data['license_length_years'] = int(''.join(filter(str.isdigit, value)))
                    except:
                        data['license_length_years'] = 1
        
        # Fill in defaults
        result = {
            'success': True,
            'data': {
                'name': data.get('name', ''),
                'email': data.get('email', ''),
                'alternate_email': '',
                'organization_name': data.get('organization_name', ''),
                'organization_sector': data.get('organization_sector', ''),
                'num_premium_users': data.get('num_premium_users', 1),
                'license_length_years': data.get('license_length_years', 1),
                'institution_name': '',
                'admin_name': '',
                'admin_email': '',
                'billing_name': '',
                'billing_email': '',
                'billing_address': '',
                'shipping_address': '',
                'vat_tax_id': ''
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'success': False, 'error': str(e)})
        }