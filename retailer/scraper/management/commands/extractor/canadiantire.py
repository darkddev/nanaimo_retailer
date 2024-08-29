import requests
import json
from scraper.models import Website, Category, Product

LANG = "en_CA"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
# USER_AGENT = "PostmanRuntime/7.39.0"
API_LOAD_CATEGORY = "/v1/category/api/v1/categories"
API_LOAD_PRODUCT = "/v1/search/search"
API_GET_PRODUCT = "/v1/product/api/v1/product/productFamily"
API_GET_PRICE = "/v1/product/api/v1/product/sku/PriceAvailability"
API_TIMEOUT = 10000

class CandianTireScraper:
    def __init__(self) -> None:
        self.settings = None
        self.session = requests.session()
        self.category_count = 0
        self.product_count = 0
    
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
        url = f"{self.settings["apiroot"]}{API_LOAD_PRODUCT}?store={self.settings['store']}"
        if page > 1:
            url += f";page={page}"
        resp = self.session.get(
            url, 
            headers = {
                "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
                "Bannerid": self.settings["id"],
                "Basesiteid": self.settings["id"],
                "User-Agent": USER_AGENT,
                "Categorycode": category.orig_id,
                "Categorylevel": f"ast-id-level-{category.level}",
                "Count": "100",
            },
            timeout = API_TIMEOUT
        )
        print(resp.status_code)
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
            sku_params.append({"code": str(sku), "lowStockThreshold": "0"})
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
        
        if self.settings.get('action', None) == 'deal':
            # update old deal products price with sku and is_deal
            print("Updating old deal price...")
            old_deal_products = Product.objects.filter(site=site, is_deal = True )
            for old_deal_product in old_deal_products:
                result = self.extract_product(old_deal_product.orig_id)
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

                sku_attrs_map = {}
                if "skus" in result:
                    for sku in result["skus"]:
                        attrs = {}             
                        for optionid in sku["optionIds"]:
                            attr = optionid_attr_maps[optionid]
                            attrs[attr["key"]] = attr["value"]
                        sku_attrs_map[sku["code"]] = attrs
            
                skus = old_deal_product.skus.split(",")
                ret = self.extract_price(skus)
                prods = ret["skus"]  
                
                if old_deal_product.is_variant:
                    variants = []
                    for sku in prods:
                        variant = {}
                        variant["sku"] = sku["code"]
                        if "originalPrice" in sku and sku["originalPrice"] is not None and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
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
                    Product.objects.filter(
                            site=site,
                            orig_id=old_deal_product.orig_id
                        ).update(
                            skus = ",".join(skus),
                            variants = json.dumps(variants),
                            is_deal = False,
                        )
                else:
                    sku = prods[0]
                    if "originalPrice" in sku and sku["originalPrice"] is not None and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
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
                    
                    Product.objects.filter(
                            site=site,
                            orig_id=old_deal_product.orig_id
                        ).update(
                            skus = ",".join(skus),
                            regular_price = regular_price,
                            sale_price = sale_price,
                            stock = stock,
                            is_deal = False
                        )              

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
        try:
            result = self.extract_products(category, page)
            print(result["pagination"]["total"], ":", result["resultCount"], ":", len(result["products"]))
            for product_info in result.get("products", []):
                try:
                    self.create_product(site, category, product_info)
                except Exception as e:
                    print(e)
<<<<<<< HEAD
=======
                    pass
