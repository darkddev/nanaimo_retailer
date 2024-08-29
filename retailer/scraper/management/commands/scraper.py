from django.core.management.base import BaseCommand, CommandParser
from .extractor.canadiantire import CandianTireScraper
from .extractor.deal_canadiantire_class import DealCandianTireScraper
from .extractor.kmstools import KmstoolsScraper
from .extractor.price_canadiantire_class import PriceCanadianTireScraper
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
            scraper = DealCandianTireScraper()
            scraper.set_settings({
                "name": "sportchek",
                "domain": "sportchek.ca",
                "url": "https://www.sportchek.ca",
                "label": "SportChek",
                "id": "SC",
                "store": "290",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.sportchek.ca",
                "query" : "saleclearance",
                "experience" : "sale|clearance",
                "widgetid" : "1"
            })
        elif site_name == "price_sportchek":
            scraper = PriceCanadianTireScraper()
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
        elif site_name == "price_partycity":
            scraper = PriceCanadianTireScraper()
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
            scraper = DealCandianTireScraper()
            scraper.set_settings({
                "name": "marks",
                "domain": "marks.com",
                "url": "https://www.marks.com",
                "label": "Marks",
                "id": "MKS",
                "store": "208",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.marks.com",
                "query": "sale",
                "experience": "sale",
                "hidefacets" : "undefined|undefined|deals|undefined"
            })
        elif site_name == "price_marks":
            scraper = PriceCanadianTireScraper()
            scraper.set_settings({
                "name": "marks",
                "domain": "marks.com",
                "url": "https://www.marks.com",
                "label": "Marks",
                "id": "MKS",
                "store": "208",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.marks.com",
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
            scraper = DealCandianTireScraper()
            scraper.set_settings({
                "name": "canadiantire",
                "domain": "canadiantire.ca",
                "url": "https://www.canadiantire.ca",
                "label": "CanadianTire",
                "id": "CTR",
                "store": "365",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.canadiantire.ca",
                "query":"store promotion",
                "experience": "sale",
                "hidefacets": "deals"
            })
        elif site_name == "price_canadiantire":
            scraper = PriceCanadianTireScraper()
            scraper.set_settings({
                "name": "canadiantire",
                "domain": "canadiantire.ca",
                "url": "https://www.canadiantire.ca",
                "label": "CanadianTire",
                "id": "CTR",
                "store": "910",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.canadiantire.ca",
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
            scraper = DealCandianTireScraper()
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
        elif site_name == "price_atmosphere":
            scraper = PriceCanadianTireScraper()
            scraper.set_settings({
                "name": "atmosphere",
                "domain": "atmosphere.ca",
                "url": "https://www.atmosphere.ca",
                "label": "Atmosphere",
                "id": "ATM",
                "store": "7403",
                "apikey": "c01ef3612328420c9f5cd9277e815a0e",
                "apiroot": "https://apim.atmosphere.ca",
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
        