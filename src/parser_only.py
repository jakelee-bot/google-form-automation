"""
Standalone message parser without Playwright dependencies
"""

import re

class FormData:
    """A dataclass to hold the extracted information."""
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
        self.user_names_emails = ""
        self.first_user_name = ""
        self.first_user_email = ""
        self.second_user_name = ""
        self.second_user_email = ""

class MessageParser:
    """Parses the user's message to extract form data."""

    def extract_data(self, message: str) -> FormData:
        """Extract structured data from the input message"""
        data = FormData()
        
        if not message:
            return data
            
        lines = message.split('\n')
        
        for line in lines:
            if ':' not in line:
                continue
                
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if not value:
                continue
            
            # Map keys to data fields
            if 'your name' in key:
                data.name = value
            elif 'your email' in key:
                data.email = value
            elif 'alternate email' in key:
                data.alternate_email = value
            elif 'organization name' in key:
                data.organization_name = value
            elif 'organization sector' in key or 'sector' in key:
                data.organization_sector = 'Academic' if 'acad' in value.lower() else 'Industry'
            elif 'how many people' in key or 'premium access' in key:
                numbers = re.findall(r'\d+', value)
                if numbers:
                    data.num_premium_users = int(numbers[0])
            elif 'length of license' in key:
                numbers = re.findall(r'\d+', value)
                if numbers:
                    data.license_length_years = int(numbers[0])
            elif 'institution' in key or 'lab' in key or 'team' in key:
                data.institution_name = value
            elif 'admin name' in key:
                data.admin_name = value
            elif 'admin email' in key:
                data.admin_email = value
            elif 'billing name' in key:
                data.billing_name = value
            elif 'billing email' in key:
                data.billing_email = value
            elif 'billing address' in key:
                data.billing_address = value
            elif 'shipping address' in key:
                data.shipping_address = value
            elif 'vat' in key or 'tax id' in key:
                data.vat_tax_id = value
            elif 'intended users' in key:
                data.user_names_emails = value
        
        # Handle special cases
        if 3 <= data.num_premium_users <= 4:
            data.num_premium_users = 5
            
        if not data.institution_name and data.organization_name:
            data.institution_name = data.organization_name
            
        if data.billing_address and not data.shipping_address:
            data.shipping_address = data.billing_address
        elif data.shipping_address and not data.billing_address:
            data.billing_address = data.shipping_address
            
        return data