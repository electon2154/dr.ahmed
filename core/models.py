from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=100)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def get_discounted_price(self):
        if self.discount and self.discount > 0:
            # Calculate percentage discount
            discount_amount = (self.price * self.discount) / 100
            return self.price - discount_amount
        return self.price
    
    def get_discount_percentage(self):
        """Return the discount as a percentage for display purposes"""
        return self.discount if self.discount else 0


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart {self.session_key}"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        return self.quantity * self.product.get_discounted_price()


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=100, default='Anonymous')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer_name} - {self.rating} stars for {self.product.name}"


class PurchaseHistory(models.Model):
    product = models.ForeignKey(Product, related_name='purchases', on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-purchase_date']
    
    def __str__(self):
        buyer = self.user.username if self.user else f"Anonymous ({self.session_key})"
        return f"{buyer} purchased {self.quantity} x {self.product.name}"


class SiteReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    reviewer_name = models.CharField(max_length=100, default='Anonymous')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)  # For moderation if needed
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer_name} - {self.rating} stars for website"


class VisitorCounter(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    visit_date = models.DateTimeField(auto_now_add=True)
    page_visited = models.CharField(max_length=200, default='/')
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"Visit from {self.ip_address} on {self.visit_date.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_total_visitors(cls):
        """Get total unique visitors"""
        return cls.objects.values('ip_address').distinct().count()
    
    @classmethod
    def get_today_visitors(cls):
        """Get today's unique visitors"""
        from django.utils import timezone
        today = timezone.now().date()
        return cls.objects.filter(visit_date__date=today).values('ip_address').distinct().count()
