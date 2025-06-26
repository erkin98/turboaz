#!/usr/bin/env python3
import os

from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Your chat ID or channel ID where updates will be sent

# Turbo.az URL with your specific requirements
TURBO_AZ_URL = "https://turbo.az/autos?page=1&price_from=17000&price_to=22000&used=1&year_to=2015&engine_from=2.3&kilometers_to=150000"

# Monitoring settings
CHECK_INTERVAL_MINUTES = 10  # Increased from 5 to 10 minutes
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # Increased timeout for better reliability

# Rate limiting settings
MAX_REQUESTS_PER_HOUR = 100  # Conservative limit
MIN_REQUEST_DELAY = 2.0  # Minimum 2 seconds between requests
CACHE_DURATION_HOURS = 24  # Cache car details for 24 hours

# File to store known car IDs
KNOWN_CARS_FILE = "known_cars.txt"

# Logging settings
LOG_LEVEL = "INFO"
