import requests
import json
from scraper.models import Website, Category, Product
import threading
import time

LANG = "en_CA"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
# USER_AGENT = "PostmanRuntime/7.39.0"
API_LOAD_CATEGORY = "/v1/category/api/v1/categories"
API_LOAD_PRODUCT = "/v1/search/search"
API_GET_PRODUCT = "/v1/product/api/v1/product/productFamily"
API_GET_PRICE = "/v1/product/api/v1/product/sku/PriceAvailability"
API_TIMEOUT = 10000

class PriceCanadianTireScraper:
    def __init__(self) -> None:
        self.settings = None
        self.session = requests.session()
        self.category_count = 0
        self.product_count = 0
        
    def set_settings(self, settings):
        for key in ["name", "domain", "url", "label", "id", "store", "apikey", "apiroot"]:
            if key not in settings:
                print(f"{key} is absent in settings")
                return False
        self.settings = settings
        return True
    
    def get_site(self, name):
        try:
            site = Website.objects.get(name=name)
            return site
        except Website.DoesNotExist:
            return False

    def get_price_response(self, sku_params, max_retries = 5, delay = 2):
        retries = 0
        while retries < max_retries:
            try:
                resp = requests.post(
                    f"{self.settings['apiroot']}{API_GET_PRICE}", 
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
                if resp.status_code == 200:
                    return resp.json()
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
            retries += 1
            print(f"PRICE:Retrying... ({retries}/{max_retries})")
            time.sleep(delay)
        print("Max retries reached. Could not get a successful response.")
        return None
    
    def start(self):
        while True:
            print(f"Updating Price for Site : {self.settings['domain']}")
            self.site = self.get_site(self.settings["name"])
            
            batch_size = 50
            total_count = Product.objects.filter(site=self.site).count()
            
            for offset in range(0, total_count, batch_size):
                bulk_skus = []
                products = Product.objects.filter(site = self.site).order_by('orig_id')[offset:offset+batch_size]
                
                for product in products:
                    if product.is_variant:
                        skus = product.skus.split(",")
                    else:
                        skus = product.skus.split(",")[:1]
                        
                    bulk_skus.extend(skus)
                    
                sku_params = []
                
                for sku in bulk_skus:
                    sku_params.append({"code":str(sku), "lowStockThreshold":"0"})

                result = self.get_price_response(sku_params)
                
                if result is not None:
                    prods = result["skus"]
                    for product in products:
                        if product.is_variant:
                            print(f"*** {product.orig_id} is updated.  : Deal : {product.is_deal}")
                            try:
                                old_variants = json.loads(product.variants.replace("'", '"'))
                            except json.JSONDecodeError as e:
                                old_variants = [] 
                                    
                            new_variants = []
                            
                            try:
                                for variant in old_variants:
                                    try:
                                        sku_value = next((item for item in prods if str(item["code"]) == variant["sku"] and variant["attributes"] != {}), None)
                                        if "originalPrice" in sku_value and sku_value["originalPrice"] is not None and "value" in sku_value["originalPrice"] and sku_value["originalPrice"]["value"] is not None:
                                            variant["regular_price"] = sku_value["originalPrice"]["value"]
                                        else:
                                            variant["regular_price"] = 0
                                        if "currentPrice" in sku_value and "value" in sku_value["currentPrice"] and sku_value["currentPrice"]["value"] is not None:
                                            variant["sale_price"] = sku_value["currentPrice"]["value"]
                                        else:
                                            variant["sale_price"] = 0
                                        if "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "Corporate" in sku_value["fulfillment"]["availability"] and "Quantity" in sku_value["fulfillment"]["availability"]["Corporate"]:
                                            variant["stock"] = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
                                        elif "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "quantity" in sku_value["fulfillment"]["availability"]:
                                            variant["stock"] = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
                                        else:
                                            variant["stock"] = 0   
                                        new_variants.append(variant)
                                    except:
                                        new_variants.append(variant)
                                        continue
                            except Exception as e:
                                print(e)
                                
                            product.variants = new_variants
                        else:
                            print(f"***{product.orig_id} is updated.  : Deal : {product.is_deal}")
                            sku_value = next((item for item in prods if str(item["code"]) == product.skus.split(",")[0]), None)
                            try:
                                if "originalPrice" in sku_value and sku_value["originalPrice"] is not None and "value" in sku_value["originalPrice"] and sku_value["originalPrice"]["value"] is not None:
                                    regular_price = sku_value["originalPrice"]["value"]
                                else:
                                    regular_price = 0
                                if "currentPrice" in sku_value and "value" in sku_value["currentPrice"] and sku_value["currentPrice"]["value"] is not None:
                                    sale_price = sku_value["currentPrice"]["value"]
                                else:
                                    sale_price = 0
                                if "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "Corporate" in sku_value["fulfillment"]["availability"] and "Quantity" in sku_value["fulfillment"]["availability"]["Corporate"]:
                                    stock = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
                                elif "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "quantity" in sku_value["fulfillment"]["availability"]:
                                    stock = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
                                else:
                                    stock = 0
                            
                                product.regular_price = regular_price
                                product.sale_price = sale_price
                                product.stock = stock
                            except:
                                product.stock = 0
                    Product.objects.bulk_update(products, ['sale_price', 'regular_price', 'stock', 'variants'])
                else:
                    continue