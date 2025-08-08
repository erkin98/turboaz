import asyncio
import logging
import os
from typing import List, Set

from bot import TurboAzBot
from car_scraper import CarListing, TurboAzScraper
from config import BOT_TOKEN, CHAT_ID, KNOWN_CARS_FILE

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CarMonitor:
    def __init__(self):
        self.scraper = TurboAzScraper()
        # Telegram is optional: only initialize when credentials are provided
        if BOT_TOKEN and CHAT_ID:
            try:
                self.bot = TurboAzBot()
            except Exception as e:
                logger.warning(f"Telegram disabled due to configuration error: {e}")
                self.bot = None
        else:
            logger.info("Telegram not configured; running in web-only mode")
            self.bot = None
        self.known_cars: Set[str] = set()
        self.current_url = None  # Store the current URL
        self.load_known_cars()

    def set_url(self, url: str):
        """Set the URL to use for monitoring."""
        self.current_url = url
        logger.info(f"Updated monitoring URL: {url}")

    def load_known_cars(self):
        """Load previously seen car IDs from file."""
        if os.path.exists(KNOWN_CARS_FILE):
            try:
                with open(KNOWN_CARS_FILE, "r") as f:
                    self.known_cars = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.known_cars)} known car IDs")
            except Exception as e:
                logger.error(f"Error loading known cars: {e}")
                self.known_cars = set()
        else:
            logger.info("No previous car data found, starting fresh")

    def save_known_cars(self):
        """Save current known car IDs to file."""
        try:
            with open(KNOWN_CARS_FILE, "w") as f:
                for car_id in sorted(self.known_cars):
                    f.write(f"{car_id}\n")
            logger.info(f"Saved {len(self.known_cars)} known car IDs")
        except Exception as e:
            logger.error(f"Error saving known cars: {e}")

    def add_known_car(self, car_id: str):
        """Add a car ID to the known cars set and save to file."""
        self.known_cars.add(car_id)
        self.save_known_cars()

    def filter_new_cars(self, cars: List[CarListing]) -> List[CarListing]:
        """Filter out cars that we've already seen."""
        new_cars = []
        for car in cars:
            if car.car_id not in self.known_cars:
                new_cars.append(car)
                self.add_known_car(car.car_id)

        return new_cars

    async def check_for_new_cars(self, url: str = None) -> int:
        """Check for new cars and send notifications."""
        logger.info("Checking for new cars...")

        try:
            # Use provided URL or fallback to current URL
            search_url = url or self.current_url

            # Get current cars from website
            current_cars = self.scraper.get_new_cars(search_url)

            if not current_cars:
                logger.warning("No cars found on the website")
                return 0

            # Filter out cars we've already seen
            new_cars = self.filter_new_cars(current_cars)

            if new_cars:
                logger.info(f"Found {len(new_cars)} new cars!")

                # Send notifications for new cars (if Telegram is enabled)
                if self.bot:
                    successful = await self.bot.send_multiple_cars(new_cars)
                    logger.info(
                        f"Successfully sent {successful}/{len(new_cars)} notifications"
                    )
                else:
                    logger.info("Telegram disabled; skipping notifications")

                return len(new_cars)
            else:
                logger.info("No new cars found")
                return 0

        except Exception as e:
            logger.error(f"Error checking for new cars: {e}")
            try:
                if self.bot:
                    await self.bot.send_status_message(f"Error occurred: {str(e)}")
            except Exception:
                pass
            return 0

    async def initialize_monitoring(self, url: str = None) -> bool:
        """Initialize the monitoring system."""
        logger.info("Initializing car monitoring...")

        # Store the URL if provided
        if url:
            self.set_url(url)

        # Test bot connection if enabled
        if self.bot:
            if not await self.bot.test_connection():
                logger.error("Failed to connect to Telegram bot")
                return False

        # If this is the first run, populate known cars without sending notifications
        if not self.known_cars:
            logger.info("First run - populating known cars without notifications...")
            search_url = url or self.current_url
            current_cars = self.scraper.get_new_cars(search_url)
            for car in current_cars:
                self.add_known_car(car.car_id)

            await self.bot.send_status_message(
                f"Monitoring initialized with {len(current_cars)} existing cars. "
                "I'll now monitor for new listings!"
            )

        return True
