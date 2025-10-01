from .cart import CartManager

def cart_context(request):
    """Context processor to make cart data available in all templates"""
    cart = CartManager(request)
    cart_total_items = cart.get_total_items()
    
    return {
        'cart_total_items': cart_total_items,
        'cart_has_items': cart_total_items > 0,
    }