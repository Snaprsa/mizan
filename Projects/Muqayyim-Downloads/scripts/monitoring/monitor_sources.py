#!/usr/bin/env python3
"""
Monitor real estate data sources for new content and classify relevance.

This script monitors Saudi real estate data sources (RSS feeds and web pages)
for new listings, transactions, and market news. It classifies content by
relevance and saves new items to JSON for further processing.

Usage:
    python monitor_sources.py                    # Run all sources
    python monitor_sources.py --source aqar      # Run specific source
    python monitor_sources.py --output ./custom  # Custom output directory
    python monitor_sources.py --help             # Show help

Requirements:
    - requests
    - All else is standard library
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
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


class SourceMonitor:
    """Monitor a single real estate data source."""

    # High relevance keywords
    HIGH_RELEVANCE_KEYWORDS = [
        "عقار",
        "اكتساب",
        "بيع",
        "صفقة",
        "قيمة",
        "مقيم",
        "إيجار",
        "مجمع",
        "برج",
        "فيلا",
        "شقة",
        "acquisition",
        "transaction",
        "valuation",
        "sale",
        "lease",
        "deal",
        "property",
        "real estate",
        "SAR",
        "million",
        "billion",
        "sqm",
        "riyadh",
        "jeddah",
        "dammam",
    ]

    # Medium relevance keywords
    MEDIUM_RELEVANCE_KEYWORDS = [
        "سوق",
        "عقاري",
        "سكن",
        "تجاري",
        "استثمار",
        "market",
        "price",
        "location",
        "apartment",
        "villa",
        "commercial",
        "residential",
        "investment",
        "housing",
    ]

    def __init__(self, source_name: str, source_url: str, source_type: str = "web"):
        """
        Initialize source monitor.

        Args:
            source_name: Human-readable name (e.g., "Aqar.fm")
            source_url: URL to monitor
            source_type: "rss" or "web"
        """
        self.source_name = source_name
        self.source_url = source_url
        self.source_type = source_type
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def check_robots_txt(self) -> bool:
        """
        Check if source domain allows scraping via robots.txt.

        Returns:
            True if allowed, False if disallowed
        """
        try:
            parsed = urlparse(self.source_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            can_fetch = rp.can_fetch("*", self.source_url)
            if not can_fetch:
                logger.warning(
                    f"{self.source_name}: robots.txt disallows fetching {self.source_url}"
                )
            return can_fetch
        except Exception as e:
            logger.debug(f"{self.source_name}: Could not check robots.txt: {e}")
            # Assume allowed if robots.txt check fails
            return True

    def fetch_content(self) -> Optional[str]:
        """
        Fetch page content.

        Returns:
            Page content or None on error
        """
        try:
            response = self.session.get(self.source_url, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"{self.source_name}: Failed to fetch {self.source_url}: {e}")
            return None

    def classify_relevance(self, text: str) -> str:
        """
        Classify relevance based on keyword presence.

        Args:
            text: Text to classify

        Returns:
            "high", "medium", or "low"
        """
        text_lower = text.lower()
        high_matches = sum(
            1 for kw in self.HIGH_RELEVANCE_KEYWORDS if kw in text_lower
        )
        medium_matches = sum(
            1 for kw in self.MEDIUM_RELEVANCE_KEYWORDS if kw in text_lower
        )

        if high_matches >= 2:
            return "high"
        elif high_matches >= 1 or medium_matches >= 3:
            return "medium"
        else:
            return "low"

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract basic metadata from content (stub - extend as needed).

        Args:
            content: Page content

        Returns:
            Metadata dictionary
        """
        metadata = {
            "length_chars": len(content),
            "contains_sar": "SAR" in content or "ر.س" in content,
            "contains_sqm": "sqm" in content or "م²" in content or "متر مربع" in content,
            "language": "mixed" if "ع" in content else "en",
        }
        return metadata


