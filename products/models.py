import uuid

from django.db import models
from django.utils.text import slugify


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
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True, blank=True)
	description = models.TextField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField() 
	image = models.ImageField(upload_to="products")
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	is_active = models.BooleanField(default=True)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args,**kwargs)
	
	def __str__(self):
		return self.name

