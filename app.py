#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_socketio import SocketIO, emit

from car_monitor import CarMonitor
from car_scraper import CarListing
from config import BOT_TOKEN, CHAT_ID, CHECK_INTERVAL_MINUTES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-change-this")
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
monitor = None
monitoring_thread = None
is_monitoring = False


class DatabaseManager:
    def __init__(self, db_path="app_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create enhanced cars table with all details
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS found_cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id TEXT UNIQUE,
                title TEXT,
                price TEXT,
                year TEXT,
                mileage TEXT,
                engine TEXT,
                url TEXT,
                image_url TEXT,
                city TEXT,
                brand TEXT,
                model TEXT,
                body_type TEXT,
                color TEXT,
                engine_details TEXT,
                transmission TEXT,
                drivetrain TEXT,
                is_new TEXT,
                seats TEXT,
                owners TEXT,
                condition_info TEXT,
                market TEXT,
                description TEXT,
                all_images TEXT,
                specifications TEXT,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT FALSE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def save_car(self, car: CarListing, notified=False):
        """Save a found car to the database with all details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Convert lists and dicts to JSON strings
            all_images_json = json.dumps(car.all_images) if car.all_images else None
            specifications_json = (
                json.dumps(car.specifications) if car.specifications else None
            )

            # Try to update existing record first (to avoid resetting found_at)
            cursor.execute(
                """
                UPDATE found_cars SET 
                    title=?, price=?, year=?, mileage=?, engine=?, url=?, image_url=?,
                    city=?, brand=?, model=?, body_type=?, color=?, engine_details=?, transmission=?,
                    drivetrain=?, is_new=?, seats=?, owners=?, condition_info=?, market=?, description=?,
                    all_images=?, specifications=?, notified=?
                WHERE car_id=?
            """,
                (
                    car.title,
                    car.price,
                    car.year,
                    car.mileage,
                    car.engine,
                    car.url,
                    car.image_url,
                    car.city,
                    car.brand,
                    car.model,
                    car.body_type,
                    car.color,
                    car.engine_details,
                    car.transmission,
                    car.drivetrain,
                    car.is_new,
                    car.seats,
                    car.owners,
                    car.condition,
                    car.market,
                    car.description,
                    all_images_json,
                    specifications_json,
                    notified,
                    car.car_id,
                ),
            )

            if cursor.rowcount == 0:
                # No existing row; insert new
                cursor.execute(
                    """
                    INSERT INTO found_cars 
                    (car_id, title, price, year, mileage, engine, url, image_url,
                     city, brand, model, body_type, color, engine_details, transmission,
                     drivetrain, is_new, seats, owners, condition_info, market, description,
                     all_images, specifications, notified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        car.car_id,
                        car.title,
                        car.price,
                        car.year,
                        car.mileage,
                        car.engine,
                        car.url,
                        car.image_url,
                        car.city,
                        car.brand,
                        car.model,
                        car.body_type,
                        car.color,
                        car.engine_details,
                        car.transmission,
                        car.drivetrain,
                        car.is_new,
                        car.seats,
                        car.owners,
                        car.condition,
                        car.market,
                        car.description,
                        all_images_json,
                        specifications_json,
                        notified,
                    ),
                )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving car: {e}")
        finally:
            conn.close()

    def get_recent_cars(self, limit=50):
        """Get recently found cars with all details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM found_cars 
            ORDER BY found_at DESC 
            LIMIT ?
        """,
            (limit,),
        )

        cars = []
        for row in cursor.fetchall():
            # Parse JSON fields
            try:
                all_images = json.loads(row[23]) if row[23] and row[23].strip() else []
            except (json.JSONDecodeError, TypeError):
                all_images = []
            try:
                specifications = (
                    json.loads(row[24]) if row[24] and row[24].strip() else {}
                )
            except (json.JSONDecodeError, TypeError):
                specifications = {}

            cars.append(
                {
                    "id": row[0],
                    "car_id": row[1],
                    "title": row[2],
                    "price": row[3],
                    "year": row[4],
                    "mileage": row[5],
                    "engine": row[6],
                    "url": row[7],
                    "image_url": row[8],
                    "city": row[9],
                    "brand": row[10],
                    "model": row[11],
                    "body_type": row[12],
                    "color": row[13],
                    "engine_details": row[14],
                    "transmission": row[15],
                    "drivetrain": row[16],
                    "is_new": row[17],
                    "seats": row[18],
                    "owners": row[19],
                    "condition_info": row[20],
                    "market": row[21],
                    "description": row[22],
                    "all_images": all_images,
                    "specifications": specifications,
                    "found_at": row[25],
                    "notified": row[26],
                }
            )

        conn.close()
        return cars

    def get_stats(self):
        """Get monitoring statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total cars found
        cursor.execute("SELECT COUNT(*) FROM found_cars")
        total_cars = cursor.fetchone()[0]

        # Cars found today
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM found_cars WHERE DATE(found_at) = ?", (today,)
        )
        today_cars = cursor.fetchone()[0]

        # Cars found this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM found_cars WHERE DATE(found_at) >= ?", (week_ago,)
        )
        week_cars = cursor.fetchone()[0]

        conn.close()

        return {
            "total_cars": total_cars,
            "today_cars": today_cars,
            "week_cars": week_cars,
        }

    def log_message(self, level, message):
        """Log a message to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO app_logs (level, message)
            VALUES (?, ?)
        """,
            (level, message),
        )

        conn.commit()
        conn.close()

        # Emit to connected clients
        socketio.emit(
            "new_log",
            {
                "level": level,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_setting(self, key: str, default_value: str = None):
        """Get a setting value from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else default_value

    def save_setting(self, key: str, value: str):
        """Save a setting value to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
        conn.close()

    def get_filter_settings(self):
        """Get current filter settings with defaults."""
        return {
            "price_from": self.get_setting("filter_price_from", "17000"),
            "price_to": self.get_setting("filter_price_to", "22000"),
            "year_from": self.get_setting("filter_year_from", ""),
            "year_to": self.get_setting("filter_year_to", "2015"),
            "engine_from": self.get_setting("filter_engine_from", "2300"),
            "engine_to": self.get_setting("filter_engine_to", ""),
            "mileage_to": self.get_setting("filter_mileage_to", "150000"),
            "condition": self.get_setting(
                "filter_condition", "used"
            ),  # new, used, or all
            "brand": self.get_setting("filter_brand", ""),
            "city": self.get_setting("filter_city", ""),
            "currency": self.get_setting("filter_currency", "azn"),
            "crashed": self.get_setting("filter_crashed", "1"),  # Include crashed cars
            "painted": self.get_setting("filter_painted", "1"),  # Include painted cars
            "for_spare_parts": self.get_setting(
                "filter_for_spare_parts", "0"
            ),  # Exclude spare parts
            "gear": self.get_setting("filter_gear", "3"),  # Manual transmission (3)
            "transmission": self.get_setting(
                "filter_transmission", "2"
            ),  # Front wheel drive (2)
        }

    def save_filter_settings(self, filters):
        """Save filter settings to database."""
        for key, value in filters.items():
            self.save_setting(f"filter_{key}", str(value))

    def build_turbo_az_url(self, filters=None):
        """Build Turbo.az URL from filter settings using the detailed query format."""
        if filters is None:
            filters = self.get_filter_settings()

        base_url = "https://turbo.az/autos"

        # Build query parameters using the exact format from the provided URL
        params = []

        # Sorting and basic filters
        params.append("q%5Bsort%5D=")  # Empty sort
        params.append(
            "q%5Bmake%5D%5B%5D="
        )  # Empty make (brand will be handled separately if needed)
        params.append("q%5Bmodel%5D%5B%5D=")  # Empty model

        # Condition (new/used)
        condition = filters.get("condition", "used")
        if condition == "used":
            params.append("q%5Bused%5D=1")
        elif condition == "new":
            params.append("q%5Bused%5D=0")
        else:  # all
            params.append("q%5Bused%5D=1")  # Default to used for 'all'

        params.append("q%5Bregion%5D%5B%5D=")  # Empty region

        # Price range
        if filters.get("price_from"):
            params.append(f"q%5Bprice_from%5D={filters['price_from']}")
        else:
            params.append("q%5Bprice_from%5D=")

        if filters.get("price_to"):
            params.append(f"q%5Bprice_to%5D={filters['price_to']}")
        else:
            params.append("q%5Bprice_to%5D=")

        # Currency
        currency = filters.get("currency", "azn")
        params.append(f"q%5Bcurrency%5D={currency}")

        # Loan and barter (default to 0)
        params.append("q%5Bloan%5D=0")
        params.append("q%5Bbarter%5D=0")

        # Category (21 seems to be a specific category from the URL)
        params.append("q%5Bcategory%5D%5B%5D=")
        params.append("q%5Bcategory%5D%5B%5D=21")

        # Year range
        if filters.get("year_from"):
            params.append(f"q%5Byear_from%5D={filters['year_from']}")
        else:
            params.append("q%5Byear_from%5D=")

        if filters.get("year_to"):
            params.append(f"q%5Byear_to%5D={filters['year_to']}")
        else:
            params.append("q%5Byear_to%5D=")

        # Color (empty for now)
        params.append("q%5Bcolor%5D%5B%5D=")

        # Fuel type (empty for now)
        params.append("q%5Bfuel_type%5D%5B%5D=")

        # Gear (transmission type)
        params.append("q%5Bgear%5D%5B%5D=")
        gear = filters.get("gear", "3")
        params.append(f"q%5Bgear%5D%5B%5D={gear}")

        # Transmission (drivetrain)
        params.append("q%5Btransmission%5D%5B%5D=")
        transmission = filters.get("transmission", "2")
        params.append(f"q%5Btransmission%5D%5B%5D={transmission}")

        # Engine volume (in cc, so 2300 = 2.3L)
        if filters.get("engine_from"):
            # Convert from liters to cc if needed
            engine_from = filters["engine_from"]
            if "." in str(engine_from):
                engine_from = str(int(float(engine_from) * 1000))
            params.append(f"q%5Bengine_volume_from%5D={engine_from}")
        else:
            params.append("q%5Bengine_volume_from%5D=")

        if filters.get("engine_to"):
            engine_to = filters["engine_to"]
            if "." in str(engine_to):
                engine_to = str(int(float(engine_to) * 1000))
            params.append(f"q%5Bengine_volume_to%5D={engine_to}")
        else:
            params.append("q%5Bengine_volume_to%5D=")

        # Power (empty for now)
        params.append("q%5Bpower_from%5D=")
        params.append("q%5Bpower_to%5D=")

        # Mileage
        params.append("q%5Bmileage_from%5D=")
        if filters.get("mileage_to"):
            params.append(f"q%5Bmileage_to%5D={filters['mileage_to']}")
        else:
            params.append("q%5Bmileage_to%5D=")

        # Shop filters
        params.append("q%5Bonly_shops%5D=")
        params.append("q%5Bprior_owners_count%5D%5B%5D=")
        params.append("q%5Bseats_count%5D%5B%5D=")
        params.append("q%5Bmarket%5D%5B%5D=")

        # Condition filters (crashed, painted, spare parts)
        crashed = filters.get("crashed", "1")
        params.append(f"q%5Bcrashed%5D={crashed}")

        painted = filters.get("painted", "1")
        params.append(f"q%5Bpainted%5D={painted}")

        for_spare_parts = filters.get("for_spare_parts", "0")
        params.append(f"q%5Bfor_spare_parts%5D={for_spare_parts}")

        # Availability status
        params.append("q%5Bavailability_status%5D=")

        return f"{base_url}?{'&'.join(params)}"


# Initialize database
db = DatabaseManager()


class AppCarMonitor(CarMonitor):
    """Car monitor with app integration."""

    def __init__(self):
        super().__init__()

    def update_url_from_filters(self):
        """Update the monitoring URL from current filter settings."""
        filters = db.get_filter_settings()
        new_url = db.build_turbo_az_url(filters)
        self.set_url(new_url)

        # Update the config as well for backwards compatibility
        import config

        config.TURBO_AZ_URL = new_url

        logger.info(f"Updated scraper URL: {new_url}")

    async def check_for_new_cars(self) -> int:
        """Check for new cars using current filter settings and save to database."""
        db.log_message("INFO", "Checking for new cars...")

        try:
            # Get current cars from website using current filter settings
            filters = db.get_filter_settings()
            current_url = db.build_turbo_az_url(filters)

            # Make sure monitor knows about the current URL
            self.set_url(current_url)

            # Get cars using the scraper directly with our URL
            current_cars = self.scraper.get_new_cars(current_url)

            if not current_cars:
                db.log_message("WARNING", "No cars found on the website")
                return 0

            # Filter out cars we've already seen
            new_cars = self.filter_new_cars(current_cars)

            if new_cars:
                db.log_message("INFO", f"Found {len(new_cars)} new cars!")

                # Save cars to database
                for car in new_cars:
                    db.save_car(car, notified=False)

                    # Emit real-time update with enhanced data
                    socketio.emit(
                        "new_car",
                        {
                            "car_id": car.car_id,
                            "title": car.title,
                            "price": car.price,
                            "year": car.year,
                            "mileage": car.mileage,
                            "engine": car.engine,
                            "url": car.url,
                            "image_url": car.image_url,
                            "city": car.city,
                            "brand": car.brand,
                            "color": car.color,
                            "transmission": car.transmission,
                            "found_at": datetime.now().isoformat(),
                        },
                    )

                # Send telegram notifications if configured
                if BOT_TOKEN and CHAT_ID:
                    try:
                        successful = await self.bot.send_multiple_cars(new_cars)
                        db.log_message(
                            "INFO",
                            f"Successfully sent {successful}/{len(new_cars)} Telegram notifications",
                        )

                        # Mark as notified in database
                        conn = sqlite3.connect(db.db_path)
                        cur = conn.cursor()
                        try:
                            cur.executemany(
                                "UPDATE found_cars SET notified=1 WHERE car_id=?",
                                [(car.car_id,) for car in new_cars],
                            )
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Failed to mark cars as notified: {e}")
                        finally:
                            conn.close()

                    except Exception as e:
                        db.log_message(
                            "ERROR", f"Failed to send Telegram notifications: {str(e)}"
                        )
                else:
                    db.log_message(
                        "INFO", "Telegram not configured - cars saved to database only"
                    )

                return len(new_cars)
            else:
                db.log_message("INFO", "No new cars found")
                return 0

        except Exception as e:
            error_msg = f"Error checking for new cars: {str(e)}"
            db.log_message("ERROR", error_msg)
            logger.error(error_msg)
            return 0


def run_monitoring_loop():
    """Run the monitoring loop in a separate thread."""
    global is_monitoring

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def monitor_loop():
        global is_monitoring, monitor

        while is_monitoring:
            try:
                if monitor:
                    await monitor.check_for_new_cars()

                # Wait for next check
                await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)

            except Exception as e:
                db.log_message("ERROR", f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    loop.run_until_complete(monitor_loop())


@app.route("/")
def dashboard():
    """Main dashboard page."""
    stats = db.get_stats()
    recent_cars = db.get_recent_cars(10)
    filters = db.get_filter_settings()
    current_url = db.build_turbo_az_url(filters)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_cars=recent_cars,
        is_monitoring=is_monitoring,
        bot_configured=bool(BOT_TOKEN and CHAT_ID),
        filters=filters,
        current_url=current_url,
    )


@app.route("/cars")
def cars_page():
    """Cars listing page."""
    page = request.args.get("page", 1, type=int)
    per_page = 20

    cars = db.get_recent_cars(page * per_page)
    start_idx = (page - 1) * per_page
    page_cars = cars[start_idx : start_idx + per_page]

    return render_template(
        "cars.html", cars=page_cars, page=page, has_next=len(cars) > page * per_page
    )


@app.route("/car/<car_id>")
def car_detail(car_id):
    """Individual car detail page."""
    cars = db.get_recent_cars(1000)  # Get more cars to find the specific one
    car = next((c for c in cars if c["car_id"] == car_id), None)

    if not car:
        flash("Car not found", "error")
        return redirect(url_for("cars_page"))

    return render_template("car_detail.html", car=car)


@app.route("/settings")
def settings_page():
    """Settings page."""
    filters = db.get_filter_settings()
    return render_template(
        "settings.html",
        check_interval=CHECK_INTERVAL_MINUTES,
        bot_token_configured=bool(BOT_TOKEN),
        chat_id_configured=bool(CHAT_ID),
        filters=filters,
    )


@app.route("/api/start_monitoring", methods=["POST"])
def start_monitoring():
    """Start the monitoring process."""
    global monitor, monitoring_thread, is_monitoring

    if is_monitoring:
        return jsonify({"success": False, "message": "Monitoring is already running"})

    try:
        monitor = AppCarMonitor()
        is_monitoring = True

        # Start monitoring in a separate thread
        monitoring_thread = threading.Thread(target=run_monitoring_loop, daemon=True)
        monitoring_thread.start()

        db.log_message("INFO", "Monitoring started")
        return jsonify({"success": True, "message": "Monitoring started successfully"})

    except Exception as e:
        error_msg = f"Failed to start monitoring: {str(e)}"
        db.log_message("ERROR", error_msg)
        return jsonify({"success": False, "message": error_msg})


@app.route("/api/stop_monitoring", methods=["POST"])
def stop_monitoring():
    """Stop the monitoring process."""
    global is_monitoring

    if not is_monitoring:
        return jsonify({"success": False, "message": "Monitoring is not running"})

    is_monitoring = False
    db.log_message("INFO", "Monitoring stopped")

    return jsonify({"success": True, "message": "Monitoring stopped successfully"})


@app.route("/api/save_filters", methods=["POST"])
def save_filters():
    """Save filter settings."""
    try:
        data = request.get_json()

        # Validate and clean the filter data
        filters = {}

        # Price range
        if data.get("price_from"):
            filters["price_from"] = str(int(data["price_from"]))
        if data.get("price_to"):
            filters["price_to"] = str(int(data["price_to"]))

        # Year range
        if data.get("year_from"):
            filters["year_from"] = str(int(data["year_from"]))
        if data.get("year_to"):
            filters["year_to"] = str(int(data["year_to"]))

        # Engine size (convert to cc for URL)
        if data.get("engine_from"):
            engine_val = float(data["engine_from"])
            # If less than 100, assume it's in liters and convert to cc
            if engine_val < 100:
                engine_val = int(engine_val * 1000)
            filters["engine_from"] = str(int(engine_val))
        if data.get("engine_to"):
            engine_val = float(data["engine_to"])
            if engine_val < 100:
                engine_val = int(engine_val * 1000)
            filters["engine_to"] = str(int(engine_val))

        # Mileage
        if data.get("mileage_to"):
            filters["mileage_to"] = str(int(data["mileage_to"]))

        # Condition
        condition = data.get("condition", "used")
        if condition in ["new", "used", "all"]:
            filters["condition"] = condition

        # Currency
        currency = data.get("currency", "azn")
        if currency in ["azn", "usd", "eur"]:
            filters["currency"] = currency

        # Crashed cars filter
        crashed = data.get("crashed", "1")
        filters["crashed"] = "1" if crashed in ["1", "true", True] else "0"

        # Painted cars filter
        painted = data.get("painted", "1")
        filters["painted"] = "1" if painted in ["1", "true", True] else "0"

        # For spare parts filter
        for_spare_parts = data.get("for_spare_parts", "0")
        filters["for_spare_parts"] = (
            "1" if for_spare_parts in ["1", "true", True] else "0"
        )

        # Gear type (transmission)
        gear = data.get("gear", "3")
        if gear in ["1", "2", "3"]:  # 1=auto, 2=manual, 3=both or default
            filters["gear"] = gear

        # Transmission (drivetrain)
        transmission = data.get("transmission", "2")
        if transmission in ["1", "2", "3"]:  # 1=rear, 2=front, 3=4wd
            filters["transmission"] = transmission

        # Brand and city (for future filtering)
        if data.get("brand"):
            filters["brand"] = str(data["brand"]).strip()
        if data.get("city"):
            filters["city"] = str(data["city"]).strip()

        # Save to database
        db.save_filter_settings(filters)

        # Generate new URL
        new_url = db.build_turbo_az_url(filters)

        # Update the monitor if it's running
        global monitor
        if monitor:
            monitor.update_url_from_filters()

        db.log_message("INFO", f"Filter settings updated. New URL: {new_url}")

        return jsonify(
            {
                "success": True,
                "message": "Filter settings saved successfully",
                "url": new_url,
            }
        )

    except Exception as e:
        error_msg = f"Failed to save filter settings: {str(e)}"
        db.log_message("ERROR", error_msg)
        return jsonify({"success": False, "message": error_msg})


@app.route("/api/test_scraper")
def test_scraper():
    """Test the scraper functionality."""
    try:
        from car_scraper import TurboAzScraper

        scraper = TurboAzScraper()
        # Use current filter settings for testing
        filters = db.get_filter_settings()
        current_url = db.build_turbo_az_url(filters)
        cars = scraper.get_new_cars(current_url)

        return jsonify(
            {
                "success": True,
                "message": f"Found {len(cars)} cars with detailed information",
                "sample_cars": [
                    {
                        "title": car.title,
                        "price": car.price,
                        "year": car.year,
                        "city": car.city,
                        "brand": car.brand,
                        "color": car.color,
                        "url": car.url,
                    }
                    for car in cars[:3]  # First 3 cars
                ],
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Scraper test failed: {str(e)}"})


@app.route("/api/test_telegram")
def test_telegram():
    """Test Telegram bot connection."""
    if not BOT_TOKEN or not CHAT_ID:
        return jsonify(
            {"success": False, "message": "Telegram credentials not configured"}
        )

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def test_bot():
            from bot import TurboAzBot

            bot = TurboAzBot()
            return await bot.test_connection()

        success = loop.run_until_complete(test_bot())

        if success:
            return jsonify(
                {"success": True, "message": "Telegram bot connection successful"}
            )
        else:
            return jsonify(
                {"success": False, "message": "Telegram bot connection failed"}
            )

    except Exception as e:
        return jsonify({"success": False, "message": f"Telegram test failed: {str(e)}"})
    finally:
        try:
            loop.close()
        except Exception:
            pass


@app.route("/api/status")
def get_status():
    """Get current monitoring status."""
    return jsonify({"is_monitoring": is_monitoring})


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    emit("connected", {"message": "Connected to Turbo.az Monitor"})


if __name__ == "__main__":
    print("🚗 Starting Turbo.az Car Monitor Web App")
    print("🌐 Open your browser to http://localhost:5000")

    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
