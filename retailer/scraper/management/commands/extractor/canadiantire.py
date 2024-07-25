import requests
import json
from scraper.models import Website, Category, Product

LANG = "en_CA"
USER_AGENT = "PostmanRuntime/7.39.0"
API_LOAD_CATEGORY = "/v1/category/api/v1/categories"
API_LOAD_PRODUCT = "/v1/search/search"
API_GET_PRODUCT = "/v1/product/api/v1/product/productFamily"
API_GET_PRICE = "/v1/product/api/v1/product/sku/PriceAvailability"
API_TIMEOUT = 100000

class CandianTireScraper:
    def __init__(self) -> None:
        self.settings = None
        self.session = requests.session()
        self.category_count = 0
        self.product_count = 0
        pass
    
    def create_site(self, name, domain, url):
        try:
            site = Website.objects.get(name=name)
            return site
        except Website.DoesNotExist:
            site = Website.objects.create(name=name, domain=domain, url=url)
            return site
        except Exception as e:
            raise e

    def set_settings(self, settings):
        for key in ["name", "domain", "url", "label", "id", "store", "apikey", "apiroot"]:
            if key not in settings:
                print(f"{key} is absent in settings")
                return False
        self.settings = settings
        return True

    def extract_categories(self):
        resp = self.session.get(
            f"{self.settings["apiroot"]}{API_LOAD_CATEGORY}", 
            headers = {
                "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                "Bannerid": self.settings["id"],
                "Basesiteid": self.settings["id"],
                "User-Agent": USER_AGENT
            },
            params = {"lang" : LANG},
            timeout = API_TIMEOUT
        )
        result = resp.json()
        return result.get("categories", [])

    def extract_products(self, category, page):
        resp = self.session.get(
            f"{self.settings["apiroot"]}{API_LOAD_PRODUCT}", 
            headers = {
                "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                "Bannerid": self.settings["id"],
                "Basesiteid": self.settings["id"],
                "User-Agent": USER_AGENT,
                "Categorycode": category.orig_id,
                "Categorylevel": f"ast-id-level-{category.level}",
                "Count": "100",
            },
            params = {"store" : self.settings['store'] if page == 1 else f"{self.settings['store']};page={page}"},
            timeout = API_TIMEOUT
        )
        return resp.json()

    def extract_product(self, code):
        resp = self.session.get(
            f"{self.settings["apiroot"]}{API_GET_PRODUCT}/{code}", 
            headers = {
                "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                "Basesiteid": self.settings["id"],
                "User-Agent": USER_AGENT
            },
            params = {
                "baseStoreId": self.settings["id"],
                "lang": LANG,
                "storeId": self.settings["store"]
            },
            timeout = API_TIMEOUT
        )
        return resp.json()
    
    def extract_price(self, skus):
        sku_params = []
        for sku in skus:
            sku_params.append({"code": sku, "lowStockThreshold": "0"})
        resp = self.session.post(
            f"{self.settings["apiroot"]}{API_GET_PRICE}", 
            headers = {
                "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                "Basesiteid": self.settings["id"],
                "Bannerid": self.settings["id"],
                "User-Agent": USER_AGENT
            },
            params = {
                "cache": "true",
                "lang": LANG,
                "storeId": self.settings["store"]
            },
            json= { "skus":sku_params },
            timeout = API_TIMEOUT
        )
        return resp.json()
    
    def create_category(self, site, cat_info, level, parent = None, parent_paths = []):
        cat_paths = parent_paths.copy()
        cat_paths.append(cat_info["name"])
        try:
            category = Category.objects.get(site=site, orig_id=cat_info["id"])
            self.category_count += 1
            category.orig_path = " > ".join(cat_paths)
            category.save()
            print("-" * level, f"{self.category_count} : {category.name}: {cat_paths}")
        except Category.DoesNotExist:
            role = "leaf"
            if len(cat_info["subcategories"]) > 0:
                role ="node"
            category = Category.objects.create(
                site = site, 
                name = cat_info["name"],
                url = f"{site.url}{cat_info["url"]}",
                role = role,
                level = level,
                orig_id = cat_info["id"],
                parent = parent,
                orig_path = " > ".join(cat_paths)
            )
            self.category_count += 1
            print("+" * level, f"{self.category_count} : {category.name}: {cat_paths}")
        except Exception as e:
            raise e
        for subcat in cat_info["subcategories"]:
            self.create_category(site, subcat, level + 1, category, cat_paths)
    
    def create_categories_for_site(self, site):
        print("make categories ...")
        category_infos = self.extract_categories()
        for cat_info in category_infos:
            self.create_category(site, cat_info, 1)
    
    def create_products_for_site(self, site):
        categories = Category.objects.filter(site=site, parent=None)
        for category in categories:
            self.load_products_for_category(site, category)

    def load_products_for_category(self, site, category):
        if category.role == "node":
            subcats = Category.objects.filter(site=site, parent=category)
            for subcat in subcats:
                self.load_products_for_category(site, subcat)
        else:
            self.create_products_for_category(site, category)

    def create_products_for_category(self, site, category):
        page = 1
        while True:
            print(f"### CATEGORY ({category.name}): PAGE {page}")
            total = self.create_products_for_page(site, category, page)
            if page >= total:
                break
            page += 1


    def create_products_for_page(self, site, category, page):
        result = self.extract_products(category, page)
        print(result["pagination"]["total"], ":", result["resultCount"], ":", len(result["products"]))
        for product_info in result.get("products", []):
            try:
                self.create_product(site, category, product_info)
            except:
                pass
        return result["pagination"]["total"]

    def create_product(self, site, category, product_info):
        try:
            product = Product.objects.get(site=site, orig_id=product_info["code"])
            self.product_count += 1
            print(f"--- PRODUCT {self.product_count} : {product.name}")
        except Product.DoesNotExist:
            result = self.extract_product(product_info["code"])
            features = []
            if "featureBullets" in result:
                for feature in result["featureBullets"]:
                    features.append(feature.get("description", ""))
            specifications = {}
            if "specifications" in result:
                for spec in result["specifications"]:
                    specifications[spec["label"]] = spec["value"]
            if "images" in result:
                images = []
                for image in result["images"]:
                    images.append(image["url"])
            is_variant = False
            if "options" in result:
                is_variant = len(result["options"]) > 0
                attributes = {}
                optionid_attr_maps = {}
                for option in result["options"]:
                    values = []
                    for value in option["values"]:
                        optionid_attr_maps[value["id"]] = {"key" : option["display"], "value":value["value"]}
                        values.append(value["value"])
                    attributes[option["display"]] = values
            
            skus = []
            sku_attrs_map = {}
            if "skus" in result:
                for sku in result["skus"]:
                    skus.append(sku["code"])
                    attrs = {}             
                    for optionid in sku["optionIds"]:
                        attr = optionid_attr_maps[optionid]
                        attrs[attr["key"]] = attr["value"]
                    sku_attrs_map[sku["code"]] = attrs
            ret = self.extract_price(skus)
            if is_variant:
                variants = []
                for sku in ret["skus"]:
                    variant = {}
                    variant["sku"] = sku["code"]
                    if "originalPrice" in sku and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
                        variant["regular_price"] = sku["originalPrice"]["value"]
                    else:
                        variant["regular_price"] = 0
                    if "currentPrice" in sku and "value" in sku["currentPrice"] and sku["currentPrice"]["value"] is not None:
                        variant["sale_price"] = sku["currentPrice"]["value"]
                    else:
                        variant["sale_price"] = 0
                    if "fulfillment" in sku and "availability" in sku["fulfillment"] and "Corporate" in sku["fulfillment"]["availability"] and "Quantity" in sku["fulfillment"]["availability"]["Corporate"]:
                        variant["stock"] = sku["fulfillment"]["availability"]["Corporate"]["Quantity"]
                    elif "fulfillment" in sku and "availability" in sku["fulfillment"] and "quantity" in sku["fulfillment"]["availability"]:
                        variant["stock"] = sku["fulfillment"]["availability"]["Corporate"]["Quantity"]
                    else:
                        variant["stock"] = 0
                    variant["attributes"] = sku_attrs_map[sku["code"]]
                    variants.append(variant)
                Product.objects.create(
                    site = site, 
                    category = category,
                    name = result["name"],
                    brand = result["brand"]["label"],
                    url = f"{self.settings["url"]}{result["canonicalUrl"]}",
                    description = result["longDescription"],
                    specification = json.dumps(specifications),
                    features = json.dumps(features),
                    images = json.dumps(images),
                    is_variant = is_variant,
                    orig_id = product_info["code"],
                    skus = ",".join(skus),
                    status = "off",
                    attributes = json.dumps(attributes),
                    variants = json.dumps(variants),
                )
            else:
                sku = ret["skus"][0]
                if "originalPrice" in sku and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
                    regular_price = sku["originalPrice"]["value"]
                else:
                    regular_price = 0
                if "currentPrice" in sku and "value" in sku["currentPrice"] and sku["currentPrice"]["value"] is not None:
                    sale_price = sku["currentPrice"]["value"]
                else:
                    sale_price = 0
                if "fulfillment" in sku and "availability" in sku["fulfillment"] and "Corporate" in sku["fulfillment"]["availability"] and "Quantity" in sku["fulfillment"]["availability"]["Corporate"]:
                    stock = sku["fulfillment"]["availability"]["Corporate"]["Quantity"]
                elif "fulfillment" in sku and "availability" in sku["fulfillment"] and "quantity" in sku["fulfillment"]["availability"]:
                    stock = sku["fulfillment"]["availability"]["Corporate"]["Quantity"]
                else:
                    stock = 0
                Product.objects.create(
                    site = site, 
                    category = category,
                    name = result["name"],
                    brand = result["brand"]["label"],
                    url = f"{self.settings["url"]}{result["canonicalUrl"]}",
                    description = result["longDescription"],
                    specification = json.dumps(specifications),
                    features = json.dumps(features),
                    images = json.dumps(images),
                    is_variant = False,
                    orig_id = product_info["code"],
                    skus = ",".join(skus),
                    status = "off",
                    regular_price = regular_price,
                    sale_price = sale_price,
                    stock = stock
                )
            self.product_count += 1
            print(f"+++ PRODUCT {self.product_count} : {result["name"]}")
            # print(f"+++ PRODUCT {self.product_count} : {self.settings["url"]}{result["canonicalUrl"]}")
            
        except Exception as e:
            raise e
    
    def start(self):
        # try :
        print("start to scrape ...")
        if self.settings is None:
            print(f"settings should be setted, first.")
            return
        site = self.create_site(self.settings["name"], self.settings["domain"], self.settings["url"]) 
        self.create_categories_for_site(site)
        self.create_products_for_site(site)
        # except Exception as e:
        #     print(e)
        #     print(f"website({self.settings["name"]}) scraping failed")

    