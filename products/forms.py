from django import forms
from .models import Product, Category, ProductImage, Variant

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image', 'category', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set "Other" as default category if it exists
        try:
            other_category = Category.objects.get(name__iexact="Other")
            self.fields['category'].initial = other_category.id
        except Category.DoesNotExist:
            pass



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        


class AdditionalImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['size', 'color', 'price', 'stock']