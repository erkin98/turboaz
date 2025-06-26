#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from datetime import datetime

from car_monitor import CarMonitor
from config import CHECK_INTERVAL_MINUTES

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("turbo_bot.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class TurboAzMonitorApp:
    def __init__(self):
        self.monitor = CarMonitor()
        self.running = False

    async def run_monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting Turbo.az car monitoring bot...")

        # Initialize monitoring
        if not await self.monitor.initialize_monitoring():
            logger.error("Failed to initialize monitoring. Exiting.")
            return

        self.running = True
        check_count = 0

        while self.running:
            try:
                check_count += 1
                logger.info(f"--- Check #{check_count} at {datetime.now()} ---")

                new_cars_count = await self.monitor.check_for_new_cars()

                if new_cars_count > 0:
                    logger.info(
                        f"✅ Found and notified about {new_cars_count} new cars"
                    )
                else:
                    logger.info("ℹ️ No new cars found")

                # Wait for next check
                logger.info(
                    f"Waiting {CHECK_INTERVAL_MINUTES} minutes until next check..."
                )
                await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        logger.info("Stop signal received")


# Global app instance for signal handling
app = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}")
    if app:
        app.stop()


async def main():
    """Main entry point."""
    global app

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = TurboAzMonitorApp()

    try:
        await app.run_monitoring_loop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Turbo.az monitoring bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
