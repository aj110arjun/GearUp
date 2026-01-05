import io
import logging
import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.forms import inlineformset_factory
from django.utils import timezone

from cloudinary.models import CloudinaryField
from PIL import Image

from core.validators import validate_image_file
from .models import Product, Category, ProductVariant, ProductImage, ProductVariantImage, ProductOffer, CategoryOffer, ProductReview


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
        validators=[validate_image_file]
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set category choices to only active and non-deleted
        self.fields['category'].queryset = Category.objects.filter(is_active=True, is_deleted=False)
        self.fields['category'].empty_label = "Select a category"

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
        validators=[validate_image_file]
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
                'class': 'sr-only peer'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
            }),
            'is_bestseller': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
            }),
            'track_inventory': forms.CheckboxInput(attrs={
                'class': 'sr-only peer'
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
        self.fields['category'].queryset = Category.objects.filter(is_active=True, is_deleted=False)
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
    """Refactored form for individual product variants supporting flexible attributes"""
    
    # We keep these fields in the form for UI ease, but we'll map them to the attribute system
    size = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-sm',
        'placeholder': 'e.g., M, L, XL'
    }))
    color = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-sm',
        'placeholder': 'e.g., Red, Blue'
    }))

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate size and color from attribute_values
            self.fields['size'].initial = self.instance.size
            self.fields['color'].initial = self.instance.color

    class Meta:
        model = ProductVariant
        fields = ['price', 'stock_quantity', 'main_image', 'is_active', 'sku']
        widgets = {
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
            'sku': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Auto-generated if blank'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'price': 'Price (₹) *',
            'main_image': 'Main Variant Image (Required)',
        }
    
    def clean_main_image(self):
        image = self.cleaned_data.get('main_image')
        if not image and not (self.instance and self.instance.main_image):
            raise ValidationError('Main variant image is required.')
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Map size and color to attribute system
            size_val = self.cleaned_data.get('size')
            color_val = self.cleaned_data.get('color')
            
            new_attrs = []
            if size_val:
                attr, _ = VariantAttribute.objects.get_or_create(name='Size')
                val, _ = VariantAttributeValue.objects.get_or_create(attribute=attr, value=size_val)
                new_attrs.append(val)
            
            if color_val:
                attr, _ = VariantAttribute.objects.get_or_create(name='Color')
                val, _ = VariantAttributeValue.objects.get_or_create(attribute=attr, value=color_val)
                new_attrs.append(val)
            
            if new_attrs:
                instance.attribute_values.set(new_attrs)
                
        return instance

    def clean(self):
        cleaned_data = super().clean()
        size = cleaned_data.get('size')
        color = cleaned_data.get('color')
        
        if self.product and size and color:
            # Check for existing variants with same attributes
            exists = ProductVariant.objects.filter(
                product=self.product,
                is_deleted=False
            )
            
            # This is a broad check, we should ideally check the specific attribute values
            # but for the simple Color/Size case this works as a safety net
            if self.instance and self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            
            # We'll refine this check if needed for more complex attributes
        return cleaned_data

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
        validators=[validate_image_file]
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


class ProductVariantImageForm(forms.ModelForm):
    """Form for additional images for product variants"""
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        validators=[validate_image_file]
    )
    
    class Meta:
        model = ProductVariantImage
        fields = ['image', 'alt_text', 'display_order']
        widgets = {
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Alt text'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.image:
            self.fields['image'].required = False

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'file'):
            if image.size > 10 * 1024 * 1024:
                raise ValidationError('Image file size cannot exceed 10MB.')
            try:
                if hasattr(image, 'seek'):
                    image.seek(0)
                img = Image.open(image)
                img.verify()
            except Exception:
                raise ValidationError('Invalid image file.')
            if hasattr(image, 'seek'):
                image.seek(0)
        return image


# Create formsets
ProductVariantImageFormSet = inlineformset_factory(
    ProductVariant,
    ProductVariantImage,
    form=ProductVariantImageForm,
    extra=1,
    can_delete=True
)


ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=0,
    can_delete=True
)

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make slug optional so model can auto-generate it if empty
        self.fields['slug'].required = False

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
                raise ValidationError(
                    'Category with this name already exists.'
                )
        
        return name

    def clean_slug(self):
        """
        Return parsed slug. We skip strict uniqueness check here to allow
        the model to handle auto-incrementing slugs (e.g. name-1) if needed,
        unless the user specifically entered a duplicate slug (which the model handles too).
        """
        slug = self.cleaned_data.get('slug')
        return slug


