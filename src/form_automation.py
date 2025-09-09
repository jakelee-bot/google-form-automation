"""
Google Form Automation Bot using Playwright.

This script automates filling out a Google Form based on input from a user message.
It uses Playwright for browser automation and can run in either headless or headed mode.
"""

import asyncio
import logging
import re
import os
from typing import List, Optional, Tuple

from playwright.async_api import async_playwright, Browser, Page, Playwright
from .config import config
from src.parser_only import MessageParser, FormData

# --- Configuration ---
LOG_FILE = 'form_automation.log'
FORM_URL = config.FORM_URL  # CHANGE THIS LINE

# Setup logging
os.makedirs('logs', exist_ok=True)  # ADD THIS LINE
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),  # CHANGE THIS LINE
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/{LOG_FILE}'),  # CHANGE THIS LINE
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Form Structure Definition ---
FORM_STRUCTURE = {
    'page_1': {
        'name': 'Contact Information',
        'fields': [
            {'field': 'name', 'required': True, 'type': 'text', 'label': 'Your name'},
            {'field': 'email', 'required': True, 'type': 'email', 'label': 'Your email'},
            {'field': 'send_to', 'required': False, 'type': 'email', 'label': 'Send to', 'default_to': 'email'}
        ]
    },
    'page_2': {
        'name': 'Organization Details',
        'fields': [
            {'field': 'organization_name', 'required': True, 'type': 'text', 'label': "Organization's Name"},
            {'field': 'organization_sector', 'required': True, 'type': 'radio', 'label': 'Sector', 'options': ['Academic', 'Industry']}
        ]
    },
    'page_3': {
        'name': 'License Details',
        'fields': [
            {'field': 'num_premium_users', 'required': True, 'type': 'dropdown', 'label': 'Number of Premium users'},
            {'field': 'license_length_years', 'required': True, 'type': 'dropdown', 'label': 'Length of license'}
        ]
    },
    'page_4': {
        'name': 'Admin Information (5+ users)',
        'condition': lambda data: data.num_premium_users >= 5,
        'fields': [
            {'field': 'institution_name', 'required': False, 'type': 'text', 'label': 'Institution name', 'default_to': 'organization_name'},
            {'field': 'admin_name', 'required': False, 'type': 'text', 'label': 'Admin name', 'default_to': 'name'},
            {'field': 'admin_email', 'required': False, 'type': 'email', 'label': 'Admin email', 'default_to': 'email'}
        ]
    },
    'page_5': {
        'name': 'Individual User (1 person)',
        'condition': lambda data: data.num_premium_users == 1,
        'fields': [
            {'field': 'first_user_name', 'required': False, 'type': 'text', 'label': 'First user name', 'default_to': 'name'},
            {'field': 'first_user_email', 'required': False, 'type': 'email', 'label': 'First user email', 'default_to': 'email'}
        ]
    },
    'page_6': {
        'name': 'Two Users Information',
        'condition': lambda data: data.num_premium_users == 2,
        'fields': [
            {'field': 'first_user_name', 'required': False, 'type': 'text', 'label': 'First user name', 'default_to': 'name'},
            {'field': 'first_user_email', 'required': False, 'type': 'email', 'label': 'First user email', 'default_to': 'email'},
            {'field': 'second_user_name', 'required': True, 'type': 'text', 'label': 'Second user name'},
            {'field': 'second_user_email', 'required': True, 'type': 'email', 'label': 'Second user email'}
        ]
    },
    'page_7': {
        'name': 'Billing Information',
        'fields': [
            {'field': 'billing_name', 'required': False, 'type': 'text', 'label': 'Billing name'},
            {'field': 'billing_email', 'required': False, 'type': 'email', 'label': 'Billing email'},
            {'field': 'billing_address', 'required': False, 'type': 'textarea', 'label': 'Billing address'},
            {'field': 'shipping_address', 'required': False, 'type': 'textarea', 'label': 'Shipping address'},
            {'field': 'vat_tax_id', 'required': False, 'type': 'text', 'label': 'VAT or Tax ID'}
        ]
    }
}

