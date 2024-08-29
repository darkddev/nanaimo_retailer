from django.core.management.base import BaseCommand, CommandParser
from .extractor.canadiantire import CandianTireScraper
from .extractor.kmstools import KmstoolsScraper

class Command(BaseCommand):
    help = "Scrape all categories and products from other site"
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("site", type=str, help="Name of the site")
    
    def handle(self, *args, **options):
        site_name = options['site']
        if site_name == "sportchek":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "sportchek",
                "domain": "sportchek.ca",
                "url": "https://www.sportchek.ca",
                "label": "SportChek",
                "id": "SC",
                "store": "290",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.sportchek.ca",
            })
        elif site_name == "deal_sportchek":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "sportchek",
                "domain": "sportchek.ca",
                "url": "https://www.sportchek.ca",
                "label": "SportChek",
                "id": "SC",
                "store": "290",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.sportchek.ca",
                "action": "deal",
                "query" : "saleclearance",
                "experience" : "sale|clearance",
                "widgetid" : "1"
            })
        elif site_name == "partycity":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "partycity",
                "domain": "partycity.ca",
                "url": "https://www.partycity.ca",
                "label": "PartyCity",
                "id": "PTY",
                "store": "872",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.partycity.ca",
            })
        elif site_name == "marks":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "marks",
                "domain": "marks.com",
                "url": "https://www.marks.com",
                "label": "Marks",
                "id": "MKS",
                "store": "730",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.marks.com",
            })
        elif site_name == "deal_marks":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "marks",
                "domain": "marks.com",
                "url": "https://www.marks.com",
                "label": "Marks",
                "id": "MKS",
                "store": "208",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.marks.com",
                "action":"deal",
                "query": "sale",
            })
        elif site_name == "canadiantire":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "canadiantire",
                "domain": "canadiantire.ca",
                "url": "https://www.canadiantire.ca",
                "label": "CanadianTire",
                "id": "CTR",
                "store": "179",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.canadiantire.ca",
            })
        elif site_name == "deal_canadiantire":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "canadiantire",
                "domain": "canadiantire.ca",
                "url": "https://www.canadiantire.ca",
                "label": "CanadianTire",
                "id": "CTR",
                "store": "365",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.canadiantire.ca",
                "action":"deal",
                "experience": "sale",
                "hidefacets": "deals"
            })
        elif site_name == "atmosphere":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "atmosphere",
                "domain": "atmosphere.ca",
                "url": "https://www.atmosphere.ca",
                "label": "Atmosphere",
                "id": "ATM",
                "store": "243",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.atmosphere.ca",
            })
        elif site_name == "deal_atmosphere":
            scraper = CandianTireScraper()
            scraper.set_settings({
                "name": "atmosphere",
                "domain": "atmosphere.ca",
                "url": "https://www.atmosphere.ca",
                "label": "Atmosphere",
                "id": "ATM",
                "store": "7403",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.atmosphere.ca",
                "action":"deal",
                "experience" : "sale|clearance",
                "widgetid" : "2jn4vze9"
            })
        elif site_name == "kmstools":
            scraper = KmstoolsScraper()
            scraper.set_settings({
                "name": "kmstools",
                "domain": "kmstools.com",
                "url": "https://www.kmstools.com",
                "label": "kmstools",
            })
        else:
            print(f"scraper script for {site_name} not found")
            return
        scraper.start()
        