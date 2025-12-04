import io
import logging
import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.forms import inlineformset_factory

from cloudinary.models import CloudinaryField
from PIL import Image

from .models import Product, Category, ProductVariant, ProductImage


logger = logging.getLogger(__name__)

class ProductCreateForm(forms.ModelForm):
    """Simplified form for product creation - only basic fields"""
    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Main product image (required)',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
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

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'file'):  # It's a file upload
            # Check file size (limit to 10MB)
            if hasattr(image, 'size') and image.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Image file size cannot exceed 10MB.')
            
            # Check image dimensions
            try:
                # Seek to beginning of file
                if hasattr(image, 'seek'):
                    image.seek(0)
                
                img = Image.open(image)
                width, height = img.size
                
                # Ensure minimum dimensions
                if width < 300 or height < 300:
                    raise ValidationError('Image dimensions should be at least 300x300 pixels.')
                
                # Ensure aspect ratio is reasonable
                ratio = width / height
                if ratio < 0.5 or ratio > 2:
                    raise ValidationError('Image aspect ratio should be between 0.5 and 2.')
                    
            except Exception as e:
                raise ValidationError('Invalid image file.')
            
            # Reset file pointer after reading
            if hasattr(image, 'seek'):
                image.seek(0)
        
        return image

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


class ProductEditForm(forms.ModelForm):
    """Full form for product editing - includes all fields"""
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Change main product image (optional)',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
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
        if image and hasattr(image, 'file'):  # It's a file upload, not CloudinaryResource
            # Check file size (limit to 10MB)
            if hasattr(image, 'size') and image.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Image file size cannot exceed 10MB.')
            
            # Check image dimensions
            try:
                # Seek to beginning of file
                if hasattr(image, 'seek'):
                    image.seek(0)
                
                img = Image.open(image)
                width, height = img.size
                
                # Ensure minimum dimensions
                if width < 300 or height < 300:
                    raise ValidationError('Image dimensions should be at least 300x300 pixels.')
                
                # Ensure aspect ratio is reasonable
                ratio = width / height
                if ratio < 0.5 or ratio > 2:
                    raise ValidationError('Image aspect ratio should be between 0.5 and 2.')
                    
            except Exception as e:
                raise ValidationError(f'Invalid image file: {str(e)}')
            
            # Reset file pointer after reading
            if hasattr(image, 'seek'):
                image.seek(0)
        
        return image


class ProductVariantForm(forms.ModelForm):
    """Form for individual product variants"""
    
    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'price', 'stock_quantity', 'is_active']
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
                'min': '0',
                'required': True
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
        labels = {
            'price': 'Price (₹) *',
            'compare_price': 'Compare Price (₹)',
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            raise ValidationError('Price is required.')
        if price < 0:
            raise ValidationError('Price cannot be negative.')
        return price

    

    def clean_stock_quantity(self):
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock


class ProductImageForm(forms.ModelForm):
    """Form for product images"""
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        widgets = {
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Image description for SEO'
            }),
        }
        labels = {
            'display_order': 'Display order (lower numbers show first)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If instance exists and has image, make the field not required
        if self.instance and self.instance.pk and self.instance.image:
            self.fields['image'].required = False

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'file'):  # It's a file upload, not CloudinaryResource
            # Check file size (limit to 10MB)
            if hasattr(image, 'size') and image.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError('Image file size cannot exceed 10MB.')
            
            # Check image dimensions
            try:
                # Seek to beginning of file
                if hasattr(image, 'seek'):
                    image.seek(0)
                
                img = Image.open(image)
                width, height = img.size
                
                # Ensure minimum dimensions
                if width < 300 or height < 300:
                    raise ValidationError('Image dimensions should be at least 300x300 pixels.')
                
                # Ensure aspect ratio is reasonable
                ratio = width / height
                if ratio < 0.5 or ratio > 2:
                    raise ValidationError('Image aspect ratio should be between 0.5 and 2.')
                    
            except Exception as e:
                raise ValidationError(f'Invalid image file: {str(e)}')
            
            # Reset file pointer after reading
            if hasattr(image, 'seek'):
                image.seek(0)
        
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
    extra=1,  # Show only 1 empty image form by default
    can_delete=True,
    min_num=0,
    validate_min=False,
    max_num=10,  # Limit to 10 images
)



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'auto-generated-slug'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter category description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_name(self):
        """
        Form-level validation for case-insensitive unique name
        """
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Category name is required.')
        
        # Case-insensitive uniqueness check
        if name:
            queryset = Category.objects.filter(name__iexact=name)
            
            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                # Find the existing name (with its original case)
                existing_name = queryset.first().name
                raise ValidationError(
                    f'A category with name "{existing_name}" already exists. '
                    f'Names are case-insensitive.'
                )
        
        return name

    def clean_slug(self):
        """
        Form-level validation for unique slug
        """
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        # Generate slug from name if slug is empty
        if not slug and name:
            slug = slugify(name)
        
        # Ensure slug is unique
        if slug:
            queryset = Category.objects.filter(slug=slug)
            
            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError('A category with this slug already exists.')
        
        return slug