import requests
import json
from scraper.models import Website, Category, Product
from lxml import html
from lxml.html import tostring
import math

API_TIMEOUT = 100000

class KmstoolsScraper:
    def __init__(self) -> None:
        self.settings           = None
        self.api_url            = "https://skg4w4.a.searchspring.io/api/search/search.json?"
        self.session            = requests.session()
        self.category_count     = 0
        self.product_count      = 0
        self.html_tree          = None
        self.categories         = []
        self.category_filters   = []
        pass

    def set_settings(self, settings):
        for key in ["name", "domain", "url", "label"]:
            if key not in settings:
                print(f"{key} is absent in settings")
                return False
        self.settings = settings
        return True

    def create_site(self, name, domain, url):
        try:
            site = Website.objects.get(name=name)
            return site
        except Website.DoesNotExist:
            site = Website.objects.create(name=name, domain=domain, url=url)
            return site
        except Exception as e:
            raise e

    def create_category(self, site, cat_info, level, parent = None, parent_paths = []):
        cat_paths = parent_paths.copy()
        cat_paths.append(cat_info["name"])
        orig_id = cat_info["name"].replace(' ', '') + "_" + str(level) + "_" + str(site.id)
        try:
            category = Category.objects.get(site=site, orig_id=orig_id)
            self.category_count += 1
            category.orig_path = " > ".join(cat_paths)
            category.save()
            print("-" * level, f"{self.category_count} : {category.name}: {cat_paths}")
        except Category.DoesNotExist:
            role = "leaf"
            if cat_info["sub_categories"] and len(cat_info["sub_categories"]) > 0:
                role ="node"
            category = Category.objects.create(
                site = site, 
                name = cat_info["name"],
                url = cat_info["url"],
                role = role,
                level = level,
                orig_id = orig_id,
                parent = parent,
                orig_path = " > ".join(cat_paths)
            )
            self.category_count += 1
            print("+" * level, f"{self.category_count} : {category.name}: {cat_paths}")
        except Exception as e:
            raise e
        if level > 1:
            self.category_filters.append(cat_paths)
        for subcat in cat_info["sub_categories"]:
            self.create_category(site, subcat, level + 1, category, cat_paths)

    def create_categories_for_site(self, site):
        print("make categories ...")
        resp = self.session.get(
            self.settings["url"],
            timeout = API_TIMEOUT
        )
        self.html_tree = html.fromstring(resp.text)
        li_cateory_parents = self.html_tree.cssselect('ul#navpro-topnav')[0].cssselect('div.navpro-dropdown.navpro-dropdown-level1.size-small')[0].cssselect('ul.children')[0].cssselect('li.parent')
        for li_cateory_parent in li_cateory_parents:
            name = li_cateory_parent.cssselect('a')[0].cssselect('span')[0].text_content().strip()
            url = li_cateory_parent.cssselect('a')[0].get('href')
            sub_categories = []
            for li_item in li_cateory_parent.cssselect('li.li-item'):
                sub_name = li_item.cssselect('a')[0].cssselect('span')[0].text_content().strip()
                sub_url = li_item.cssselect('a')[0].get('href')
                sub_categories.append({
                    'name' : sub_name,
                    'url' : sub_url,
                    'sub_categories' : []
                })
            sub_categories.pop(0)
            self.categories.append({
                'name' : name,
                'url' : url,
                'sub_categories' : sub_categories
            })
        for category in self.categories:
            self.create_category(site, category, 1)
    
    def create_products_for_site(self, site):
        print("make products ...")
        for cat_path in self.category_filters:
            cat_url = f"{self.api_url}resultsFormat=native&siteId=skg4w4&bgfilter.category_hierarchy={'>'.join(cat_path)}"
            resp = self.session.get(
                cat_url,
                timeout = API_TIMEOUT
            )
            result = resp.json()
            totalPages = result['pagination']['totalPages']
            if totalPages > 0:
                for page in range(1, totalPages+1):
                    products_url = f"{cat_url}&page={page}"
                    resp = self.session.get(
                        products_url,
                        timeout = API_TIMEOUT
                    )
                    result = resp.json()
                    products = result['results']
                    for product in products:
                        self.create_product_one_by_one(site, cat_path, product)

    def create_product_one_by_one(self, site, cat_path, product_info):
        orig_path = ' > '.join(cat_path)
        try:
            category = Category.objects.get(site=site, orig_path=orig_path)
            category_id = category.id
        except :
            print("Unregistered Category : ", orig_path)
            return
            
        url = f"{self.settings['url']}{product_info['url']}"
        print(url)
        orig_id = product_info["id"]
        sku = product_info["sku"]
        name = product_info["name"]
        sale_price = product_info["final_price"]
        stock = 0
        if 'stock_qty' in product_info :
            stock = math.floor(float(product_info["stock_qty"]))
        if stock == -1 :
            stock = 0
        brand = ""
        if 'brand' in product_info :
            brand = product_info["brand"] 


        try:
            product = Product.objects.get(name=name)
            self.product_count += 1
            print(f"--- PRODUCT {self.product_count} : {product.name}")
        except Product.DoesNotExist:
            resp = self.session.get(
                url,
                timeout = API_TIMEOUT
            )

            html_content = resp.text.replace('product.info.description', 'product-info-description')
            self.html_tree = html.fromstring(html_content)
            regular_price = 0
            description = ""
            images = []
            scripts = self.html_tree.xpath('//script[@type="text/x-magento-init"]/text()')
            for script in scripts:
                if 'mage/gallery/gallery' in script.strip():
                    gallery_data = json.loads(script.strip())
                    data_images = gallery_data['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data'] 
                    for data_image in data_images:
                        images.append(data_image['img'])
            try:
                if not self.html_tree.cssselect('#maincontent')[0].cssselect('div.columns')[0].cssselect('div.main')[0].cssselect('div.product-info-main'):
                    print("------ 404")
                    return
            except:
                return
            if self.html_tree.cssselect('#maincontent')[0].cssselect('div.columns')[0].cssselect('div.main')[0].cssselect('div.product-info-main')[0].cssselect('div.product-info-price')[0].cssselect('span.old-price') and len(self.html_tree.cssselect('#maincontent')[0].cssselect('div.columns')[0].cssselect('div.main')[0].cssselect('div.product-info-main')[0].cssselect('div.product-info-price')[0].cssselect('span.old-price')[0].cssselect('span.price-container')) > 0:
                regular_price = self.html_tree.cssselect('#maincontent')[0].cssselect('div.columns')[0].cssselect('div.main')[0].cssselect('div.product-info-main')[0].cssselect('div.product-info-price')[0].cssselect('div.price-box')[0].cssselect('span.old-price')[0].cssselect('span.price-container')[0].cssselect('span.price-wrapper')[0].text_content().strip().replace("$", "").replace(",", "")

            if self.html_tree.cssselect('div#product-info-description'):
                div_description = self.html_tree.cssselect('div#product-info-description')[0].cssselect('div.marketing_text')[0]
                description = tostring(div_description).decode('utf-8')
            product = Product.objects.create(
                site = site, 
                category_id = category_id,
                name = name,
                brand = brand,
                url = url,
                description = description,
                specification = "",
                features = "",
                images = json.dumps(images),
                orig_id = orig_id,
                skus = json.dumps([sku]),
                status = "off",
                stock = stock,
                sale_price = sale_price,
                regular_price = regular_price,
            )
            self.product_count += 1
            print(f"+++ PRODUCT {self.product_count} : {product.name}")

    def start(self):
        print("start to scrape ...")
        if self.settings is None:
            print(f"settings should be setted, first.")
            return
        site = self.create_site(self.settings["name"], self.settings["domain"], self.settings["url"]) 
        self.create_categories_for_site(site)
        self.create_products_for_site(site)
