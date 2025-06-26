import json
import logging
import os
import random
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config import MAX_RETRIES, REQUEST_TIMEOUT

try:
    from fake_useragent import UserAgent

    FAKE_UA_AVAILABLE = True
except ImportError:
    FAKE_UA_AVAILABLE = False
    logging.warning("fake-useragent not available, using static user agents")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CarListing:
    def __init__(
        self,
        car_id: str,
        title: str,
        price: str,
        year: str,
        mileage: str,
        engine: str,
        url: str,
        image_url: str = None,
    ):
        self.car_id = car_id
        self.title = title
        self.price = price
        self.year = year
        self.mileage = mileage
        self.engine = engine
        self.url = url
        self.image_url = image_url

        # Additional detailed information
        self.city = None
        self.brand = None
        self.model = None
        self.body_type = None
        self.color = None
        self.engine_details = None
        self.transmission = None
        self.drivetrain = None
        self.is_new = None
        self.seats = None
        self.owners = None
        self.condition = None
        self.market = None
        self.description = None
        self.all_images = []
        self.specifications = {}

    def __str__(self):
        details = f"{self.title}\n💰 {self.price}\n📅 {self.year}\n🔄 {self.mileage}\n⚙️ {self.engine}"
        if self.city:
            details += f"\n📍 {self.city}"
        if self.color:
            details += f"\n🎨 {self.color}"
        if self.transmission:
            details += f"\n🔧 {self.transmission}"
        details += f"\n🔗 {self.url}"
        return details


class AdvancedUserAgentManager:
    """Advanced user agent management with multiple strategies."""

    def __init__(self):
        self.ua_generator = None
        if FAKE_UA_AVAILABLE:
            try:
                self.ua_generator = UserAgent()
                logger.info("✅ Advanced user agent generator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize UserAgent: {e}")
                self.ua_generator = None

        # Fallback static user agents (high-quality, recent versions)
        self.static_desktop_agents = [
            # Chrome (Windows, Mac, Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Firefox (Windows, Mac, Linux)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Safari (Mac)
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            # Edge (Windows)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ]

        # Mobile user agents for diversity
        self.static_mobile_agents = [
            # iPhone Safari
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            # Android Chrome
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            # iPad Safari
            "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        ]

        self.current_ua = None
        self.request_count = 0

    def get_random_desktop_ua(self) -> str:
        """Get a random desktop user agent."""
        if self.ua_generator:
            try:
                # Try different browsers with fake-useragent
                browser_choice = random.choice(["chrome", "firefox", "safari", "edge"])
                if browser_choice == "chrome":
                    return self.ua_generator.chrome
                elif browser_choice == "firefox":
                    return self.ua_generator.firefox
                elif browser_choice == "safari":
                    return self.ua_generator.safari
                else:
                    return self.ua_generator.edge
            except Exception:
                pass

        return random.choice(self.static_desktop_agents)

    def get_random_mobile_ua(self) -> str:
        """Get a random mobile user agent."""
        return random.choice(self.static_mobile_agents)

    def get_user_agent(self, force_mobile: bool = False) -> str:
        """Get an appropriate user agent with intelligent selection."""
        self.request_count += 1

        # Occasionally use mobile (10% chance) unless forced
        use_mobile = force_mobile or random.random() < 0.1

        if use_mobile:
            ua = self.get_random_mobile_ua()
            logger.debug(f"Using mobile UA: {ua[:50]}...")
        else:
            ua = self.get_random_desktop_ua()
            logger.debug(f"Using desktop UA: {ua[:50]}...")

        self.current_ua = ua
        return ua

    def get_headers_for_ua(self, user_agent: str) -> Dict[str, str]:
        """Generate realistic headers based on the user agent."""
        is_mobile = (
            "Mobile" in user_agent or "iPhone" in user_agent or "Android" in user_agent
        )
        is_firefox = "Firefox" in user_agent
        is_safari = "Safari" in user_agent and "Chrome" not in user_agent
        is_chrome = "Chrome" in user_agent

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,az;q=0.8,tr;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Browser-specific headers
        if is_chrome:
            headers.update(
                {
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?1" if is_mobile else "?0",
                    "sec-ch-ua-platform": (
                        '"Android"' if "Android" in user_agent else '"Windows"'
                    ),
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                }
            )

        if is_firefox:
            headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            )

        if is_mobile:
            headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
            )
            headers["Viewport-Width"] = str(random.randint(360, 414))

        # Add some randomization
        if random.random() < 0.3:
            headers["Cache-Control"] = "max-age=0"

        return headers