class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = ['product', 'name', 'discount_percentage', 'start_date', 'end_date', 'is_active']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'placeholder': 'e.g., Summer Sale 2025'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'placeholder': '10-90',
                'min': '10',
                'max': '90'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'type': 'date',
                'min': timezone.now().strftime('%Y-%m-%d'),
                'onchange': 'updateOfferEndDate()'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'type': 'date',
                'min': timezone.now().strftime('%Y-%m-%d')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 transition-all cursor-pointer'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Explicit empty checks (though Django handles required fields, custom messages are nice)
        if not cleaned_data.get('name'):
            self.add_error('name', 'Offer name is required.')
        
        if not cleaned_data.get('product'):
            self.add_error('product', 'Please select a product.')
            
        if not cleaned_data.get('discount_percentage'):
            self.add_error('discount_percentage', 'Discount percentage is required.')
            
        if not cleaned_data.get('start_date'):
            self.add_error('start_date', 'Start date is required.')
            
        if not cleaned_data.get('end_date'):
            self.add_error('end_date', 'End date is required.')

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        product = cleaned_data.get('product')
        is_active = cleaned_data.get('is_active')

        # 1. Date Validation: End Date must be >= Start Date
        if start_date and end_date:
            # Convert datetime to date for comparison if needed
            from datetime import date
            start = start_date.date() if hasattr(start_date, 'date') else start_date
            end = end_date.date() if hasattr(end_date, 'date') else end_date
            
            if end < start:
                raise ValidationError('End date cannot be before start date.')

        # 2. Prevent overlapping active offers for the same product
        if product and start_date and end_date and is_active:
            # Check for overlapping offers
            overlapping_offers = ProductOffer.objects.filter(
                product=product,
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                overlapping_offers = overlapping_offers.exclude(pk=self.instance.pk)

            if overlapping_offers.exists():
                raise ValidationError(
                    f'An active offer already exists for {product.name} during this time period. '
                    'Please adjust the dates or deactivate the other offer.'
                )
        
        return cleaned_data

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['category', 'name', 'discount_percentage', 'start_date', 'end_date', 'is_active']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'placeholder': 'e.g., Winter Collection Clearance'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'placeholder': '10-90',
                'min': '10',
                'max': '90'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'type': 'date',
                'min': timezone.now().strftime('%Y-%m-%d'),
                'onchange': 'updateOfferEndDate()'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all',
                'type': 'date',
                'min': timezone.now().strftime('%Y-%m-%d')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 transition-all cursor-pointer'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Explicit empty checks
        if not cleaned_data.get('name'):
            self.add_error('name', 'Offer name is required.')
        
        if not cleaned_data.get('category'):
            self.add_error('category', 'Please select a category.')
            
        if not cleaned_data.get('discount_percentage'):
            self.add_error('discount_percentage', 'Discount percentage is required.')
            
        if not cleaned_data.get('start_date'):
            self.add_error('start_date', 'Start date is required.')
            
        if not cleaned_data.get('end_date'):
            self.add_error('end_date', 'End date is required.')

        start_date = cleaned_data.get('start_date')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        category = cleaned_data.get('category')
        is_active = cleaned_data.get('is_active')

        # 1. Date Validation: End Date must be >= Start Date
        if start_date and end_date:
            # Convert datetime to date for comparison if needed
            from datetime import date
            start = start_date.date() if hasattr(start_date, 'date') else start_date
            end = end_date.date() if hasattr(end_date, 'date') else end_date
            
            if end < start:
                raise ValidationError('End date cannot be before start date.')

        # 2. Prevent overlapping active offers for the same category
        if category and start_date and end_date and is_active:
            # Check for overlapping offers
            overlapping_offers = CategoryOffer.objects.filter(
                category=category,
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                overlapping_offers = overlapping_offers.exclude(pk=self.instance.pk)

            if overlapping_offers.exists():
                raise ValidationError(
                    f'An active offer already exists for {category.name} during this time period. '
                    'Please adjust the dates or deactivate the other offer.'
                )
        
        return cleaned_data


class ProductReviewForm(forms.ModelForm):
    """Form for product reviews - without image upload"""
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=ProductReview.RATING_CHOICES),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a title for your review',
                'maxlength': '200'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this product...',
                'maxlength': '1000'
            }),
        }
        labels = {
            'rating': 'Your Rating',
            'title': 'Review Title',
            'comment': 'Your Review',
        }