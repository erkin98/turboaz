#!/usr/bin/env python3
import asyncio
import logging
import os
from typing import List

import httpx

from car_scraper import CarListing
from config import BOT_TOKEN, CHAT_ID

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TurboAzBot:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")

        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")
        if not self.chat_id:
            raise ValueError("CHAT_ID environment variable is required")

    def format_car_message(self, car: CarListing) -> str:
        """Format a comprehensive car message with all available specifications."""

        # Header with car emoji and basic info
        message = f"🚗 **New Car Alert!**\n\n"
        message += f"**{car.title}**\n"
        message += f"💰 **{car.price}**\n\n"

        # Essential details section
        message += "📋 **Essential Details:**\n"
        if car.year and car.year != "N/A":
            message += f"📅 Year: {car.year}\n"
        if car.mileage and car.mileage != "N/A":
            message += f"🔄 Mileage: {car.mileage}\n"
        if car.engine_details:
            message += f"⚙️ Engine: {car.engine_details}\n"
        elif car.engine and car.engine != "N/A":
            message += f"⚙️ Engine: {car.engine}\n"

        # Location and ownership
        if car.city:
            message += f"📍 City: {car.city}\n"
        if car.owners:
            message += f"👥 Previous Owners: {car.owners}\n"

        message += "\n"

        # Vehicle specifications
        message += "🔧 **Vehicle Specs:**\n"
        if car.brand:
            message += f"🚗 Brand: {car.brand}\n"
        if car.model:
            message += f"🏷️ Model: {car.model}\n"
        if car.body_type:
            message += f"🚙 Body Type: {car.body_type}\n"
        if car.color:
            message += f"🎨 Color: {car.color}\n"
        if car.transmission:
            message += f"🔧 Transmission: {car.transmission}\n"
        if car.drivetrain:
            message += f"⚙️ Drivetrain: {car.drivetrain}\n"

        # Condition and market info
        if car.condition or car.is_new or car.market:
            message += "\n🔍 **Condition & Info:**\n"
            if car.is_new:
                message += f"✨ New: {car.is_new}\n"
            if car.condition:
                message += f"🔍 Condition: {car.condition}\n"
            if car.market:
                message += f"🌍 Market: {car.market}\n"

        # Additional features
        if car.seats:
            message += f"\n💺 Seats: {car.seats}\n"

        # Description (limited)
        if car.description and len(car.description) > 10:
            desc = (
                car.description[:150] + "..."
                if len(car.description) > 150
                else car.description
            )
            message += f"\n📝 **Description:**\n_{desc}_\n"

        # Additional specifications summary
        if car.specifications and len(car.specifications) > 5:
            message += f"\n📊 **Complete Specs:** {len(car.specifications)} details available\n"

        # Link to the listing
        message += f"\n🔗 [View on Turbo.az]({car.url})"

        return message

    async def send_car_notification(self, car: CarListing) -> bool:
        """Send a detailed car notification via Telegram."""
        try:
            message = self.format_car_message(car)

            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

            # Prepare the data
            data = {
                "chat_id": self.chat_id,
                "caption": message,
                "parse_mode": "Markdown",
            }

            # Add image if available
            if car.image_url:
                data["photo"] = car.image_url
            else:
                # If no image, send as text message instead
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()

            logger.info(f"Sent enhanced notification for car: {car.car_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification for car {car.car_id}: {e}")
            return False

    async def send_multiple_cars(self, cars: List[CarListing]) -> int:
        """Send notifications for multiple cars with enhanced details."""
        successful = 0

        for car in cars:
            try:
                if await self.send_car_notification(car):
                    successful += 1
                # Small delay between messages to avoid rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error sending notification for car {car.car_id}: {e}")

        return successful

    async def send_status_message(self, message: str):
        """Send a status message to the chat."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": f"🤖 *Bot Status:* {message}",
                "parse_mode": "Markdown",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()

            logger.info(f"Sent status message: {message}")
        except Exception as e:
            logger.error(f"Failed to send status message: {e}")

    async def test_connection(self) -> bool:
        """Test the Telegram bot connection with enhanced format preview."""
        try:
            # Create a sample car for testing
            from car_scraper import CarListing

            test_car = CarListing(
                car_id="TEST123",
                title="Test Car - Jeep Grand Cherokee",
                price="20,000 AZN",
                year="2012",
                mileage="137,000 km",
                engine="5.7 L / 360 a.g. / Benzin",
                url="https://turbo.az",
                image_url="https://via.placeholder.com/400x300/4CAF50/white?text=TEST+CAR",
            )

            # Add enhanced details
            test_car.city = "Bakı"
            test_car.brand = "Jeep"
            test_car.model = "Grand Cherokee"
            test_car.color = "Qara"
            test_car.transmission = "Avtomat"
            test_car.body_type = "Offroader / SUV, 5 qapı"
            test_car.drivetrain = "Tam"
            test_car.condition = "Vuruğu yoxdur, rənglənib"
            test_car.owners = "2"
            test_car.market = "Amerika"
            test_car.specifications = {
                "Şəhər": "Bakı",
                "Marka": "Jeep",
                "Model": "Grand Cherokee",
                "Rəng": "Qara",
                "Mühərrik": "5.7 L / 360 a.g. / Benzin",
            }

            message = "🧪 **Bot Connection Test**\n\n"
            message += "✅ Enhanced Telegram notifications are working!\n\n"
            message += "🎉 **Features now include:**\n"
            message += "• Complete car specifications\n"
            message += "• City, brand, model details\n"
            message += "• Color and transmission info\n"
            message += "• Condition and ownership data\n"
            message += "• Engine specifications\n"
            message += "• High-quality car images\n\n"
            message += "**Sample notification format:**\n"
            message += "─" * 30 + "\n"
            message += self.format_car_message(test_car)

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()

            logger.info("Enhanced bot connection test successful")
            return True

        except Exception as e:
            logger.error(f"Bot connection test failed: {e}")
            return False