class TurboAzScraper:
    def __init__(self):
        self.session = requests.Session()
        self.cache_file = "car_details_cache.json"
        self.cache = self.load_cache()
        self.request_count = 0
        self.last_request_time = 0

        # Initialize advanced user agent manager
        self.ua_manager = AdvancedUserAgentManager()

        # Update with initial headers
        self.update_headers()

        # Rate limiting settings
        self.min_delay_between_requests = 2.0  # Minimum 2 seconds between requests
        self.max_delay_between_requests = 5.0  # Maximum 5 seconds
        self.max_requests_per_minute = 15  # Limit to 15 requests per minute
        self.request_timestamps = []

    def load_cache(self) -> Dict:
        """Load cached car details to avoid re-scraping."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    logger.info(f"Loaded {len(cache)} cached car details")
                    return cache
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}

    def save_cache(self):
        """Save car details cache to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")

    def update_headers(self):
        """Update session headers with advanced user agent rotation."""
        user_agent = self.ua_manager.get_user_agent()
        headers = self.ua_manager.get_headers_for_ua(user_agent)

        self.session.headers.update(headers)
        logger.debug(f"Updated headers with UA: {user_agent[:50]}...")

    def enforce_rate_limit(self):
        """Enforce rate limiting to avoid being banned."""
        current_time = time.time()

        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps if current_time - ts < 60
        ]

        # Check if we're at the rate limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0]) + 1
            logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
            self.request_timestamps = []

        # Enforce minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            sleep_time = self.min_delay_between_requests - time_since_last
            time.sleep(sleep_time)

        # Add random delay to appear more human-like
        random_delay = random.uniform(0.5, 2.0)
        time.sleep(random_delay)

        # Record this request
        self.request_timestamps.append(time.time())
        self.last_request_time = time.time()
        self.request_count += 1

        # Rotate user agent more frequently for better stealth
        if self.request_count % random.randint(3, 7) == 0:
            self.update_headers()
            logger.debug(f"Rotated user agent after {self.request_count} requests")

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse the HTML content from the given URL with anti-detection measures."""
        self.enforce_rate_limit()

        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Requesting: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)

                # Handle rate limiting responses
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    # Change user agent after being rate limited
                    self.update_headers()
                    continue

                # Handle temporary server errors
                elif response.status_code in [502, 503, 504]:
                    wait_time = (2**attempt) * random.uniform(1, 2)
                    logger.warning(
                        f"Server error {response.status_code}, waiting {wait_time:.1f}s"
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                # Ensure proper text decoding by using response.text instead of response.content
                # This handles encoding detection and decompression automatically
                soup = BeautifulSoup(response.text, "html.parser")

                # Verify we got proper HTML content
                logger.debug(f"Content length: {len(response.text)} chars")
                logger.debug(f"Content preview: {response.text[:200]}...")

                # Check for basic HTML indicators
                has_html = soup.find("html") is not None
                has_body = soup.find("body") is not None
                has_turbo = "turbo.az" in response.text.lower()
                has_products = "products-i" in response.text

                logger.debug(
                    f"HTML validation: html={has_html}, body={has_body}, turbo={has_turbo}, products={has_products}"
                )

                if has_html or has_body or has_turbo or len(response.text) > 10000:
                    logger.debug(f"Successfully parsed HTML content")
                    return soup
                else:
                    logger.warning(f"Content validation failed")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt)

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                else:
                    logger.error(
                        f"Failed to fetch page after {MAX_RETRIES} attempts: {url}"
                    )
                    return None

            except Exception as e:
                logger.warning(f"Parsing error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt)

        return None

    def extract_car_listings(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract car listings from the parsed HTML."""
        cars = []

        # Find all car listing containers
        car_items = soup.find_all("div", class_="products-i")

        for item in car_items:
            try:
                # Extract car ID from the data attributes or href
                link_elem = item.find("a", class_="products-i__link")
                if not link_elem:
                    continue

                car_url = link_elem.get("href")
                if car_url and not car_url.startswith("http"):
                    car_url = "https://turbo.az" + car_url

                # Extract car ID from URL
                car_id_match = re.search(r"/(\d+)", car_url)
                if not car_id_match:
                    continue
                car_id = car_id_match.group(1)

                # Extract basic info from listing page
                title_elem = item.find("div", class_="products-i__name")
                title = title_elem.get_text(strip=True) if title_elem else "N/A"

                price_elem = item.find("div", class_="products-i__price")
                price = price_elem.get_text(strip=True) if price_elem else "N/A"

                # Extract additional details
                details = item.find_all("div", class_="products-i__attributes-i")
                year = "N/A"
                mileage = "N/A"
                engine = "N/A"

                for detail in details:
                    text = detail.get_text(strip=True)
                    if re.match(r"\d{4}", text):  # Year
                        year = text
                    elif "km" in text.lower():  # Mileage
                        mileage = text
                    elif any(
                        unit in text.lower() for unit in ["l", "cc", "cm³"]
                    ):  # Engine
                        engine = text

                # Extract image URL
                img_elem = item.find("img")
                image_url = img_elem.get("src") if img_elem else None
                if image_url and not image_url.startswith("http"):
                    image_url = "https://turbo.az" + image_url

                car = CarListing(
                    car_id, title, price, year, mileage, engine, car_url, image_url
                )
                cars.append(car)

            except Exception as e:
                logger.warning(f"Error parsing car listing: {e}")
                continue

        return cars

    def extract_detailed_info(self, car: CarListing) -> CarListing:
        """Extract detailed information from individual car page with caching."""

        # Check cache first
        if car.car_id in self.cache:
            cached_data = self.cache[car.car_id]
            # Apply cached data to car object
            for key, value in cached_data.items():
                if hasattr(car, key):
                    setattr(car, key, value)
            logger.debug(f"Used cached data for car {car.car_id}")
            return car

        try:
            logger.info(f"Fetching detailed info for car {car.car_id}")
            soup = self.get_page_content(car.url)

            if not soup:
                return car

            # Extract specifications from the product-properties section
            specifications = {}

            # Find the product-properties div
            product_props = soup.find("div", class_="product-properties")
            if product_props:
                # Get all the property items within product-properties
                prop_items = product_props.find_all(
                    "div", class_="product-properties-i"
                )

                for item in prop_items:
                    # Each item should have a label and value
                    label_elem = item.find("label")
                    value_elem = item.find("div", class_="product-properties-i-value")

                    if label_elem and value_elem:
                        key = label_elem.get_text(strip=True)
                        value = value_elem.get_text(strip=True)
                        specifications[key] = value

                # If the above doesn't work, try extracting from the raw text
                if not specifications:
                    prop_text = product_props.get_text()
                    # Split by common Azerbaijani field names
                    field_patterns = [
                        "Şəhər",
                        "Marka",
                        "Model",
                        "Buraxılış ili",
                        "Ban növü",
                        "Rəng",
                        "Mühərrik",
                        "Yürüş",
                        "Sürətlər qutusu",
                        "Ötürücü",
                        "Yeni",
                        "Yerlәrin sayı",
                        "Sahiblәr",
                        "Vәziyyәti",
                        "Hansi bazar üçün yığılıb",
                    ]

                    # Try to extract values using regex patterns
                    import re

                    for i, field in enumerate(field_patterns):
                        if i < len(field_patterns) - 1:
                            next_field = field_patterns[i + 1]
                            pattern = f"{field}(.*?){next_field}"
                        else:
                            pattern = f"{field}(.*?)$"

                        match = re.search(pattern, prop_text, re.DOTALL)
                        if match:
                            value = match.group(1).strip()
                            if value:
                                specifications[field] = value

            # Also try finding specifications in a table format (backup method)
            if not specifications:
                spec_rows = soup.find_all("tr")
                for row in spec_rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            specifications[key] = value

            # Map Azerbaijani field names to our attributes
            field_mappings = {
                "Şəhər": "city",
                "Marka": "brand",
                "Model": "model",
                "Buraxılış ili": "year",
                "Ban növü": "body_type",
                "Rəng": "color",
                "Mühərrik": "engine_details",
                "Yürüş": "mileage",
                "Sürətlər qutusu": "transmission",
                "Ötürücü": "drivetrain",
                "Yeni": "is_new",
                "Yerlәrin sayı": "seats",
                "Sahiblәr": "owners",
                "Vәziyyәti": "condition",
                "Hansi bazar üçün yığılıb": "market",
            }

            # Apply mappings
            for az_field, eng_field in field_mappings.items():
                if az_field in specifications:
                    setattr(car, eng_field, specifications[az_field])

            car.specifications = specifications

            # Extract description - try multiple selectors
            description_selectors = [
                "div.product-description",
                "div.product-text",
                "div.description",
                "div.auto-description",
            ]

            for selector in description_selectors:
                description_elem = soup.select_one(selector)
                if description_elem:
                    car.description = description_elem.get_text(strip=True)
                    break

            # Extract all images
            car.all_images = []

            # Try different image selectors
            image_selectors = [
                "img.slider-img",
                "img.product-photo",
                "div.product-photos img",
                "div.slider img",
                'img[src*="cars/"]',
                'img[src*="autos/"]',
            ]

            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    img_src = (
                        img.get("src") or img.get("data-src") or img.get("data-lazy")
                    )
                    if img_src:
                        if not img_src.startswith("http"):
                            img_src = "https://turbo.az" + img_src
                        if img_src not in car.all_images:
                            car.all_images.append(img_src)

            # Cache the extracted data
            cache_data = {}
            for field in [
                "city",
                "brand",
                "model",
                "body_type",
                "color",
                "engine_details",
                "transmission",
                "drivetrain",
                "is_new",
                "seats",
                "owners",
                "condition",
                "market",
                "description",
                "all_images",
                "specifications",
            ]:
                if hasattr(car, field):
                    cache_data[field] = getattr(car, field)

            self.cache[car.car_id] = cache_data

            # If we found specifications, log them for debugging
            if specifications:
                logger.info(
                    f"Extracted {len(specifications)} specifications for car {car.car_id}"
                )
                for key, value in list(specifications.items())[:3]:  # Log first 3
                    logger.info(f"  {key}: {value}")
            else:
                logger.warning(f"No specifications found for car {car.car_id}")

            logger.info(f"Successfully extracted detailed info for car {car.car_id}")
            return car

        except Exception as e:
            logger.error(f"Error extracting detailed info for car {car.car_id}: {e}")
            return car

    def get_new_cars(self, url: str = None) -> List[CarListing]:
        """Fetch all current car listings from Turbo.az with detailed information and rate limiting."""
        if url is None:
            # Fallback URL if none provided
            url = "https://turbo.az/autos?page=1&price_from=17000&price_to=22000&used=1&year_to=2015&engine_from=2.3&kilometers_to=150000"

        logger.info("Fetching car listings from Turbo.az...")

        soup = self.get_page_content(url)
        if not soup:
            return []

        cars = self.extract_car_listings(soup)
        logger.info(
            f"Found {len(cars)} car listings, extracting detailed information..."
        )

        # Extract detailed information for each car with intelligent throttling
        detailed_cars = []
        total_cars = len(cars)

        for i, car in enumerate(cars):
            logger.info(f"Processing car {i+1}/{total_cars}: {car.title}")

            # Check if we should throttle more aggressively
            if i > 0 and i % 5 == 0:
                pause_time = random.uniform(10, 20)
                logger.info(f"Taking a {pause_time:.1f}s break after processing 5 cars")
                time.sleep(pause_time)

            detailed_car = self.extract_detailed_info(car)
            detailed_cars.append(detailed_car)

        # Save cache after processing all cars
        self.save_cache()

        logger.info(
            f"Completed processing {len(detailed_cars)} cars with detailed information"
        )
        logger.info(f"Total requests made: {self.request_count}")
        logger.info(f"User agent rotations: {self.ua_manager.request_count}")
        return detailed_cars
