import uuid

from django.db import models
from django.utils.text import slugify
from image_cropping.fields import ImageCropField
from image_cropping import ImageRatioField
from django.db.models import Sum


class Category(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True, blank=True)

	class Meta:
		verbose_name_plural = "Categories"

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug=slugify(self.name)
		super().save(*args,**kwargs)

	def __str__(self):
		return self.name


class Product(models.Model):
	product_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
	cropping = ImageRatioField('image', '300x300') 
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True, blank=True)
	description = models.TextField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField(default=0) 
	image = models.ImageField(upload_to="products")
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	is_active = models.BooleanField(default=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args,**kwargs)
	
	def __str__(self):
		return self.name

	@property
	def total_stock(self):
		"""Sum of all variant stocks, or fallback to product stock."""
		if self.variants.exists():
			return self.variants.aggregate(total=Sum('stock'))['total'] or 0
		return self.stock

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='additional_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/additional')

    def __str__(self):
    	return self.product.name

class Variant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"

