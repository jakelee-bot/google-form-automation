import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the automation bot."""
    # Form settings
    FORM_URL = os.getenv('FORM_URL', 'https://docs.google.com/forms/d/e/1FAIpQLScy9oI-x2tmtCuE1rb6iZFZnhoPW9qutQBiml0A-4MM2eOa0g/viewform')
    
    # Run settings
    DEFAULT_HEADLESS = os.getenv('DEFAULT_HEADLESS', 'false').lower() == 'true'
    DEFAULT_PAGE_BY_PAGE = os.getenv('DEFAULT_PAGE_BY_PAGE', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'form_automation.log'
    
    # Timeouts
    DEFAULT_TIMEOUT = 30000
    NAVIGATION_TIMEOUT = 60000
    
    # Directories
    SCREENSHOT_DIR = 'screenshots'

config = Config()