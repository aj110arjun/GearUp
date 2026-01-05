import uuid

from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.conf import settings

from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from core.validators import validate_image_file


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Model-level validation for case-insensitive unique name
        """
        super().clean()
        
        # Check for case-insensitive duplicate names
        if self.name:
            queryset = Category.objects.filter(name__iexact=self.name)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            if queryset.exists():
                raise ValidationError(
                    {'name': 'A category with this name already exists (case-insensitive).'}
                )

    def save(self, *args, **kwargs):
        """
        Save method with case-insensitive name check and slug generation
        """
        # Run full model validation
        self.full_clean()
        
        # Generate slug from name if empty
        if not self.slug and self.name:
            self.slug = slugify(self.name)
            
            # Ensure slug is unique
            base_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
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
    image = CloudinaryField('products/', validators=[validate_image_file])
    
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
    is_deleted = models.BooleanField(default=False)
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
        return reverse('products:product_detail_user', kwargs={'slug': self.slug})

    @property
    def in_stock(self):
        """Check if any variant is in stock"""
        return self.variants.filter(is_deleted=False, stock_quantity__gt=0).exists()

    @property
    def min_price(self):
        """Get minimum price from variants (considering offers)"""
        variants = self.variants.filter(is_active=True, is_deleted=False)
        if variants.exists():
            return min(variant.get_discounted_price() for variant in variants)
        return 0

    @property
    def max_price(self):
        """Get maximum price from variants (considering offers)"""
        variants = self.variants.filter(is_active=True, is_deleted=False)
        if variants.exists():
            return max(variant.get_discounted_price() for variant in variants)
        return 0
    
    def get_in_stock_variants(self):
        """Return all variants that are in stock"""
        return self.variants.filter(is_deleted=False, stock_quantity__gt=0)
    
    def get_first_in_stock_variant(self):
        """Return the first variant that is in stock, or None"""
        in_stock = self.get_in_stock_variants()
        return in_stock.first() if in_stock.exists() else None

    @property
    def get_first_variant(self):
        """Get the first non-deleted variant"""
        return self.variants.filter(is_deleted=False).first()

    # ADD THESE PROPERTIES FOR TEMPLATE COMPATIBILITY
    @property
    def avg_rating(self):
        """Calculate average rating for the product, prioritizing annotated values"""
        if hasattr(self, 'avg_rating_sort'):
            return round(self.avg_rating_sort, 1) if self.avg_rating_sort else 0
        return self.get_average_rating()

    @property
    def rating_count(self):
        """Get number of ratings, prioritizing annotated values"""
        if hasattr(self, 'review_count_sort'):
            return self.review_count_sort
        return self.get_total_reviews()

    @property
    def review_count(self):
        """Alias for rating_count for template compatibility"""
        return self.rating_count

    @property
    def best_offer(self):
        """Get the best offer/discount for the product"""
        # If you have an Offer model, implement this
        return None  # Placeholder - implement based on your offer system
    
    def get_average_rating(self):
        """Calculate average rating"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            return round(avg, 1)
        return 0
    
    def get_rating_distribution(self):
        """Get rating distribution counts"""
        reviews = self.reviews.filter(is_approved=True)
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for rating in reviews.values_list('rating', flat=True):
            distribution[rating] = distribution.get(rating, 0) + 1
        return distribution
    
    def get_total_reviews(self):
        """Get total approved reviews count"""
        return self.reviews.filter(is_approved=True).count()
    
    def get_review_percentage(self):
        """Get percentage of reviews by rating"""
        total = self.get_total_reviews()
        if total == 0:
            return {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        
        distribution = self.get_rating_distribution()
        return {k: round((v / total) * 100, 1) for k, v in distribution.items()}


class VariantAttribute(models.Model):
    """Naming for attributes like 'Color', 'Size', 'Storage', etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class VariantAttributeValue(models.Model):
    """Values for attributes like 'Red', 'XL', '256GB'."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(VariantAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    """
    Refactored Product Variant model that supports flexible attributes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # New flexible attributes system
    attribute_values = models.ManyToManyField(VariantAttributeValue, related_name='variants')
    
    # Core Data
    sku = models.CharField(max_length=100, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    
    # Assets & Status
    main_image = CloudinaryField('variant_main/', validators=[validate_image_file], null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.product.name} - {self.get_display_name()}"

    def save(self, *args, **kwargs):
        # Auto-generate variant SKU if not provided
        if not self.sku:
            uuid_part = str(self.id).split('-')[0].upper()
            self.sku = f"VAR-{uuid_part}"
        super().save(*args, **kwargs)

    def get_display_name(self):
        """Dynamic display name based on all associated attributes"""
        attrs = self.attribute_values.all()
        if attrs.exists():
            return ' - '.join([a.value for a in attrs])
        return "Standard"

    @property
    def color(self):
        """Compatibility property for legacy templates"""
        val = self.attribute_values.filter(attribute__name__iexact='color').first()
        return val.value if val else ""

    @property
    def size(self):
        """Compatibility property for legacy templates"""
        val = self.attribute_values.filter(attribute__name__iexact='size').first()
        return val.value if val else ""

    @property
    def is_low_stock(self):
        """Check if stock is low (threshold: 5)"""
        return 0 < self.stock_quantity <= 5

    def get_best_offer(self):
        """Checks both Product and Category offers and returns the highest discount."""
        now = timezone.now()
        product_offer = self.product.offers.filter(is_active=True, start_date__lte=now, end_date__gte=now).order_by('-discount_percentage').first()
        product_discount = product_offer.discount_percentage if product_offer else 0
        
        category_offer = self.product.category.offers.filter(is_active=True, start_date__lte=now, end_date__gte=now).order_by('-discount_percentage').first()
        category_discount = category_offer.discount_percentage if category_offer else 0
        
        return max(product_discount, category_discount)

    @property
    def discounted_price(self):
        discount_percentage = self.get_best_offer()
        if discount_percentage > 0:
            return self.price - (self.price * discount_percentage / 100)
        return self.price

    def get_discounted_price(self):
        return self.discounted_price

    @property
    def discount_percentage(self):
        return self.get_best_offer()

    def get_discount(self):
        return self.discount_percentage


class ProductImage(models.Model):
    """Product images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('product_images/', validators=[validate_image_file])
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


class ProductVariantImage(models.Model):
    """Additional images for individual product variants"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('variant_images/', validators=[validate_image_file])
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'created_at']

    def __str__(self):
        return f"{self.variant} - Image {self.display_order}"


class ProductOffer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=100)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(90)],
        help_text="Discount percentage (10-90)"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.discount_percentage}% off {self.product.name}"

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class CategoryOffer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=100)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(90)],
        help_text="Discount percentage (10-90)"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.discount_percentage}% off {self.category.name}"

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star - Poor'),
        (2, '2 Stars - Fair'),
        (3, '3 Stars - Good'),
        (4, '4 Stars - Very Good'),
        (5, '5 Stars - Excellent'),
    ]
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} stars"
    
    def get_rating_stars(self):
        """Return HTML for star rating"""
        full_stars = '★' * self.rating
        empty_stars = '☆' * (5 - self.rating)
        return full_stars + empty_stars


# ReviewImage model commented out — not needed for review functionality
# class ReviewImage(models.Model):
#     review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
#     image = CloudinaryField('review_images/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     
#     def __str__(self):
#         return f"Image for {self.review}"


class ReviewVote(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    helpful = models.BooleanField()  # True = helpful, False = not helpful
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']