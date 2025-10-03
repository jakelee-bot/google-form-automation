import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.parser_only import MessageParser
except ImportError:
    # Fallback if import fails
    class MessageParser:
        def extract_data(self, message):
            class Data:
                def __init__(self):
                    self.name = ""
                    self.email = ""
                    self.alternate_email = ""
                    self.organization_name = ""
                    self.organization_sector = ""
                    self.num_premium_users = 1
                    self.license_length_years = 1
                    self.institution_name = ""
                    self.admin_name = ""
                    self.admin_email = ""
                    self.billing_name = ""
                    self.billing_email = ""
                    self.billing_address = ""
                    self.shipping_address = ""
                    self.vat_tax_id = ""
            return Data()

# Optional normalizer import with safe fallback
try:
    from src.normalizer import normalize_email_text
except Exception:
    def normalize_email_text(text: str) -> str:
        return text


def handler(request):
    """Vercel serverless function handler."""
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers
        }
    
    try:
        # Parse request
        body = json.loads(request.body or '{}')
        message = body.get('message', '')
        
        # Pre-normalize message when available
        message = normalize_email_text(message)
        
        # Parse the message
        parser = MessageParser()
        extracted = parser.extract_data(message)
        
        # Build response
        result = {
            'success': True,
            'data': {
                'name': getattr(extracted, 'name', ''),
                'email': getattr(extracted, 'email', ''),
                'alternate_email': getattr(extracted, 'alternate_email', ''),
                'organization_name': getattr(extracted, 'organization_name', ''),
                'organization_sector': getattr(extracted, 'organization_sector', ''),
                'num_premium_users': getattr(extracted, 'num_premium_users', 1),
                'license_length_years': getattr(extracted, 'license_length_years', 1),
                'institution_name': getattr(extracted, 'institution_name', ''),
                'admin_name': getattr(extracted, 'admin_name', ''),
                'admin_email': getattr(extracted, 'admin_email', ''),
                'billing_name': getattr(extracted, 'billing_name', ''),
                'billing_email': getattr(extracted, 'billing_email', ''),
                'billing_address': getattr(extracted, 'billing_address', ''),
                'shipping_address': getattr(extracted, 'shipping_address', ''),
                'vat_tax_id': getattr(extracted, 'vat_tax_id', '')
            }
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
        }