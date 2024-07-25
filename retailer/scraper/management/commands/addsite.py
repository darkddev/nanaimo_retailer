from django.core.management.base import BaseCommand, CommandError, CommandParser
from scraper.models import Website, Category, Product


class Command(BaseCommand):
    help = "Add new site"
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str, help="Name of the site")
        parser.add_argument("--domain", type=str, help="Domain name of the site")
        parser.add_argument("--url", type=str, help="Url of the site")
    
    def handle(self, *args, **options):
        site_name = options['name']
        site_domain = options['domain']
        site_url = options['url']
        try :
            site = Website.objects.get(name=site_name)
            self.stdout.write(f"{site.name} is already existed")
        except Website.DoesNotExist:
            site = Website(name=site_name, domain=site_domain, url=site_url)
            site.save()
            self.stdout.write(f"{site.name} is created")
        except :
            self.stdout.write(f"{site.name} is failed to create")