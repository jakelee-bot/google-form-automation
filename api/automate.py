"""
Vercel API endpoint for form automation.
"""

import json
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.form_automation import GoogleFormBot, MessageParser

async def process_form_data(message: str, headless: bool = True) -> dict:
    """Process form data and return results."""
    bot = GoogleFormBot(headless=headless, page_by_page=False)
    parser = MessageParser()
    
    try:
        # Extract data
        data = parser.extract_data(message)
        
        # Convert to dict for response
        result = {
            'success': True,
            'extracted_data': {
                'name': data.name,
                'email': data.email,
                'alternate_email': data.alternate_email,
                'organization_name': data.organization_name,
                'organization_sector': data.organization_sector,
                'num_premium_users': data.num_premium_users,
                'license_length_years': data.license_length_years,
                'institution_name': data.institution_name,
                'admin_name': data.admin_name,
                'admin_email': data.admin_email,
                'billing_name': data.billing_name,
                'billing_email': data.billing_email,
                'billing_address': data.billing_address,
                'shipping_address': data.shipping_address,
                'vat_tax_id': data.vat_tax_id,
                'user_names_emails': data.user_names_emails
            }
        }
        
        # Run automation
        await bot.setup()
        await bot.run_automation(message)
        await bot.cleanup()
        
        result['message'] = 'Form submitted successfully'
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'message': 'Failed to process form'
        }
    
    return result

def handler(request):
    """Vercel serverless function handler."""
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        body = json.loads(request.body)
        message = body.get('message', '')
        headless = body.get('headless', True)
        
        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Run async function
        result = asyncio.run(process_form_data(message, headless))
        
        return {
            'statusCode': 200 if result['success'] else 500,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }