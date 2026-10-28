#!/usr/bin/env python3
"""
Collect property listing data from Aqar.fm.

This script fetches a property listing from Aqar.fm and extracts key fields
for valuation analysis. Extracted data is saved as JSON with source metadata.

Usage:
    python aqar_collector.py <URL>              # Collect from URL
    python aqar_collector.py <URL> --output ./data  # Custom output dir
    python aqar_collector.py --help             # Show help

Example:
    python aqar_collector.py "https://aqar.fm/property/12345678"

Requirements:
    - requests
    - All else is standard library
"""

import argparse
import json
import logging
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AqarCollector:
    """Collect property data from Aqar.fm listings."""

    AQAR_DOMAIN = "aqar.fm"
    TIMEOUT = 15

    def __init__(self, url: str):
        """
        Initialize Aqar collector.

        Args:
            url: Aqar.fm property listing URL
        """
        self.url = url
        self.session = requests.Session()
        self.session.timeout = self.TIMEOUT
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
            }
        )
        self.content = None
        self.extracted_data = {}

    def validate_url(self) -> bool:
        """
        Validate that URL is from aqar.fm.

        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(self.url)
            if self.AQAR_DOMAIN not in parsed.netloc:
                logger.error(f"URL must be from {self.AQAR_DOMAIN}")
                return False
            return True
        except Exception as e:
            logger.error(f"Invalid URL: {e}")
            return False

    def check_robots_txt(self) -> bool:
        """
        Check if aqar.fm allows scraping in robots.txt.

        Returns:
            True if allowed, False if disallowed
        """
        try:
            rp = RobotFileParser()
            rp.set_url("https://aqar.fm/robots.txt")
            rp.read()
            can_fetch = rp.can_fetch("*", self.url)
            if not can_fetch:
                logger.warning("aqar.fm robots.txt disallows scraping this URL")
            return can_fetch
        except Exception as e:
            logger.debug(f"Could not check robots.txt: {e}")
            # Assume allowed if check fails
            return True

    def fetch_content(self) -> bool:
        """
        Fetch HTML content from URL.

        Returns:
            True on success, False on error
        """
        try:
            response = self.session.get(self.url, allow_redirects=True)
            response.raise_for_status()
            self.content = response.text
            logger.info(f"Fetched {len(self.content)} bytes")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL: {e}")
            return False

    def extract_price(self) -> Optional[Dict[str, Any]]:
        """
        Extract price information from HTML.

        Returns:
            Dictionary with price_sar and price_per_sqm or None
        """
        if not self.content:
            return None

        try:
            # Look for price patterns: "1,200,000 ر.س" or similar
            price_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*(?:ر\.س|SAR|ر س)',
                r'Price["\']?\s*:\s*(\d{1,3}(?:,\d{3})*)',
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE)
                if matches:
                    # Take first match and clean commas
                    price_str = matches[0].replace(",", "")
                    try:
                        price_sar = int(price_str)
                        return {"price_sar": price_sar}
                    except ValueError:
                        continue

            logger.debug("Could not extract price")
            return None
        except Exception as e:
            logger.debug(f"Error extracting price: {e}")
            return None

    def extract_area(self) -> Optional[Dict[str, Any]]:
        """
        Extract property area in sqm.

        Returns:
            Dictionary with area_sqm or None
        """
        if not self.content:
            return None

        try:
            # Look for area patterns: "800 sqm" or "800 م²"
            area_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:sqm|م²|متر مربع)',
                r'Area["\']?\s*:\s*(\d+(?:\.\d+)?)',
                r'(?:Size|space)["\']?\s*:\s*(\d+(?:\.\d+)?)',
            ]

            for pattern in area_patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE)
                if matches:
                    try:
                        area_sqm = float(matches[0])
                        return {"area_sqm": area_sqm}
                    except ValueError:
                        continue

            logger.debug("Could not extract area")
            return None
        except Exception as e:
            logger.debug(f"Error extracting area: {e}")
            return None

    def extract_location(self) -> Optional[Dict[str, Any]]:
        """
        Extract location information.

        Returns:
            Dictionary with location data or None
        """
        if not self.content:
            return None

        try:
            # Look for city/district patterns
            location_data = {}

            # Saudi cities
            cities = [
                "Riyadh",
                "الرياض",
                "Jeddah",
                "جدة",
                "Dammam",
                "الدمام",
                "Khobar",
                "الخبر",
                "Mecca",
                "مكة",
                "Medina",
                "المدينة",
            ]

            for city in cities:
                if city in self.content:
                    location_data["city"] = city
                    break

            # Common districts/regions
            district_patterns = r'(?:District|حي|منطقة)["\']?\s*[:=]?\s*"?([^"<,]+)'
            matches = re.findall(district_patterns, self.content, re.IGNORECASE)
            if matches:
                location_data["district"] = matches[0].strip()

            return location_data if location_data else None
        except Exception as e:
            logger.debug(f"Error extracting location: {e}")
            return None

    def extract_property_type(self) -> Optional[str]:
        """
        Extract property type (villa, apartment, etc.).

        Returns:
            Property type string or None
        """
        if not self.content:
            return None

        try:
            types = {
                "villa": ["villa", "فيلا"],
                "apartment": ["apartment", "flat", "شقة"],
                "townhouse": ["townhouse", "تاون هاوس"],
                "commercial": ["commercial", "تجاري", "shop", "محل"],
                "land": ["land", "أرض", "plot"],
                "studio": ["studio", "استوديو"],
            }

            for ptype, keywords in types.items():
                for kw in keywords:
                    if kw.lower() in self.content.lower():
                        return ptype

            logger.debug("Could not determine property type")
            return None
        except Exception as e:
            logger.debug(f"Error extracting property type: {e}")
            return None

    def extract_bedrooms(self) -> Optional[int]:
        """
        Extract number of bedrooms.

        Returns:
            Number of bedrooms or None
        """
        if not self.content:
            return None

        try:
            # Look for bedroom patterns: "5 BR" or "5 غرف نوم"
            patterns = [
                r'(\d+)\s*(?:BR|bedrooms?|غرف نوم|غرفة نوم)',
                r'bedrooms?\s*[:=]?\s*(\d+)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE)
                if matches:
                    try:
                        return int(matches[0])
                    except ValueError:
                        continue

            return None
        except Exception as e:
            logger.debug(f"Error extracting bedrooms: {e}")
            return None

    def extract_bathrooms(self) -> Optional[int]:
        """
        Extract number of bathrooms.

        Returns:
            Number of bathrooms or None
        """
        if not self.content:
            return None

        try:
            patterns = [
                r'(\d+)\s*(?:BA|bathrooms?|حمام)',
                r'bathrooms?\s*[:=]?\s*(\d+)',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE)
                if matches:
                    try:
                        return int(matches[0])
                    except ValueError:
                        continue

            return None
        except Exception as e:
            logger.debug(f"Error extracting bathrooms: {e}")
            return None

    def extract_tenure(self) -> Optional[str]:
        """
        Extract property tenure (freehold, leasehold, etc.).

        Returns:
            Tenure type or None
        """
        if not self.content:
            return None

        try:
            tenure_keywords = {
                "freehold": ["freehold", "ملك", "Freehold"],
                "leasehold": ["leasehold", "إيجار طويل الأجل"],
                "usufruct": ["usufruct", "منفعة"],
            }

            for tenure, keywords in tenure_keywords.items():
                for kw in keywords:
                    if kw.lower() in self.content.lower():
                        return tenure

            return None
        except Exception as e:
            logger.debug(f"Error extracting tenure: {e}")
            return None

    def extract_description(self) -> Optional[str]:
        """
        Extract property description.

        Returns:
            Description text or None
        """
        if not self.content:
            return None

        try:
            # Try to find description section
            # Look for text between common description markers
            desc_patterns = [
                r'description["\']?\s*[:=]?\s*["\']?([^"<]{50,}?)["\'<]',
                r'about["\']?\s*[:=]?\s*["\']?([^"<]{50,}?)["\'<]',
                r'<p[^>]*>([^<]{50,}?)</p>',
            ]

            for pattern in desc_patterns:
                matches = re.findall(pattern, self.content, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Clean and return first match
                    desc = matches[0].strip()
                    # Remove HTML tags and extra whitespace
                    desc = re.sub(r'<[^>]+>', '', desc)
                    desc = re.sub(r'\s+', ' ', desc)
                    if len(desc) > 30:
                        return desc[:500]  # Limit to 500 chars

            return None
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return None

    def collect(self) -> bool:
        """
        Execute full extraction pipeline.

        Returns:
            True on success, False on error
        """
        logger.info(f"Starting extraction from: {self.url}")

        # Validate
        if not self.validate_url():
            return False

        # Check robots.txt
        if not self.check_robots_txt():
            logger.error("Scraping disallowed by robots.txt")
            return False

        # Fetch content
        if not self.fetch_content():
            return False

        # Extract fields
        logger.info("Extracting property data...")

        price_data = self.extract_price()
        if price_data:
            self.extracted_data.update(price_data)

        area_data = self.extract_area()
        if area_data:
            self.extracted_data.update(area_data)

        # Calculate price per sqm if both available
        if "price_sar" in self.extracted_data and "area_sqm" in self.extracted_data:
            self.extracted_data["price_per_sqm"] = round(
                self.extracted_data["price_sar"] / self.extracted_data["area_sqm"], 2
            )

        location_data = self.extract_location()
        if location_data:
            self.extracted_data.update(location_data)

        ptype = self.extract_property_type()
        if ptype:
            self.extracted_data["property_type"] = ptype

        bedrooms = self.extract_bedrooms()
        if bedrooms:
            self.extracted_data["bedrooms"] = bedrooms

        bathrooms = self.extract_bathrooms()
        if bathrooms:
            self.extracted_data["bathrooms"] = bathrooms

        tenure = self.extract_tenure()
        if tenure:
            self.extracted_data["tenure"] = tenure

        description = self.extract_description()
        if description:
            self.extracted_data["description"] = description

        logger.info(f"Extracted {len(self.extracted_data)} fields")
        return True

    def save(self, output_dir: str = "./data/raw") -> Optional[str]:
        """
        Save extracted data to JSON file.

        Args:
            output_dir: Directory to save file

        Returns:
            Path to saved file or None on error
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"aqar_{timestamp}.json"
        filepath = output_path / filename

        output_data = {
            "metadata": {
                "source": "aqar.fm",
                "url": self.url,
                "extracted_at": datetime.utcnow().isoformat(),
                "extraction_version": "1.0",
            },
            "data": self.extracted_data,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"Failed to save data: {e}")
            return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract property data from Aqar.fm listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from URL
  python aqar_collector.py "https://aqar.fm/property/12345678"

  # Custom output directory
  python aqar_collector.py "https://aqar.fm/property/12345678" --output ./custom_dir

  # Show help
  python aqar_collector.py --help
        """,
    )

    parser.add_argument("url", help="Aqar.fm property listing URL")
    parser.add_argument(
        "--output",
        type=str,
        default="./data/raw",
        help="Output directory for extracted JSON (default: ./data/raw)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run collector
    collector = AqarCollector(args.url)
    if collector.collect():
        filepath = collector.save(args.output)
        if filepath:
            print(f"\nSuccess: Data saved to {filepath}")
            print(f"Extracted fields: {list(collector.extracted_data.keys())}")
            return 0

    logger.error("Extraction failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
