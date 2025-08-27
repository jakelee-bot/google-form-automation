#!/usr/bin/env bash
# Install dependencies
pip install -r requirements.txt

# Install playwright and browsers
pip install playwright
python -m playwright install chromium
python -m playwright install-deps