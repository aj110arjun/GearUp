from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, AdditionalImage, ProductVariant

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'brand', 'image', 'category',
            'sku', 'track_inventory', 'is_active', 'is_featured', 'is_bestseller',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brand name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter product description'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU-001'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meta title for SEO'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Meta description for SEO'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'track_inventory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_bestseller': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Publish Product',
            'track_inventory': 'Track Inventory',
            'is_featured': 'Feature on Homepage',
            'is_bestseller': 'Mark as Bestseller',
        }
        help_texts = {
            'sku': 'Unique stock keeping unit',
            'image': 'Primary product image',
            'sku': 'Unique stock keeping unit',
        }

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check if SKU is unique (excluding current instance for edits)
            queryset = Product.objects.filter(sku=sku)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A product with this SKU already exists.')
        return sku

    def clean_compare_price(self):
        # Product model does not have compare_price/price at product level
        return self.cleaned_data.get('meta_description')


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = AdditionalImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color', 'size', 'sku', 'price', 'compare_price', 'stock_quantity', 'is_active', 'weight']
        widgets = {
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Color (e.g., Red)'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Size (e.g., Large)'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Variant SKU'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'compare_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


# Formset for multiple images
ProductImageFormSet = forms.inlineformset_factory(
    Product,
    AdditionalImage,
    form=ProductImageForm,
    extra=5,  # Number of empty forms to show
    can_delete=True,
    max_num=10  # Maximum number of images
)

# Formset for multiple variants
ProductVariantFormSet = forms.inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=3,  # Number of empty forms to show
    can_delete=True,
    max_num=20  # Maximum number of variants
)