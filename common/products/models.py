import uuid

from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from cloudinary.models import CloudinaryField


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    brand = models.CharField(max_length=100) 

    image = CloudinaryField('products/', default="https://res.cloudinary.com/dhpo5iq3m/image/upload/jic4cjtfmvgh0zubu8gt.png")
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    
    # Inventory & Identification
    sku = models.CharField(max_length=100, unique=True, blank=True)
    track_inventory = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"GRP{self.id:06d}" if self.id else "GRPTEMP"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        """Check if any variant is in stock"""
        return self.variants.filter(stock_quantity__gt=0).exists()

    @property
    def min_price(self):
        """Get minimum price from variants"""
        variants = self.variants.filter(is_active=True)
        if variants.exists():
            return min(variant.price for variant in variants)
        return 0

    @property
    def max_price(self):
        """Get maximum price from variants"""
        variants = self.variants.filter(is_active=True)
        if variants.exists():
            return max(variant.price for variant in variants)
        return 0
    

class ProductVariant(models.Model):
    # Required Fields (as per your request)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    
    # Additional Useful Fields
    sku = models.CharField(max_length=100, unique=True, blank=True)
    compare_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Original price for showing discounts"
    )
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Weight in grams"
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'color', 'size']
        ordering = ['product', 'color', 'size']

    def __str__(self):
        variant_name = f"{self.product.name}"
        if self.color:
            variant_name += f" - {self.color.name}"
        if self.size:
            variant_name += f" - {self.size.name}"
        return variant_name

    def save(self, *args, **kwargs):
        if not self.sku:
            base_sku = self.product.sku
            color_code = self.color.name[:3].upper() if self.color else "DEF"
            size_code = self.size.code if self.size else "ONE"
            self.sku = f"{base_sku}-{color_code}-{size_code}"
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        """Generate display name from color and size"""
        parts = []
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return " / ".join(parts) if parts else "Standard"

    @property
    def in_stock(self):
        """Check if variant is in stock"""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if variant is low in stock"""
        return 0 < self.stock_quantity <= 10

    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare price exists"""
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount)
        return 0

    @property
    def is_on_sale(self):
        """Check if variant is on sale"""
        return self.compare_price and self.compare_price > self.price
    

class AdditionalImage(models.Model):
    # Primary Key as UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = CloudinaryField('product_additional_images', default="https://res.cloudinary.com/dhpo5iq3m/image/upload/jic4cjtfmvgh0zubu8gt.png")

    class Meta:
        verbose_name = "Additional Product Image"
        verbose_name_plural = "Additional Product Images"

    def __str__(self):
        return f"Additional image for {self.product.name}"

    