>>>>>>> 95e0efd0660bf829e442d11a88f7cc9ea887e146
            return result["pagination"]["total"]
        except:
            print("Retrying to get products")
            self.create_products_for_page(site, category, page)
            return result["pagination"]["total"]

    def create_product(self, site, category, product_info):
        try:
            product = Product.objects.get(site=site, orig_id=product_info["code"])
            
            # result = self.extract_product(product_info["code"])
            
            # is_variant = False
            # if "options" in result:
            #     is_variant = len(result["options"]) > 0
            #     attributes = {}
            #     optionid_attr_maps = {}
            #     for option in result["options"]:
            #         values = []
            #         for value in option["values"]:
            #             optionid_attr_maps[value["id"]] = {"key" : option["display"], "value":value["value"]}
            #             values.append(value["value"])
            #         attributes[option["display"]] = values



            
            # skus = product.skus.split(",")
            # sku_params = []
            # for sku in skus:
            #     sku_params.append({"code": str(sku), "lowStockThreshold": "0"})
            # resp = self.session.post(
            #     f"{self.settings["apiroot"]}{API_GET_PRICE}", 
            #     headers = {
            #         "Ocp-Apim-Subscription-Key" : self.settings["apikey"],
            #         "Basesiteid": self.settings["id"],
            #         "Bannerid": self.settings["id"],
            #         "User-Agent": USER_AGENT
            #     },
            #     params = {
            #         "cache": "true",
            #         "lang": LANG,
            #         "storeId": self.settings["store"]
            #     },
            #     json= { "skus":sku_params },
            #     timeout = API_TIMEOUT
            # )
            # result = resp.json()
            # prods = result["skus"]

            # if product.is_variant:
            #     try:
            #         old_variants = json.loads((product.variants).replace("'", '"'))
            #     except json.JSONDecodeError as e:
            #         old_variants = []
            #     new_variants = []

            #     for sku_value in prods:
            #         for variant in old_variants:
            #             if variant["sku"] == sku_value["code"]:
            #                 if "originalPrice" in sku_value and sku_value["originalPrice"] is not None and "value" in sku_value["originalPrice"] and sku_value["originalPrice"]["value"] is not None:
            #                     variant["regular_price"] = sku_value["originalPrice"]["value"]
            #                 else:
            #                     variant["regular_price"] = 0
            #                 if "currentPrice" in sku_value and "value" in sku_value["currentPrice"] and sku_value["currentPrice"]["value"] is not None:
            #                     variant["sale_price"] = sku_value["currentPrice"]["value"]
            #                 else:
            #                     variant["sale_price"] = 0
            #                 if "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "Corporate" in sku_value["fulfillment"]["availability"] and "Quantity" in sku_value["fulfillment"]["availability"]["Corporate"]:
            #                     variant["stock"] = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
            #                 elif "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "quantity" in sku_value["fulfillment"]["availability"]:
            #                     variant["stock"] = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
            #                 else:
            #                     variant["stock"] = 0    
                            
            #                 new_variants.append(variant)

            #     Product.objects.filter( site = site, orig_id = product.orig_id ).update( variants = new_variants )  
                
            #     # resp = self.session.post( 
            #     #         url = "https://wwmalls.com/wp-json/admin/non-compliant/update-deal-price",
            #     #         params={
            #     #             'orig_id' : product.orig_id,
            #     #             'site_id' : site.name
            #     #         }
            #     #     )
            #     # print(resp.text)
            # else:
            #     sku_value = prods[0]
            #     if "originalPrice" in sku_value and sku_value["originalPrice"] is not None and "value" in sku_value["originalPrice"] and sku_value["originalPrice"]["value"] is not None:
            #         regular_price = sku_value["originalPrice"]["value"]
            #     else:
            #         regular_price = 0
            #     if "currentPrice" in sku_value and "value" in sku_value["currentPrice"] and sku_value["currentPrice"]["value"] is not None:
            #         sale_price = sku_value["currentPrice"]["value"]
            #     else:
            #         sale_price = 0
            #     if "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "Corporate" in sku_value["fulfillment"]["availability"] and "Quantity" in sku_value["fulfillment"]["availability"]["Corporate"]:
            #         stock = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
            #     elif "fulfillment" in sku_value and "availability" in sku_value["fulfillment"] and "quantity" in sku_value["fulfillment"]["availability"]:
            #         stock = sku_value["fulfillment"]["availability"]["Corporate"]["Quantity"]
            #     else:
            #         stock = 0
                
            #     Product.objects.filter(
            #         site = site,
            #         orig_id = product.orig_id
            #     ).update(
            #         regular_price = regular_price,
            #         sale_price = sale_price,
            #         stock = stock,
            #     )
            #     # resp = self.session.post( 
            #     #         url = "https://wwmalls.com/wp-json/admin/non-compliant/update-deal-price",
            #     #         params={
            #     #             'orig_id' : product.orig_id,
            #     #             'site_id' : site.name
            #     #         }
            #     #     )
            #     # print(resp.text)

            self.product_count += 1
            
            print(f"---Existing Product {self.product_count} : {product.name} was updated ")
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
            prods = ret["skus"]

            if is_variant:
                variants = []
                for sku in prods:
                    variant = {}
                    variant["sku"] = sku["code"]
                    if "originalPrice" in sku and sku["originalPrice"] is not None and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
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
                    is_deal = False
                )
                # resp = self.session.post( 
                #         url = "https://wwmalls.com/wp-json/admin/non-compliant/update-deal-price",
                #         params={
                #             'orig_id' : product_info["code"],
                #             'site_id' : site.name
                #         }
                #     )
                # print(resp.text)
            else:
                sku = prods[0]
                if "originalPrice" in sku and sku["originalPrice"] is not None and "value" in sku["originalPrice"] and sku["originalPrice"]["value"] is not None:
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
                    stock = stock,
                    is_deal = False
                )
                # resp = self.session.post( 
                #         url = "https://wwmalls.com/wp-json/admin/non-compliant/update-deal-price",
                #         params={
                #             'orig_id' : product_info["code"],
                #             'site_id' : site.name
                #         }
                #     )
                # print(resp.text)
            self.product_count += 1
            print(f"+++ PRODUCT {self.product_count} : {result["name"]}")
            
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

    