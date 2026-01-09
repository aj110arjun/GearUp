import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GearUp.settings')
django.setup()

from common.products.models import Product, ProductVariant, ProductImage

def migrate_images():
    print("Starting image migration...")
    
    # 1. Migrate Product.image to first variant
    products = Product.objects.all()
    for product in products:
        # Check if product has an image (using raw field access if possible, or just checking if it exists)
        # Note: Since the field is removed from model, we might need to use a historical migration 
        # or have done this BEFORE removing the field.
        # However, if the user hasn't run migrations yet, the field STILL EXISTS in the database.
        
        try:
            # We use raw SQL to get the image because the model field is gone
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT image FROM products_product WHERE id = %s", [str(product.id)])
                row = cursor.fetchone()
                product_image = row[0] if row else None
            
            if product_image:
                first_variant = product.variants.first()
                if first_variant and not first_variant.primary_image:
                    first_variant.primary_image = product_image
                    first_variant.save()
                    print(f"Migrated main image for product: {product.name}")
        except Exception as e:
            print(f"Error migrating main image for {product.name}: {e}")

    # 2. Migrate ProductImage records
    # 2. Migrate ProductImage records using raw SQL since the 'product' field is being removed from the model
    from django.db import connection
    with connection.cursor() as cursor:
        # Check if products_productimage table still has product_id column
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products_productimage' AND column_name='product_id'")
        if cursor.fetchone():
            cursor.execute("SELECT id, product_id FROM products_productimage WHERE variant_id IS NULL AND product_id IS NOT NULL")
            rows = cursor.fetchall()
            for img_id, prod_id in rows:
                product = Product.objects.get(id=prod_id)
                first_variant = product.variants.first()
                if first_variant:
                    ProductImage.objects.filter(id=img_id).update(variant=first_variant)
                    print(f"Migrated ProductImage {img_id} to variant of {product.name}")
                else:
                    print(f"No variant found for ProductImage {img_id} (Product: {product.name})")
        else:
            print("product_id column already removed from products_productimage. Skipping ProductImage migration.")

    print("Migration complete!")

if __name__ == "__main__":
    migrate_images()
