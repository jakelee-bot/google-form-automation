#!/usr/bin/env python3
"""
Test script for local development
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.form_automation import GoogleFormBot, MessageParser

test_message = """
Your name: John Doe
Your email: john.doe@example.com
Organization name: Acme University
Organization sector: Academic
How many people need Premium access? 2
Length of license: 1
Names and emails of intended users: Jane Smith (jane.smith@example.com)
"""

async def test():
    parser = MessageParser()
    data = parser.extract_data(test_message)
    
    print("\n=== EXTRACTED DATA ===")
    print(f"  Name: {data.name}")
    print(f"  Email: {data.email}")
    print(f"  Organization: {data.organization_name}")
    print(f"  Sector: {data.organization_sector}")
    print(f"  Users: {data.num_premium_users}")
    print(f"  License Years: {data.license_length_years}")
    print(f"  User Names/Emails: {data.user_names_emails}")
    print("===================\n")
    
    # Ask if user wants to run the full automation
    response = input("Do you want to run the full form automation? (y/n): ")
    if response.lower() == 'y':
        print("\nStarting form automation...")
        bot = GoogleFormBot(headless=False, page_by_page=True)
        await bot.run_automation(test_message)

if __name__ == "__main__":
    asyncio.run(test())