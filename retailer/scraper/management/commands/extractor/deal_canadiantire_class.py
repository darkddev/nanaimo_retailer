import requests
import json
from scraper.models import Website, Category, Product
import re
import time

LANG = "en_CA"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
API_LOAD_CATEGORY = "/v1/category/api/v1/categories"
API_LOAD_PRODUCT = "/v1/search/search"
API_GET_PRODUCT = "/v1/product/api/v1/product/productFamily"
API_GET_PRICE = "/v1/product/api/v1/product/sku/PriceAvailability"
API_TIMEOUT = 10000

class DealCandianTireScraper:
    def __init__(self) -> None:
        self.settings = None
        self.session = requests.session()
        self.category_count = 0
        self.product_count = 0
        self.site = None
        self.all_deals = []
        self.temp_products_update= []

    def get_site_id(self, name):
        try:
            site = Website.objects.get(name=name)
            return site
        except Website.DoesNotExist:
            return False

    def change_old2new_inlist(self, orig_id):
        found = False

        for item in self.all_deals:
            if item.orig_id == orig_id:
                found = True
                break
        return found
    
    def set_settings(self, settings):
        for key in ["name", "domain", "url", "label", "id", "store", "apikey", "apiroot"]:
            if key not in settings:
                print(f"{key} is absent in settings")
                return False
        self.settings = settings
        return True

    def reverse_old_deals(self):
        self.site = self.get_site_id(self.settings["name"])
        old_deal_products = Product.objects.filter( site = self.site, is_deal = True )
        self.all_deals.extend(old_deal_products)

    def get_product_response(self, url, max_retries = 5 , delay = 2):
        retries = 0
        while retries < max_retries:
            try:
                resp = self.session.get(
                    url, 
                    headers = {
                        "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                        "Bannerid": self.settings["id"],
                        "Basesiteid": self.settings["id"],
                        "User-Agent": USER_AGENT,
                        "Count": "100",
                        "Q" : self.settings.get("query", None),
                        "experience" : self.settings.get("experience", None),
                        "hidefacets" : self.settings.get("hidefacets",None),
                        "widgetid" : self.settings.get("widgetid", None),
                    },
                    timeout = API_TIMEOUT
                )
                if resp.status_code == 200:
                    return resp.json()
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
            retries += 1
            print(f"PRODUCT:Retrying... ({retries}/{max_retries})")
            time.sleep(delay)
            
        print("Max retries reached. Could not get a successful response.")
        return None    

    def extract_products(self, page):
        url = f"{self.settings['apiroot']}{API_LOAD_PRODUCT}?store={self.settings['store']}"

        if page > 1:
            url += f";page={page}"
        
        result = self.get_product_response(url)
        
        if result != None:
            
            for product_info in result.get("products", []):
                try:
                    orig_id = product_info["code"]
                    is_exist = self.change_old2new_inlist(orig_id)
                    
                    if is_exist:
                        pass
                    else:
                        try:
                            product = Product.objects.get(site = self.site, orig_id=orig_id)
                            self.all_deals.append(product)
                        except Product.DoesNotExist:
                            pass
                except Exception as e:
                    print (e)
                    continue
            return result["pagination"]["total"]
        else:
            return None
        
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

    def update_price(self, pre_info):
        skus = pre_info.skus.split(",")
        sku_params = []
        for sku in skus:
            sku_params.append({"code": str(sku), "lowStockThreshold": "0"})

        
        result = self.get_price_response(sku_params=sku_params)
        if result != None:
            try:
                prods = result["skus"]
                if pre_info.is_variant:
                    try:
                        old_variants = json.loads(pre_info.variants.replace("'", '"'))
                    except json.JSONDecodeError as e:
                        old_variants = []
                        
                    new_variants = []
                    
                    discount = 0
                    new_discount = 0
                    
                    for sku_value in prods:
                        for variant in old_variants:
                            if variant["sku"] == sku_value["code"]:
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
                                
                                if variant['regular_price'] > 0 and variant['sale_price'] > 0:
                                    if variant['regular_price'] > variant['sale_price']:
                                        new_discount = (variant['regular_price'] - variant['sale_price']) / variant['regular_price'] * 100
                                else:
                                    new_discount = 0
                                    
                                try:
                                    if "Discount Applied" in sku_value["priceMessage"][0]["label"] if sku_value["priceMessage"][0]["label"] ==  None else "":
                                        pattern = r'(\d+)%'
                                        match = re.search(pattern, sku_value["priceMessage"][0]["label"] if sku_value["priceMessage"][0]["label"] ==  None else "" )
                                        if match:
                                            new_discount = int(match.group(1))
                                except:
                                    pass
                                        
                                if new_discount > discount:
                                    discount = new_discount
                                    
                                new_variants.append(variant)
                    self.product_count +=1
                    
                    if discount >= 30:
                        print(f"*** {pre_info.orig_id} 30% off. : Discount : {discount} : Count : {self.product_count}")
                        pre_info.variants = json.dumps(new_variants)
                        pre_info.is_deal = True
                    else:
                        pre_info.variants = json.dumps(new_variants)
                        pre_info.is_deal = False
                        print(f"--- No Deal : {pre_info.orig_id} : Discount : {discount} : Count : {self.product_count}")
                    self.temp_products_update.append(pre_info)
                else:
                    sku_value = prods[0]
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

                    if regular_price > 0 and sale_price > 0:
                        if regular_price > sale_price: 
                            discount = (regular_price - sale_price) / regular_price * 100
                    else:       
                        discount = 0
                    try:
                        if "Discount Applied" in sku_value["priceMessage"][0]["label"] if sku_value["priceMessage"][0]["label"] ==  None else "":
                            pattern = r'(\d+)%'
                            match = re.search(pattern, sku_value["priceMessage"][0]["label"] if sku_value["priceMessage"][0]["label"] ==  None else "")
                            if match:
                                discount = int(match.group(1))
                    except:
                        pass
                    self.product_count +=1
                    if discount >= 30:
                        print(f"*** Deal : {pre_info.orig_id} 30% off : Discount : {discount} : Count : {self.product_count}")
                        pre_info.regular_price = regular_price
                        pre_info.sale_price = sale_price
                        pre_info.stock = stock
                        pre_info.is_deal = True
                    else:
                        pre_info.regular_price = regular_price
                        pre_info.sale_price = sale_price
                        pre_info.stock = stock
                        pre_info.is_deal = False
                        print(f"--- No Deal : {pre_info.orig_id} : Discount : {discount} : Count : {self.product_count}")
                    self.temp_products_update.append(pre_info)
                return True
            except:
                return False
        else:
            return False
        
    def start(self):
        print("Starting Deal products...")

        if self.settings is None:
            print(f"settings should be set, first.")
            return
        while True:
            print("Reversing Old deals to init...")

            self.reverse_old_deals()

            page = 1
            
            while True:
                print(f"### Scraping Deal Page : PAGE {page}")
                total = self.extract_products(page)
                if total != None:
                    if page >= total:
                        break
                    page += 1
                else:
                    page += 1
                    continue

            print("Update Price for All Deals")

            for index, item in enumerate(self.all_deals, start=1):
                if item.is_deal:
                    print(f"+++ Update Price For Old Deal : {item.orig_id}")
                    success = self.update_price(item)
                    if success == False:
                        print(f"Failed : Update Price For New Deal : {item.orig_id}")
                else:
                    print(f"--- Update Price For New Deal : {item.orig_id}")
                    success = self.update_price(item)
                    if success == False:
                        print(f"Failed : Update Price For New Deal : {item.orig_id}")
                
                if index % 100 == 0:
                    print(f"Bulk Update Deals")
                    Product.objects.bulk_update(self.temp_products_update, ['sale_price', 'regular_price', 'stock', 'is_deal', 'variants'])
                    self.temp_products_update.clear()
                    
            print(f"Updated Deals for site : {self.settings['domain']}")
            self.product_count = 0