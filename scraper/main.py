import argparse
from scraper import Scraper

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

scraper = Scraper('https://luksusowealkohole.pl/')
if args.clean:
    scraper.clear_result()
scraper.run()
scraper.scrap(only_category=args.category, save_categories=args.save_categories, save_listings=args.save_listings,
              load_categories=args.load_categories)
