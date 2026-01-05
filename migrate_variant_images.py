import os
import django
import sys

# Add the project root to sys.path
sys.path.append('/home/arjun-aj/Documents/django/project3/src/GearUp')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GearUp.settings')
django.setup()

from common.products.models import Product, ProductVariant, ProductImage, ProductVariantImage

def migrate_images():
    products = Product.objects.prefetch_related('variants', 'images').all()
    print(f"Starting migration for {products.count()} products...")
    
    for product in products:
        variants = product.variants.filter(is_deleted=False)
        if not variants.exists():
            continue
            
        # 1. Migrate main product image to the first variant
        primary_variant = variants.first()
        if product.image and not primary_variant.main_image:
            primary_variant.main_image = product.image
            primary_variant.save()
            print(f"Migrated main image for {product.name} to variant {primary_variant}")
            
        # 2. Migrate ProductImage gallery to ProductVariantImage
        product_gallery = product.images.all()
        for variant in variants:
            for p_img in product_gallery:
                # Check if it already exists to avoid duplicates
                if not ProductVariantImage.objects.filter(variant=variant, image=p_img.image).exists():
                    ProductVariantImage.objects.create(
                        variant=variant,
                        image=p_img.image,
                        alt_text=p_img.alt_text,
                        display_order=p_img.display_order
                    )
            print(f"Migrated gallery for variant {variant}")

if __name__ == "__main__":
    migrate_images()
