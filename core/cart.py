from decimal import Decimal
from django.conf import settings
from .models import Product, Cart, CartItem


class CartManager:
    """
    Session-based cart management system
    """
    
    def __init__(self, request):
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None
        
        # Initialize cart in session if it doesn't exist
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
    
    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.get_discounted_price())
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        self.save()
    
    def save(self):
        """
        Mark the session as modified to make sure it gets saved
        """
        self.session.modified = True
    
    def remove(self, product):
        """
        Remove a product from the cart
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def update_quantity(self, product, quantity):
        """
        Update the quantity of a product in the cart
        """
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity <= 0:
                self.remove(product)
            else:
                self.cart[product_id]['quantity'] = quantity
                self.save()
    
    def get_total_price(self):
        """
        Calculate the total price of all items in the cart
        """
        return sum(Decimal(item['price']) * item['quantity'] 
                  for item in self.cart.values())
    
    def get_total_items(self):
        """
        Get the total number of items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())
    
    def clear(self):
        """
        Remove cart from session
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()
    
    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        
        for product in products:
            cart[str(product.id)]['product'] = product
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item
    
    def __len__(self):
        """
        Count all items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_cart_items(self):
        """
        Get all cart items with product information
        """
        items = []
        for item in self:
            items.append({
                'product': item['product'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price']
            })
        return items
    
    def sync_with_database(self):
        """
        Sync session cart with database cart for authenticated users
        """
        if not self.user:
            return
        
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(
            user=self.user,
            defaults={'session_key': self.session.session_key}
        )
        
        # Clear existing cart items
        cart.items.all().delete()
        
        # Add items from session to database
        for item in self:
            CartItem.objects.create(
                cart=cart,
                product=item['product'],
                quantity=item['quantity']
            )
    
    def load_from_database(self):
        """
        Load cart from database for authenticated users
        """
        if not self.user:
            return
        
        try:
            cart = Cart.objects.get(user=self.user)
            # Clear session cart
            self.cart.clear()
            
            # Load items from database to session
            for item in cart.items.all():
                self.cart[str(item.product.id)] = {
                    'quantity': item.quantity,
                    'price': str(item.product.get_discounted_price())
                }
            self.save()
        except Cart.DoesNotExist:
            pass