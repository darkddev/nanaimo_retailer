from django.db import models

# Create your models here.
class Website(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, null=True, blank=True)
    url = models.CharField(max_length=100, null=True, blank=True)
    class Meta:
        db_table = 'wp_websites'

    def __str__(self):
        return self.domain
    
class Category(models.Model):
    ROLES = models.TextChoices("leaf", "node")
    site = models.ForeignKey(Website, on_delete=models.CASCADE, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=100, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    orig_id = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, default='0')
    role = models.CharField(max_length=10, null=True, blank=True, choices=ROLES)
    level = models.IntegerField(null=True, blank=True)
    google_path = models.CharField(max_length=300, null=True, blank=True)
    orig_path = models.CharField(max_length=300, null=True, blank=True)
    class Meta:
        db_table = 'wp_categories'

    def __str__(self):
        return self.name if self.name else str(self.id)

class Product(models.Model):
    site = models.ForeignKey(Website, on_delete=models.CASCADE, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_index=True)
    name = models.TextField(null=True, blank=True)
    brand = models.CharField(max_length=50, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    specification = models.TextField(null=True, blank=True)
    features = models.TextField(null=True, blank=True)
    images = models.TextField(null=True, blank=True)
    is_variant = models.BooleanField(default=False)

    skus = models.TextField(null=True, blank=True)
    orig_id = models.CharField(max_length=30, null=True, blank=True)
    wwmall_id = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)

    sale_price = models.FloatField(null=True, blank=True)
    regular_price = models.FloatField(null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True)
    attributes = models.TextField(null=True, blank=True)
    variants = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'wp_products'

    def __str__(self):
        return self.name if self.name else str(self.id)