# products/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import Product, Category, ProductVariant, ProductImage
from django.forms import inlineformset_factory

class ProductCreateForm(forms.ModelForm):
    """Simplified form for product creation - only basic fields"""
    # Add image field to the create form
    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Main product image (required)'
    )
    
    class Meta:
        model = Product
        fields = ['name', 'slug', 'description', 'brand', 'category', 'sku', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter product description'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brand name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank to auto-generate'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Publish Product',
        }
        help_texts = {
            'slug': 'URL-friendly version of the name (auto-generated if left empty)',
            'sku': 'Leave blank to auto-generate SKU after saving',
        }

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check if SKU is unique
            queryset = Product.objects.filter(sku=sku)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A product with this SKU already exists.')
        return sku

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Auto-generate slug from name
            name = self.cleaned_data.get('name')
            if name:
                slug = slugify(name)
                
        if slug:
            # Check if slug is unique
            queryset = Product.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A product with this slug already exists.')
        
        return slug

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate image size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large ( > 5MB )')
            # Validate file type
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError('Only JPG, JPEG, PNG, and WebP files are allowed.')
        return image


class ProductEditForm(forms.ModelForm):
    """Full form for product editing - includes all fields"""
    # Add image field for editing main product image
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Change main product image (optional)'
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'brand', 'category', 'sku', 
            'is_active', 'is_featured', 'is_bestseller', 'track_inventory',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug',
                'readonly': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter product description',
                'required': True
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brand name',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product SKU',
                'readonly': True
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meta title for SEO (optional)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Meta description for SEO (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_bestseller': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'track_inventory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Product Name',
            'slug': 'URL Slug',
            'brand': 'Brand',
            'category': 'Category',
            'sku': 'SKU',
            'description': 'Description',
            'is_active': 'Active',
            'is_featured': 'Featured',
            'is_bestseller': 'Bestseller',
            'track_inventory': 'Track Inventory',
            'meta_title': 'Meta Title',
            'meta_description': 'Meta Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set category choices
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Select a category"
        
        # Slug and SKU are not editable in edit mode
        self.fields['slug'].disabled = True
        self.fields['sku'].disabled = True

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or not name.strip():
            raise ValidationError('Product name is required.')
        return name.strip()

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if not brand or not brand.strip():
            raise ValidationError('Brand is required.')
        return brand.strip()

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not description.strip():
            raise ValidationError('Description is required.')
        return description.strip()

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise ValidationError('Please select a category.')
        return category

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate image size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large ( > 5MB )')
            # Validate file type
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError('Only JPG, JPEG, PNG, and WebP files are allowed.')
        return image


class ProductVariantForm(forms.ModelForm):
    """Form for individual product variants"""
    
    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'price', 'compare_price', 'stock_quantity', 'is_active']
        widgets = {
            'size': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'e.g., M, L, XL'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'e.g., Red, Blue'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'compare_price': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '0',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price

    def clean_compare_price(self):
        compare_price = self.cleaned_data.get('compare_price')
        if compare_price is not None and compare_price < 0:
            raise ValidationError('Compare price cannot be negative.')
        return compare_price

    def clean_stock_quantity(self):
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock


class ProductImageForm(forms.ModelForm):
    """Form for product images"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'display_order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Image description for SEO'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': '0',
                'min': '0'
            }),
        }
        labels = {
            'is_primary': 'Set as primary image',
            'display_order': 'Display order (lower numbers show first)',
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validate image size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large ( > 5MB )')
            # Validate file type
            if not image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError('Only JPG, JPEG, PNG, and WebP files are allowed.')
        return image


# Create formsets
ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,  # Show 3 empty image forms by default
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter category description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Publish Category',
        }
        help_texts = {
            'slug': 'URL-friendly version of the name (auto-generated if left empty)',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            name = self.cleaned_data.get('name')
            if name:
                slug = slugify(name)

        if slug:
            queryset = Category.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A category with this slug already exists.')

        return slug

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            queryset = Category.objects.filter(name=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A category with this name already exists.')
        return name