"""
Enhanced message parser for structured form data
"""

import re
import logging

logger = logging.getLogger(__name__)

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

    # Add this property to alias number_of_users to num_premium_users
    @property
    def number_of_users(self):
        return self.num_premium_users
    
    @number_of_users.setter
    def number_of_users(self, value):
        self.num_premium_users = value

class MessageParser:
    """Enhanced parser with better field matching"""
    
    def __init__(self):
        # Define exact field mappings - now includes both formats
        self.field_mappings = {
            # Original format mappings
            'your name': 'name',
            'your email': 'email',
            'alternate email': 'alternate_email',
            'organization name': 'organization_name',
            'organization sector': 'organization_sector',
            'how many people need premium access': 'num_premium_users',
            'length of license': 'license_length_years',
            'name of institution': 'institution_name',
            'names and emails of intended users': 'user_names_emails',
            'admin name': 'admin_name',
            'admin email': 'admin_email',
            'billing name': 'billing_name',
            'billing email': 'billing_email',
            'billing address': 'billing_address',
            'shipping address': 'shipping_address',
            'vat or tax id': 'vat_tax_id',
            'vat or tax id number': 'vat_tax_id',
            
            # New format mappings
            'full name': 'name',
            'email address': 'email',
            'license type': 'organization_sector',
            'name of your institution': 'organization_name',
            'number of individuals the license is intended for': 'num_premium_users',
            'license length': 'license_length_years'
        }
    
    def extract_data(self, message: str) -> FormData:
        """Extract structured data from the input message"""
        data = FormData()
        
        if not message:
            return data
        
        # Process line by line
        lines = message.split('\n')
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Try to detect delimiter (: or -)
            delimiter = None
            if ':' in line:
                delimiter = ':'
            elif ' - ' in line:  # Look for dash with spaces
                delimiter = ' - '
            else:
                continue
            
            # Split on delimiter
            if delimiter == ' - ':
                parts = line.split(' - ', 1)
            else:
                parts = line.split(':', 1)
                
            if len(parts) != 2:
                continue
                
            key = parts[0].strip().lower()
            value = parts[1].strip()
            
            # Remove asterisks and bullets from key
            key = key.lstrip('*').strip()
            
            # Skip empty values
            if not value:
                continue
                
            # Remove optional indicators and parenthetical content from key
            key_clean = re.sub(r'\s*\([^)]*\)', '', key)
            key_clean = key_clean.strip().rstrip('?')
            
            # Direct field mapping
            field_name = None
            for pattern, field in self.field_mappings.items():
                if pattern in key_clean or key_clean in pattern:
                    field_name = field
                    break
            
            if field_name:
                # Special handling for specific fields
                if field_name == 'organization_sector':
                    value_lower = value.lower()
                    # Check for academic indicators
                    if any(word in value_lower for word in ['acad', 'university', 'college', 'edu']):
                        setattr(data, field_name, 'Academic')
                    elif 'industry' in value_lower or 'commercial' in value_lower:
                        setattr(data, field_name, 'Industry')
                    else:
                        # Default based on presence of keywords
                        setattr(data, field_name, 'Academic' if 'academic' in value_lower else 'Industry')
                elif field_name == 'num_premium_users':
                    # Extract number
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        num_users = int(numbers[0])
                        # Coerce 3-4 license requests to 5
                        if 3 <= num_users <= 4:
                            num_users = 5
                        setattr(data, field_name, num_users)
                elif field_name == 'license_length_years':
                    # Extract number
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        setattr(data, field_name, int(numbers[0]))
                    else:
                        # Default to 1 if not specified
                        setattr(data, field_name, 1)
                else:
                    setattr(data, field_name, value)
                
                logger.info(f"Set {field_name} = {getattr(data, field_name)}")
        
        # Post-processing
        self._post_process_data(data)
        
        return data
    
    def _post_process_data(self, data: FormData):
        """Post-process extracted data"""
        # Set institution name default
        if not data.institution_name and data.organization_name:
            data.institution_name = data.organization_name
        
        # Handle address copying
        if data.billing_address and not data.shipping_address:
            data.shipping_address = data.billing_address
        elif data.shipping_address and not data.billing_address:
            data.billing_address = data.shipping_address
        
        # Extract individual users for 1-2 person licenses
        if data.user_names_emails and data.num_premium_users <= 2:
            self._extract_individual_users(data)
        
        # Set default license length if not specified
        if not data.license_length_years:
            data.license_length_years = 1
                    
    def _normalize_key(self, key: str) -> str:
        """Normalize a key for matching by removing special characters and lowercasing."""
        # Remove parenthetical content first
        key = re.sub(r'\([^)]*\)', '', key)
        # Remove special characters but keep spaces
        key = re.sub(r'[^a-zA-Z0-9\s]', '', key)
        # Convert to lowercase and remove extra spaces
        key = ' '.join(key.lower().split())
        return key

    def _parse_unstructured(self, message: str, data: FormData) -> None:
        """Parse unstructured message format."""
        logger.info("Parsing as unstructured message...")
        
        # Extract all emails first
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        emails = re.findall(email_pattern, message)
        
        if emails:
            data.email = emails[0]
            logger.info(f"Extracted primary email: {data.email}")
            
            # Look for alternate email indicators
            alt_email_patterns = [
                r'send\s+(?:quote\s+)?to[:\s]+' + email_pattern,
                r'alternate\s+email[:\s]+' + email_pattern,
                r'cc[:\s]+' + email_pattern
            ]
            
            for pattern in alt_email_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    data.alternate_email = match.group(1)
                    logger.info(f"Extracted alternate email: {data.alternate_email}")
                    break
        
        # Extract names, organizations, etc...
        # (add the rest of the unstructured parsing logic here)

    def _extract_individual_users(self, data: FormData) -> None:
        """Extract individual user names and emails from the user list."""
        if not data.user_names_emails:
            return
        
        # Extract all emails
        emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', data.user_names_emails)
        
        # For single user
        if data.num_premium_users == 1:
            data.first_user_name = data.name
            data.first_user_email = data.email
        
        # For two users
        elif data.num_premium_users == 2:
            data.first_user_name = data.name
            data.first_user_email = data.email
            
            # Find second user
            for email in emails:
                if email.lower() != data.email.lower():
                    data.second_user_email = email
                    
                    # Extract name by removing email and cleaning
                    remaining_text = data.user_names_emails.replace(email, '')
                    # Remove the primary user's name if present
                    if data.name:
                        remaining_text = remaining_text.replace(data.name, '')
                    
                    # Clean and extract name
                    name_match = re.search(r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', remaining_text)
                    if name_match:
                        data.second_user_name = name_match.group(1).strip()
                        logger.info(f"Extracted second user: {data.second_user_name} <{data.second_user_email}>")
                    break

