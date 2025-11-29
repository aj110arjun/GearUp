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
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    brand = models.CharField(max_length=100)
    
    # Image
    image = CloudinaryField(
        'products/', 
        default="https://res.cloudinary.com/dhpo5iq3m/image/upload/jic4cjtfmvgh0zubu8gt.png"
    )
    
    # Categorization
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    
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
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug and self.name:
            self.slug = slugify(self.name)
            # Ensure slug is unique
            base_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Save first to get ID
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        # Auto-generate SKU after saving if new and no SKU provided
        if is_new and not self.sku:
            # Convert UUID to string, remove hyphens, and take first 8 chars
            uuid_str = str(self.id).replace('-', '')[:8].upper()
            self.sku = f"GRP-{uuid_str}"
            super().save(update_fields=['sku'])

    def get_absolute_url(self):
        # Use 'product_slug' to match your URL pattern
        return reverse('products:product_detail_user', kwargs={'product_slug': self.slug})

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
    
    def get_in_stock_variants(self):
        """Return all variants that are in stock"""
        return self.variants.filter(stock_quantity__gt=0)
    
    def get_first_in_stock_variant(self):
        """Return the first variant that is in stock, or None"""
        in_stock = self.get_in_stock_variants()
        return in_stock.first() if in_stock.exists() else None

    # ADD THESE PROPERTIES FOR TEMPLATE COMPATIBILITY
    @property
    def avg_rating(self):
        """Calculate average rating for the product"""
        # If you have a Review model, implement this
        return 4.5  # Placeholder - implement based on your review system

    @property
    def rating_count(self):
        """Get number of ratings"""
        # If you have a Review model, implement this
        return 10  # Placeholder

    @property
    def best_offer(self):
        """Get the best offer/discount for the product"""
        # If you have an Offer model, implement this
        return None  # Placeholder - implement based on your offer system


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant attributes
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['size', 'color']
        unique_together = [['product', 'size', 'color']]

    def __str__(self):
        parts = [self.product.name]
        if self.size:
            parts.append(self.size)
        if self.color:
            parts.append(self.color)
        return ' - '.join(parts)

    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    # ADD THESE METHODS FOR TEMPLATE COMPATIBILITY
    def get_display_name(self):
        """Return display name for variant selection"""
        parts = []
        if self.color:
            parts.append(self.color)
        if self.size:
            parts.append(self.size)
        return ' - '.join(parts) if parts else "Standard"

    def get_discounted_price(self):
        """Get discounted price if available"""
        if self.compare_price and self.compare_price > self.price:
            return self.compare_price
        return self.price

    def get_discount(self):
        """Get discount percentage for template"""
        return self.discount_percentage


class ProductImage(models.Model):
    """Product images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('product_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unmark others
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)