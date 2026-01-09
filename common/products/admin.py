from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage, ProductOffer, CategoryOffer
from .forms import ProductOfferForm, CategoryOfferForm

class AdditionalImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'price', 'stock_quantity', 'is_active')
    list_filter = ('product', 'color', 'size', 'is_active')
    inlines = [AdditionalImageInline]

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True # Add this so admin can easily jump to variant edit page

class ProductOfferInline(admin.TabularInline):
    model = ProductOffer
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    inlines = [ProductVariantInline, ProductOfferInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ProductOffer)
class ProductOfferAdmin(admin.ModelAdmin):
    form = ProductOfferForm
    list_display = ('name', 'product', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(CategoryOffer)
class CategoryOfferAdmin(admin.ModelAdmin):
    form = CategoryOfferForm
    list_display = ('name', 'category', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