class GoogleFormBot:
    """A bot to automate filling a Google Form using Playwright."""

    def __init__(self, headless=True, page_by_page=False):
        self.headless = headless
        self.page_by_page = page_by_page
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def setup(self):
        """Initialize Playwright and launch the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless, args=["--start-maximized"])
        context = await self.browser.new_context(no_viewport=True)
        self.page = await context.new_page()

    async def navigate_to_form(self):
        """Navigate to the Google Form URL with retries."""
        if not self.page:
            return

        for attempt in range(1, 4):
            try:
                logger.info(f"Navigating to form (attempt {attempt}/3): {FORM_URL}")
                await self.page.goto(FORM_URL, timeout=60000)
                # Wait for the form title to be visible as a sign of successful load
                await self.page.wait_for_selector('div[role="heading"]', timeout=20000)
                logger.info("Successfully loaded form")
                return
            except Exception as e:
                logger.warning(f"Failed to load form on attempt {attempt}: {e}")
                if attempt == 3:
                    raise

    async def wait_for_user_input(self, message: str):
        """Pause execution if in page-by-page mode."""
        if self.page_by_page:
            print(f"\n{message}")
            input("Press Enter to continue...")

    async def click_next_button(self) -> bool:
        """Click the 'Next' button on the form."""
        if not self.page:
            return False

        try:
            # The "Next" button is a span inside a div
            next_button = self.page.locator('span:has-text("Next")').first
            await next_button.click(timeout=30000)
            logger.info("✓ Clicked Next button")
            return True
        except Exception as e:
            logger.error(f"❌ Error clicking Next button: {e}")
            return False

    async def click_submit_button(self) -> bool:
        """Click the 'Submit' button on the form."""
        if not self.page:
            return False

        try:
            # Try multiple possible submit button texts
            button_texts = ["Submit", "Request Quote", "Send", "Finish", "Done", "Request a Quote"]
            
            for text in button_texts:
                submit_button = self.page.locator(f'span:has-text("{text}")').first
                if await submit_button.is_visible():
                    await submit_button.click(timeout=10000)
                    logger.info(f"✓ Clicked {text} button")
                    return True
            
            # Also try role-based selection with different texts
            for text in button_texts:
                role_button = self.page.get_by_role("button", name=text)
                if await role_button.is_visible():
                    await role_button.click(timeout=10000)
                    logger.info(f"✓ Clicked {text} button (role-based)")
                    return True
            
            logger.warning("Could not find a visible submit button")
            return False
        except Exception as e:
            logger.error(f"❌ Error clicking Submit button: {e}")
            return False

    async def debug_page_elements(self, page_name: str):
        """Log details about visible form elements for debugging."""
        if not self.page:
            return

        logger.info(f"\n--- DEBUG: {page_name} form elements ---")
        
        # Try to find any heading to identify the page
        try:
            heading = await self.page.locator('div[role="heading"]').first.text_content()
            logger.info(f"Page heading: {heading}")
        except:
            pass
        
        # Check for any visible text that might identify the page
        try:
            page_text = await self.page.locator('div[role="list"]').first.text_content()
            logger.info(f"Page content preview: {page_text[:100]}...")
        except:
            pass
        
        await self.page.screenshot(path=f"quote-bot/page_{page_name.split()[1]}_debug.png")
        logger.info(f"Screenshot saved as page_{page_name.split()[1]}_debug.png")

        visible_inputs = await self.page.locator('input[type="text"]:visible').count()
        logger.info(f"Visible input fields: {visible_inputs}")

        visible_textareas = await self.page.locator('textarea:visible').count()
        logger.info(f"Visible textarea fields: {visible_textareas}")

        dropdown_buttons = await self.page.locator('div[tabindex="0"]').count()
        logger.info(f"Dropdown buttons found: {dropdown_buttons}")

    async def fill_field_with_retry(self, selectors: List[str], value: str, field_name: str) -> bool:
        """Attempt to fill a field using a list of selectors."""
        if not self.page or not value:
            return False

        for i, selector in enumerate(selectors):
            try:
                field = self.page.locator(selector).first
                if await field.is_visible(timeout=5000):
                    await field.fill(value)
                    logger.info(f"✓ Filled {field_name}: {value} (using selector: {selector})")
                    return True
            except Exception:
                logger.debug(f"Selector {i} failed for {field_name}: {selector}")
                continue

        logger.warning(f"✗ Could not fill {field_name}")
        return False

    # --- Page Filling Methods ---

    async def fill_page_1(self, data: FormData) -> bool:
        """Fill Page 1 fields - Name and Email"""
        if not self.page:
            return False
        logger.info("\n=== FILLING PAGE 1 ===")

        # Wait for page to be ready
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 1")

        # Get all text inputs and fill them by position
        inputs = await self.page.locator('input[type="text"], input[type="email"]').all()
        logger.info(f"Found {len(inputs)} input fields on Page 1")

        filled_fields = []

        try:
            # Use positional filling as it's more robust for Google Forms
            logger.info(f"Using position-based filling for {len(inputs)} fields")
            if len(inputs) >= 1 and data.name:
                await inputs[0].fill(data.name)
                logger.info(f"✓ Filled Name (field 0): {data.name}")
                filled_fields.append("Name")

            if len(inputs) >= 2 and data.email:
                await inputs[1].fill(data.email)
                logger.info(f"✓ Filled Email (field 1): {data.email}")
                filled_fields.append("Email")

            # The third field is "send to", which is the alternate email
            if len(inputs) >= 3 and data.alternate_email:
                await inputs[2].fill(data.alternate_email)
                logger.info(f"✓ Filled Send to (field 2): {data.alternate_email}")
                filled_fields.append("Send to")

        except Exception as e:
            logger.error(f"Error during positional filling on Page 1: {e}")
            # Fallback to selector-based filling
            logger.info("Using selector-based filling")
            await self.fill_field_with_retry(['input[aria-label*="name" i]'], data.name, "Name")
            await self.fill_field_with_retry(['input[aria-label*="email" i]'], data.email, "Email")

        logger.info(f"✅ Page 1 completed! Filled fields: {', '.join(filled_fields)}")

        await self.wait_for_user_input("Page 1 completed. Check the form and verify the data is correct.")

        return await self.click_next_button()

    async def fill_page_2(self, data: FormData) -> bool:
        """Fill Page 2 fields - Organization name and sector"""
        if not self.page:
            return False
        logger.info("\n=== FILLING PAGE 2 ===")

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 2")

        # 1. FILL ORGANIZATION NAME FIELD
        logger.info(f"\n--- Filling Organization Name: {data.organization_name} ---")

        org_filled = False
        try:
            # More direct approach for Page 2: find the single visible text input.
            text_inputs = await self.page.locator('input[type="text"]').all()

            visible_inputs = []
            for i in text_inputs:
                if await i.is_visible():
                    visible_inputs.append(i)

            if visible_inputs:
                logger.info(f"Found {len(visible_inputs)} visible text input(s). Filling the first one.")
                # Using .fill() which is often more reliable than typing character by character.
                await visible_inputs[0].fill(data.organization_name)
                org_filled = True
                logger.info(f"✓ Filled Organization Name: {data.organization_name}")
            else:
                # If no 'input[type="text"]' is found, try to find a textarea as a fallback.
                logger.info("No visible text inputs found, trying to find a textarea.")
                text_areas = await self.page.locator('textarea:visible').all()
                if text_areas:
                    await text_areas[0].fill(data.organization_name)
                    org_filled = True
                    logger.info(f"✓ Filled Organization Name (in textarea): {data.organization_name}")

        except Exception as e:
            logger.error(f"Error filling organization name on Page 2: {e}")

        if not org_filled:
            logger.warning("✗ Could not fill organization name field using direct approach")

        # 2. SELECT ACADEMIC/INDUSTRY
        logger.info(f"\n--- Selecting Sector: {data.organization_sector} ---")
        sector_selected = False
        try:
            sector_label = data.organization_sector or "Academic"
            sector_radio = self.page.locator(f'label:has-text("{sector_label}")')

            if await sector_radio.is_visible():
                await sector_radio.click()
                logger.info(f'✓ Selected sector: {sector_label} via label:has-text("{sector_label}")')
                sector_selected = True
            else:
                # Fallback for when label isn't directly clickable
                radio_button = self.page.locator(f'div[aria-label="{sector_label}"]').first
                if await radio_button.is_visible():
                    await radio_button.click()
                    logger.info(f"✓ Selected sector: {sector_label} via div[aria-label]")
                    sector_selected = True

        except Exception as e:
            logger.warning(f"Could not select sector '{data.organization_sector}': {e}")

        if not org_filled:
            logger.warning("❌ Could not fill organization name!")
        if not sector_selected:
            logger.warning("❌ Could not select organization sector!")

        logger.info("✅ Page 2 completed!")
        await self.wait_for_user_input("Page 2 completed. Check the organization name and sector.")

        return await self.click_next_button()

    async def fill_page_3(self, data: FormData):
        """Fill Page 3 fields - Number of Premium users and License length dropdowns"""
        if not self.page:
            return False
        logger.info("\n=== FILLING PAGE 3 ===")

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 3")

        # Get ALL elements with tabindex="0" and role="option"
        all_dropdowns = await self.page.locator('div[tabindex="0"][role="option"]').all()
        logger.info(f"Found {len(all_dropdowns)} total dropdown elements")

        # 1. FILL FIRST DROPDOWN (Users) - Should be at index 0
        logger.info(f"\n--- Selecting Number of Premium Users: {data.num_premium_users} ---")
        users_selected = False
        
        if len(all_dropdowns) >= 2:
            try:
                # Click first dropdown (index 0)
                await all_dropdowns[0].click()
                logger.info("Clicked dropdown at index 0")
                await asyncio.sleep(1.5)
                
                # Select the number
                target = str(data.num_premium_users)
                if data.num_premium_users >= 16:
                    await self.page.locator('div[role="option"]:has-text("16+")').click()
                else:
                    await self.page.locator(f'div[role="option"][data-value="{target}"]').first.click()
                
                users_selected = True
                logger.info(f"✓ Selected {data.num_premium_users} users")
                
            except Exception as e:
                logger.error(f"Error selecting users: {e}")
        
        # Wait for first dropdown to settle
        await asyncio.sleep(3)
        
        # 2. FILL SECOND DROPDOWN (License) - Should be at index 1
        logger.info(f"\n--- Selecting License Length: {data.license_length_years} years ---")
        license_selected = False
        
        if len(all_dropdowns) >= 2:
            try:
                # Click second dropdown (index 1)
                await all_dropdowns[1].click()
                logger.info("Clicked dropdown at index 1")
                await asyncio.sleep(1.5)
                
                # Select the year
                target = str(data.license_length_years)
                await self.page.locator(f'div[role="option"][data-value="{target}"]').last.click()
                
                license_selected = True
                logger.info(f"✓ Selected {data.license_length_years} year license")
                
            except Exception as e:
                logger.error(f"Error selecting license: {e}")
        
        if users_selected and license_selected:
            logger.info("✅ Both dropdowns completed!")
        else:
            logger.error(f"❌ Failed - Users: {users_selected}, License: {license_selected}")
        
        await self.wait_for_user_input("Page 3 completed. Please verify both dropdowns are filled.")
        
        # Try clicking Next twice for Page 3
        logger.info("Clicking Next button (first attempt)...")
        success = await self.click_next_button()
        
        if success:
            # Wait a bit and click again
            await asyncio.sleep(2)
            logger.info("Clicking Next button again (Page 3 sometimes requires double-click)...")
            await self.click_next_button()
        
        return success

    async def fill_page_4(self, data: FormData) -> bool:
        """Fill Page 4 fields - Institution name, Admin name, Admin email (all optional)"""
        logger.info("\n=== FILLING PAGE 4 ===")
        if not self.page:
            return False

        await self.page.wait_for_load_state('networkidle')
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

        # Debug the real form elements
        await self.debug_page_elements("Page 4")

        # Set defaults for optional fields
        institution_name = data.institution_name or data.organization_name
        admin_name       = data.admin_name       or data.name
        admin_email      = data.admin_email      or data.email

        filled_count = 0

        try:
            logger.info("Attempting to fill Page 4 fields by position.")

            # Get all visible text and email inputs
            text_inputs = await self.page.locator('input[type="text"]:visible').all()
            email_inputs = await self.page.locator('input[type="email"]:visible').all()

            logger.info(f"Found {len(text_inputs)} visible text inputs and {len(email_inputs)} visible email inputs.")

            # Fill Institution Name (first text input)
            if institution_name and text_inputs:
                await text_inputs[0].fill(institution_name)
                logger.info(f"✓ Filled Institution: {institution_name}")
                filled_count += 1

            # Fill Admin Name (second text input, if it exists)
            if admin_name and len(text_inputs) > 1:
                await text_inputs[1].fill(admin_name)
                logger.info(f"✓ Filled Admin Name: {admin_name}")
                filled_count += 1
            elif admin_name:
                 logger.warning("Could not fill Admin Name: only one text input found.")

            # Fill Admin Email (first email input)
            if admin_email and email_inputs:
                await email_inputs[0].fill(admin_email)
                logger.info(f"✓ Filled Admin Email: {admin_email}")
                filled_count += 1

        except Exception as e:
            logger.error(f"Error during positional filling on Page 4: {e}")
            # Fallback to the old method if positional fails
            logger.info("Falling back to selector-based filling for Page 4.")
            filled_count = 0 # Reset count for fallback
            if institution_name:
                inst_selectors = ['input[aria-label*="institution" i]', 'input[type="text"]:visible']
                if await self.fill_field_with_retry(inst_selectors, institution_name, "Institution"):
                    filled_count += 1
            if admin_name:
                # This selector is weak, but we keep it for the fallback
                admin_selectors = ['input[aria-label*="admin name" i]']
                if await self.fill_field_with_retry(admin_selectors, admin_name, "Admin Name"):
                    filled_count += 1
            if admin_email:
                email_selectors = ['input[type="email"]', 'input[aria-label*="admin email" i]']
                if await self.fill_field_with_retry(email_selectors, admin_email, "Admin Email"):
                    filled_count += 1

        logger.info(f"✅ Page 4 completed! Filled {filled_count}/3 optional fields")

        await self.wait_for_user_input("Page 4 completed. Check the optional fields.")

        return await self.click_next_button()

    async def fill_page_5(self, data: FormData) -> bool:
        """Handle Page 5, which is for single-user licenses. The two fields are optional."""
        if not self.page:
            return False
        logger.info("\n=== HANDLING PAGE 5 (SINGLE USER) ===")

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 5")

        logger.info("Page 5 is for single-user licenses. Fields are optional and will be left blank.")

        await self.wait_for_user_input("Page 5 has optional fields that will be skipped.")

        return await self.click_next_button()

    async def fill_page_6(self, data: FormData) -> bool:
        """Fill Page 6 fields - Individual user information for small labs"""
        if not self.page:
            return False
        logger.info("\n=== FILLING PAGE 6 ===")

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 6")

        # Extract second user's info from the combined string
        second_user_name = ""
        second_user_email = ""
        if data.user_names_emails:
            # Simple extraction: find email and assume rest is name
            emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', data.user_names_emails)
            for email in emails:
                if email.lower() != data.email.lower():
                    second_user_email = email
                    break

            if second_user_email:
                # Get the name part by removing the email and extra characters
                name_part = data.user_names_emails.replace(second_user_email, '').strip()
                name_part = re.sub(r'[\(\)–,]', '', name_part).strip()
                second_user_name = name_part

        logger.info(f"Extracted for Page 6: Name='{second_user_name}', Email='{second_user_email}'")

        # Fill fields positionally
        text_inputs = await self.page.locator('input[type="text"]:visible').all()
        email_inputs = await self.page.locator('input[type="email"]:visible').all()

        filled_count = 0

        # Page 6 has optional fields for first user, so we skip to second user
        if second_user_name and len(text_inputs) > 1:
            await text_inputs[1].fill(second_user_name)
            logger.info(f"✓ Filled Second User Name: {second_user_name}")
            filled_count += 1

        if second_user_email and len(email_inputs) > 1:
            await email_inputs[1].fill(second_user_email)
            logger.info(f"✓ Filled Second User Email: {second_user_email}")
            filled_count += 1

        logger.info(f"✅ Page 6 completed! Filled {filled_count}/2 required fields.")

        await self.wait_for_user_input("Page 6 completed. Check the second user's details.")

        return await self.click_next_button()

    async def fill_page_7(self, data: FormData) -> bool:
        """Fill Page 7 fields - Billing information (final page)"""
        if not self.page:
            return False
        logger.info("\n=== FILLING PAGE 7 ===")

        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)

        await self.debug_page_elements("Page 7")

        # Use only explicitly provided billing info. Do not fall back to main contact details.
        billing_name = data.billing_name
        billing_email = data.billing_email
        billing_address = data.billing_address
        shipping_address = data.shipping_address or billing_address

        filled_count = 0

        # Fill billing name
        if billing_name:
            name_selectors = [
                'input[aria-label*="billing name" i]',
                'input[aria-label*="billing" i][aria-label*="name" i]',
                'input[aria-label*="name" i]:not([aria-label*="ticket" i])',
                'input[type="text"]:not([aria-label*="ticket" i])'
            ]
            if await self.fill_field_with_retry(name_selectors, billing_name, "Billing Name"):
                filled_count += 1

        # Fill billing email
        if billing_email:
            email_selectors = [
                'input[aria-label*="billing email" i]',
                'input[aria-label*="billing" i][aria-label*="email" i]',
                'input[type="email"]',
                'input[aria-label*="email" i]:not([aria-label*="ticket" i])'
            ]
            if await self.fill_field_with_retry(email_selectors, billing_email, "Billing Email"):
                filled_count += 1

        # Debug log the address values
        logger.info(f"DEBUG - billing_address: '{billing_address}'")
        logger.info(f"DEBUG - shipping_address: '{shipping_address}'")
        logger.info("Entering address filling section...")

        # Fill billing and shipping addresses
        text_areas = await self.page.locator('textarea:visible').all()
        logger.info(f"Found {len(text_areas)} textarea fields")

        if len(text_areas) == 2:
            if billing_address:
                await text_areas[0].fill(billing_address)
                logger.info(f"✓ Filled Billing Address: {billing_address}")
                filled_count += 1
            else:
                logger.info("No billing address provided, leaving first textarea empty")

            if shipping_address:
                logger.info(f"Attempting to fill second textarea (shipping) with: {shipping_address}")
                await text_areas[1].fill(shipping_address)
                logger.info(f"✓ Filled Shipping Address: {shipping_address}")
                filled_count += 1
            else:
                logger.info("No shipping address provided, leaving second textarea empty")
        elif len(text_areas) == 1:
            # If only one textarea, assume it's for billing address
            if billing_address:
                await text_areas[0].fill(billing_address)
                logger.info(f"✓ Filled Billing Address (single textarea): {billing_address}")
                filled_count += 1

        # Fill VAT/Tax ID
        if data.vat_tax_id:
            # Find a text input that contains "VAT" or "Tax" in its label
            vat_inputs = await self.page.locator('input[type="text"][aria-label*="vat" i], input[type="text"][aria-label*="tax" i]').all()
            if vat_inputs:
                await vat_inputs[0].fill(data.vat_tax_id)
                logger.info(f"✓ Filled VAT/Tax ID: {data.vat_tax_id}")
                filled_count += 1
            else:
                logger.warning("✗ Could not fill VAT/Tax ID - field not found")

        logger.info(f"✅ Page 7 completed! Filled {filled_count} fields")

        await self.wait_for_user_input("Page 7 (final page) completed. Check the billing details.")

        submit_success = await self.click_submit_button()
        
        if submit_success:
            # Wait and check for success message
            await asyncio.sleep(3)
            try:
                if await self.page.locator('text="Your response has been recorded"').count() > 0:
                    logger.info("✅ Form submitted successfully! Response recorded.")
                elif await self.page.locator('text="response has been recorded"').count() > 0:
                    logger.info("✅ Form submitted successfully!")
            except:
                pass
        
        return submit_success

    async def cleanup(self):
        """Close the browser and stop Playwright."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed and Playwright stopped.")

    # --- New Validation and Workflow Methods ---

    async def validate_required_fields(self, page_key: str, data: FormData) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields have data for a given page.
        Returns (is_valid, list_of_missing_fields)
        """
        if page_key not in FORM_STRUCTURE:
            return True, []

        page_config = FORM_STRUCTURE[page_key]
        missing_fields = []

        for field_config in page_config['fields']:
            if field_config.get('required', False):
                field_name = field_config['field']
                field_label = field_config['label']

                value = getattr(data, field_name, None)

                # Special handling for Page 6 second user fields
                if page_key == 'page_6' and field_name in ['second_user_name', 'second_user_email']:
                    if not value and data.user_names_emails:
                        emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', data.user_names_emails)
                        non_primary_emails = [e for e in emails if e.lower() != data.email.lower()]

                        if field_name == 'second_user_email' and non_primary_emails:
                            value = non_primary_emails[0]
                        elif field_name == 'second_user_name' and non_primary_emails:
                            email_to_remove = non_primary_emails[0]
                            name_part = data.user_names_emails.replace(email_to_remove, '').strip()
                            name_part = re.sub(r'[\(\)–,]', '', name_part).strip()
                            value = name_part

                if not value:
                    missing_fields.append(field_label)

        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields

    async def check_for_form_errors(self) -> List[str]:
        """
        Check if the form is showing any validation errors after clicking Next/Submit.
        Google Forms shows errors with role="alert"
        """
        if not self.page:
            return []

        try:
            await asyncio.sleep(1)  # Give form time to show errors

            error_elements = await self.page.locator('[role="alert"]').all()
            errors = []

            for element in error_elements:
                text = await element.text_content()
                if text and text.strip():
                    errors.append(text.strip())

            # Also check for the generic "Required question" indicators
            required_indicators = await self.page.locator('span:has-text("This is a required question")').all()
            if required_indicators and not errors:
                errors.append(f"Found {len(required_indicators)} required field(s) not filled")

            return errors

        except Exception as e:
            logger.debug(f"Error checking for form validation errors: {e}")
            return []

    async def display_validation_summary(self, data: FormData) -> None:
        """Display a summary of what will be filled and what's missing"""
        logger.info("\n=== PRE-FILL VALIDATION SUMMARY ===")

        # Determine which pages will be shown
        if data.num_premium_users == 1:
            active_pages = ['page_1', 'page_2', 'page_3', 'page_5', 'page_7']
        elif data.num_premium_users == 2:
            active_pages = ['page_1', 'page_2', 'page_3', 'page_6', 'page_7']
        else:
            active_pages = ['page_1', 'page_2', 'page_3', 'page_4', 'page_7']

        all_valid = True

        for page_key in active_pages:
            if page_key not in FORM_STRUCTURE:
                continue

            page_config = FORM_STRUCTURE[page_key]
            page_name = page_config['name']

            # Now we can use await directly since this method is async
            is_valid, missing_fields = await self.validate_required_fields(page_key, data)

            if is_valid:
                logger.info(f"✅ {page_name}: All required fields have data")
            else:
                logger.warning(f"⚠️  {page_name}: Missing required fields: {', '.join(missing_fields)}")
                all_valid = False

        if all_valid:
            logger.info("\n✅ All required fields have data! Form should submit successfully.")
        else:
            logger.warning("\n⚠️  Some required fields are missing. The form may show validation errors.")

        logger.info("===================================\n")

    async def run_automation(self, message: str):
        """Enhanced automation workflow with field validation"""
        try:
            parser = MessageParser()
            data = parser.extract_data(message)

            await self.display_validation_summary(data)

            # Pre-validate critical fields
            is_valid, missing = await self.validate_required_fields('page_1', data)
            if not is_valid:
                logger.error(f"❌ Cannot proceed - missing critical fields: {', '.join(missing)}")
                logger.error("These fields are required to start the form.")
                return

            await self.setup()
            await self.navigate_to_form()

            # Determine page sequence
            page_sequence = ['page_1', 'page_2', 'page_3']
            if data.num_premium_users == 1:
                page_sequence.extend(['page_5', 'page_7'])
            elif data.num_premium_users == 2:
                page_sequence.extend(['page_6', 'page_7'])
            else:
                page_sequence.extend(['page_4', 'page_7'])

            page_functions = {
                'page_1': self.fill_page_1, 'page_2': self.fill_page_2, 'page_3': self.fill_page_3,
                'page_4': self.fill_page_4, 'page_5': self.fill_page_5, 'page_6': self.fill_page_6,
                'page_7': self.fill_page_7
            }

            # Process each page
            for page_key in page_sequence:
                page_config = FORM_STRUCTURE.get(page_key, {})
                page_name = page_config.get('name', page_key)

                logger.info(f"🔄 Starting {page_name}...")

                fill_func = page_functions[page_key]
                success = await fill_func(data)

                if success and page_key != 'page_7':
                    errors = await self.check_for_form_errors()
                    if errors:
                        logger.error(f"❌ Form validation errors on {page_name}:")
                        for error in errors: logger.error(f"   - {error}")

                        if self.page_by_page:
                            input(f"\n⚠️  Please manually fill required fields and click Next, then press Enter...")
                        else:
                            logger.error("Cannot proceed due to validation errors.")
                            break

                if not success and page_key != 'page_7':
                    logger.error(f"❌ Failed to complete {page_name}")
                    break

                logger.info(f"✅ {page_name} completed!")

            logger.info("🎉 Form automation completed!")

            if self.page_by_page:
                input("\nPress Enter to close browser...")

        except Exception as e:
            logger.error(f"Error during automation: {e}", exc_info=True)
            if self.page:
                await self.page.screenshot(path="quote-bot/error_screenshot.png")
                logger.info("Error screenshot saved as quote-bot/error_screenshot.png")
        finally:
            await self.cleanup()

async def main():
    """Main function to run the bot."""

    # --- Get User Input ---
    print("Paste your message below (press Enter twice to finish):")
    lines = []
    while True:
        try:
            line = input()
            if not line:
                break
            lines.append(line)
        except EOFError:
            break
    message = "\n".join(lines)

    headless_input = input("Run in headless mode? (y/n, default: n): ")
    headless = headless_input.lower() == 'y'

    page_by_page_input = input("Run in page-by-page mode (pause after each page)? (y/n, default: y): ")
    page_by_page = page_by_page_input.lower() != 'n'

    # --- Run Bot ---
    bot = GoogleFormBot(headless=headless, page_by_page=page_by_page)
    await bot.run_automation(message)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nAutomation interrupted by user.")
