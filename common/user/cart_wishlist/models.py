from django.db import models
from common.user.auths.models import UserModel
from common.products.models import Product, ProductVariant
import uuid

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserModel, 
        on_delete=models.CASCADE, 
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True) 

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart - {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.filter(variant__is_deleted=False, variant__product__is_deleted=False))

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.filter(variant__is_deleted=False, variant__product__is_deleted=False))

    @property
    def total_discount(self):
        # Calculate total discount for non-deleted items
        return sum(item.total_discount for item in self.items.filter(variant__is_deleted=False, variant__product__is_deleted=False))

    @property
    def shipping_cost(self):
        # ₹20 per valid item in the cart
        valid_items_count = self.items.filter(variant__is_deleted=False, variant__product__is_deleted=False).count()
        return valid_items_count * 20

    @property
    def final_total(self):
        return self.subtotal + self.shipping_cost

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.variant.product.name} - {self.quantity}"

    @property
    def unit_price(self):
        return self.variant.get_discounted_price()

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    @property
    def total_discount(self):
        return (self.variant.price * self.quantity) - self.total_price

    @property
    def is_available(self):
        return (not self.variant.is_deleted and 
                not self.variant.product.is_deleted and 
                self.variant.is_active and 
                self.variant.stock_quantity >= self.quantity)

    @property
    def max_quantity(self):
        """Return the maximum allowed quantity for this item (min of 5 or stock)"""
        return min(5, self.variant.stock_quantity)

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserModel, 
        on_delete=models.CASCADE, 
        related_name='wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f"Wishlist - {self.user.username}"

    @property
    def total_items(self):
        return self.items.filter(product__is_deleted=False).count()
    
    def add_product(self, product):
        """Add product to wishlist"""
        WishlistItem.objects.get_or_create(wishlist=self, product=product)
    
    def remove_product(self, product):
        """Remove product from wishlist"""
        WishlistItem.objects.filter(wishlist=self, product=product).delete()
    
    def has_product(self, product):
        """Check if product is in wishlist"""
        return WishlistItem.objects.filter(wishlist=self, product=product).exists()
    
    def get_product_ids(self):
        """Get list of product IDs in wishlist"""
        return list(self.items.values_list('product_id', flat=True))

class WishlistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ['wishlist', 'product']

    def __str__(self):
        return self.product.name