class RealEstateSourceRegistry:
    """Registry of Saudi real estate sources to monitor."""

    SOURCES = [
        {
            "name": "Aqar.fm",
            "url": "https://aqar.fm",
            "type": "web",
            "description": "Major Saudi real estate marketplace",
        },
        {
            "name": "Tadawul",
            "url": "https://www.tadawul.com.sa/exchange/about-exchange",
            "type": "web",
            "description": "Stock exchange announcements and disclosures",
        },
        {
            "name": "Al Arabiya Property",
            "url": "https://www.alarabiya.net/autos-and-property",
            "type": "web",
            "description": "News and market analysis",
        },
        {
            "name": "Saudi Gazette",
            "url": "https://saudigazette.com.sa",
            "type": "web",
            "description": "English Saudi newspaper",
        },
        {
            "name": "Bayut Saudi",
            "url": "https://bayut.com.sa",
            "type": "web",
            "description": "Gulf real estate marketplace",
        },
        {
            "name": "Property Finder",
            "url": "https://propertyfinder.sa",
            "type": "web",
            "description": "Property marketplace",
        },
        {
            "name": "Wafi",
            "url": "https://wafi.com.sa",
            "type": "web",
            "description": "Saudi services and property marketplace",
        },
        {
            "name": "Aqarsas",
            "url": "https://www.aqarsas.com",
            "type": "web",
            "description": "Saudi property marketplace",
        },
        {
            "name": "Paseetah",
            "url": "https://www.paseetah.com",
            "type": "web",
            "description": "Saudi property marketplace",
        },
        {
            "name": "Argaam",
            "url": "https://www.argaam.com/en/category/real-estate",
            "type": "web",
            "description": "Arabic financial and real estate news",
        },
    ]

    @classmethod
    def get_source(cls, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get source(s) from registry."""
        if name:
            return [s for s in cls.SOURCES if s["name"].lower() == name.lower()]
        return cls.SOURCES


def monitor_sources(
    output_dir: str = "./data/monitoring",
    source_filter: Optional[str] = None,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Monitor all registered sources for new content.

    Args:
        output_dir: Directory to save monitoring results
        source_filter: Filter to specific source name (optional)
        max_retries: Max retries per source

    Returns:
        Summary of monitoring run
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get sources
    if source_filter:
        sources = RealEstateSourceRegistry.get_source(source_filter)
        if not sources:
            logger.error(f"Source not found: {source_filter}")
            return {"status": "error", "message": f"Source not found: {source_filter}"}
    else:
        sources = RealEstateSourceRegistry.get_source()

    # Monitor each source
    run_timestamp = datetime.utcnow().isoformat()
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    results = {
        "timestamp": run_timestamp,
        "date": date_str,
        "sources_monitored": len(sources),
        "items_found": 0,
        "high_relevance": 0,
        "medium_relevance": 0,
        "low_relevance": 0,
        "errors": 0,
        "sources": [],
    }

    for source_info in sources:
        source_result = {
            "name": source_info["name"],
            "url": source_info["url"],
            "status": "unknown",
            "items_found": 0,
            "relevance": None,
            "error": None,
        }

        try:
            monitor = SourceMonitor(
                source_name=source_info["name"],
                source_url=source_info["url"],
                source_type=source_info["type"],
            )

            # Check robots.txt
            if not monitor.check_robots_txt():
                source_result["status"] = "blocked"
                source_result["error"] = "robots.txt disallows access"
                logger.warning(f"{source_info['name']}: Blocked by robots.txt")
                results["errors"] += 1
                results["sources"].append(source_result)
                continue

            # Fetch content
            content = monitor.fetch_content()
            if not content:
                source_result["status"] = "fetch_failed"
                results["errors"] += 1
                results["sources"].append(source_result)
                continue

            # Classify relevance
            relevance = monitor.classify_relevance(content)
            metadata = monitor.extract_metadata(content)

            source_result["status"] = "success"
            source_result["relevance"] = relevance
            source_result["metadata"] = metadata
            source_result["items_found"] = 1  # One page fetch

            # Update counters
            if relevance == "high":
                results["high_relevance"] += 1
            elif relevance == "medium":
                results["medium_relevance"] += 1
            else:
                results["low_relevance"] += 1

            results["items_found"] += 1
            logger.info(
                f"{source_info['name']}: {relevance} relevance "
                f"({metadata.get('length_chars', 0)} chars)"
            )

        except Exception as e:
            source_result["status"] = "error"
            source_result["error"] = str(e)
            results["errors"] += 1
            logger.error(f"{source_info['name']}: Unexpected error: {e}")

        results["sources"].append(source_result)

    # Save results
    output_file = output_path / f"monitor_run_{date_str}.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")
    except IOError as e:
        logger.error(f"Failed to save results: {e}")
        return {"status": "save_failed", "error": str(e)}

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Saudi real estate data sources for new content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor all sources
  python monitor_sources.py

  # Monitor specific source
  python monitor_sources.py --source aqar

  # Custom output directory
  python monitor_sources.py --output /var/monitoring/realestate

  # List available sources
  python monitor_sources.py --list
        """,
    )

    parser.add_argument(
        "--source",
        type=str,
        help="Monitor specific source by name (case-insensitive)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./data/monitoring",
        help="Output directory for monitoring results (default: ./data/monitoring)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sources and exit",
    )

    args = parser.parse_args()

    # List sources
    if args.list:
        print("\nAvailable Sources:")
        print("-" * 70)
        for source in RealEstateSourceRegistry.get_source():
            print(f"  {source['name']:<20} {source['description']}")
        print("-" * 70)
        print(f"\nTotal: {len(RealEstateSourceRegistry.get_source())} sources")
        return 0

    # Run monitoring
    logger.info(f"Starting monitoring run... (output: {args.output})")
    results = monitor_sources(
        output_dir=args.output,
        source_filter=args.source,
    )

    # Print summary
    print("\n" + "=" * 70)
    print("MONITORING SUMMARY")
    print("=" * 70)
    print(f"Timestamp: {results.get('timestamp')}")
    print(f"Sources monitored: {results.get('sources_monitored')}")
    print(f"Items found: {results.get('items_found')}")
    print(f"High relevance: {results.get('high_relevance')}")
    print(f"Medium relevance: {results.get('medium_relevance')}")
    print(f"Low relevance: {results.get('low_relevance')}")
    print(f"Errors: {results.get('errors')}")
    print("=" * 70 + "\n")

    return 0 if results.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
