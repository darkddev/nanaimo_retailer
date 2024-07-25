from django.contrib import admin
import json
from .models import Website, Category, Product

class WebsiteAdmin(admin.ModelAdmin):
    list_display = ["name", "domain", "url"]

class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "site", "orig_id", "role", "orig_path", "google_path"]
    list_editable = ["google_path"]
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "site", "category", "orig_id", "images_count", "is_variant", "skus_count"]
    def images_count(self, obj):
        images = json.loads(obj.images)
        return len(images)
    images_count.short_description = "Images"
    def skus_count(self, obj):
        skus = obj.skus.split(",")
        return len(skus)
    skus_count.short_description = "Skus"
admin.site.register(Website, WebsiteAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)