import argparse
import logging
from pathlib import Path

from scraper import Scraper


class Formatter(logging.Formatter):
    """Adds time elapsed since start as hh:mm:ss"""

    def format(self, record):
        seconds = int(record.relativeCreated // 1000)
        record.elapsed = f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 60:02}"
        return super().format(record)


parser = argparse.ArgumentParser(
    description="Scrapes products from luksusowealkohole.pl into scraper_results/products. "
                "Without arguments it runs the scraper and resumes from the products already saved.")
parser.add_argument("--clean", action="store_true",
                    help="delete all scraped products and photos before running (this also resets the cache, "
                         "so everything is fetched again)")
parser.add_argument("--category", metavar="NAME",
                    help="scrape only this main category (case-insensitive), e.g. \"Whisky & Bourbon\"")
parser.add_argument("--save-categories", action="store_true",
                    help="save the category tree to scraper_results/debug/categories.json")
parser.add_argument("--save-listings", action="store_true",
                    help="save product URLs found on each subcategory's pages "
                         "to scraper_results/debug/listings.json")
parser.add_argument("--load-categories", action="store_true",
                    help="read the category tree from scraper_results/debug/categories.json instead of the website "
                         "(the file can be edited by hand, e.g. to fix category names)")
args = parser.parse_args()

# to the console and to scraper_results/scraper.log (appended, so resumed runs keep the history)
log_file = Path(__file__).resolve().parent.parent / "scraper_results" / "scraper.log"
log_file.parent.mkdir(exist_ok=True)
formatter = Formatter("%(asctime)s.%(msecs)03d | %(elapsed)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
handlers = [logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")]
for handler in handlers:
    handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=handlers)

scraper = Scraper('https://luksusowealkohole.pl/')
if args.clean:
    scraper.clear_result()
scraper.load_cache()
scraper.scrap(only_category=args.category, save_categories=args.save_categories, save_listings=args.save_listings,
              load_categories=args.load_categories)
