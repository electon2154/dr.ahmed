from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Review, PurchaseHistory, SiteReview, VisitorCounter
from .cart import CartManager
from .forms import ProductForm
import json


def search(request):
    """Search view for filtering products"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    
    # Start with available products
    products = Product.objects.filter(is_available=True)
    
    # Apply search query if provided
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Apply category filter if provided
    if category:
        products = products.filter(category__icontains=category)
    
    # Order by relevance (created_at for now)
    products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique categories for filter dropdown
    categories = Product.objects.filter(is_available=True).values_list('category', flat=True).distinct().order_by('category')
    
    context = {
        'current_page': 'search',
        'products': page_obj,
        'query': query,
        'category': category,
        'categories': categories,
        'total_results': products.count()
    }
    return render(request, 'search.html', context)

# Create your views here.

def home(request):
    # Track visitor
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # Record visitor if not already recorded today
    client_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check if this IP visited today
    from django.utils import timezone
    today = timezone.now().date()
    if not VisitorCounter.objects.filter(ip_address=client_ip, visit_date__date=today).exists():
        VisitorCounter.objects.create(
            ip_address=client_ip,
            user_agent=user_agent,
            page_visited='/'
        )
    
    # Get visitor statistics
    total_visitors = VisitorCounter.get_total_visitors()
    today_visitors = VisitorCounter.get_today_visitors()
    
    # Get site reviews
    site_reviews = SiteReview.objects.filter(is_approved=True)[:5]  # Latest 5 reviews
    
    # Calculate average site rating
    site_avg_rating = 0
    site_review_count = SiteReview.objects.filter(is_approved=True).count()
    if site_review_count > 0:
        total_rating = sum(review.rating for review in SiteReview.objects.filter(is_approved=True))
        site_avg_rating = round(total_rating / site_review_count, 1)
    
    # Get category filter from URL parameters
    category_filter = request.GET.get('category', '')
    
    # Get all available products
    all_products = Product.objects.filter(is_available=True)
    
    # Apply category filter if provided
    if category_filter:
        all_products = all_products.filter(category__icontains=category_filter)
    
    # Order by creation date
    all_products = all_products.order_by('-created_at')
    
    # Get unique categories for the category sections
    categories = Product.objects.filter(is_available=True).values_list('category', flat=True).distinct().order_by('category')
    
    context = {
        'current_page': 'home',
        'all_products': all_products,
        'categories': categories,
        'selected_category': category_filter,
        'total_visitors': total_visitors,
        'today_visitors': today_visitors,
        'site_reviews': site_reviews,
        'site_avg_rating': site_avg_rating,
        'site_review_count': site_review_count
    }
    return render(request, 'home.html', context)



def contact(request):
    context = {'current_page': 'contact'}
    return render(request, 'contact.html', context)

def about(request):
    context = {'current_page': 'about'}
    return render(request, 'about.html', context)  # Using home template for now

def product(request, product_id=None):
    if product_id:
        try:
            product_obj = get_object_or_404(Product, id=product_id)
            # Get reviews for this product
            reviews = Review.objects.filter(product=product_obj)
            # Get purchase count
            purchase_count = PurchaseHistory.objects.filter(product=product_obj).count()
            # Calculate average rating
            avg_rating = 0
            if reviews.exists():
                total_rating = sum(review.rating for review in reviews)
                avg_rating = round(total_rating / reviews.count(), 1)
        except:
            # If product not found, create a default product for demo
            product_obj = None
            reviews = []
            purchase_count = 0
            avg_rating = 0
    else:
        product_obj = None
        reviews = []
        purchase_count = 0
        avg_rating = 0
    
    context = {
        'current_page': 'product',
        'product': product_obj,
        'reviews': reviews,
        'purchase_count': purchase_count,
        'avg_rating': avg_rating,
        'review_count': len(reviews)
    }
    return render(request, 'product.html', context)

def cart(request):
    cart = CartManager(request)
    cart_items = cart.get_cart_items()
    total_price = cart.get_total_price()
    total_items = cart.get_total_items()
    
    context = {
        'current_page': 'cart',
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items
    }
    return render(request, 'cart.html', context)


@require_POST
@csrf_exempt
def add_to_cart(request):
    """AJAX endpoint to add product to cart"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = CartManager(request)
        cart.add(product, quantity)
        
        # Track purchase in history
        PurchaseHistory.objects.create(
            product=product,
            quantity=quantity,
            session_key=request.session.session_key,
            user=request.user if request.user.is_authenticated else None
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_total_items': len(cart),
            'cart_total_price': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@require_POST
@csrf_exempt
def remove_from_cart(request):
    """AJAX endpoint to remove product from cart"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id)
        cart = CartManager(request)
        cart.remove(product)
        
        return JsonResponse({
            'success': True,
            'message': 'Product removed from cart successfully',
            'cart_total_items': len(cart),
            'cart_total_price': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@require_POST
@csrf_exempt
def update_cart_quantity(request):
    """AJAX endpoint to update product quantity in cart"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        
        product = get_object_or_404(Product, id=product_id)
        cart = CartManager(request)
        cart.update_quantity(product, quantity)
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'cart_total_items': len(cart),
            'cart_total_price': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def get_cart_info(request):
    """AJAX endpoint to get current cart information"""
    cart = CartManager(request)
    return JsonResponse({
        'cart_total_items': len(cart),
        'cart_total_price': str(cart.get_total_price()),
        'cart_items': cart.get_cart_items()
    })


# Dashboard Views
def dashboard(request):
    """Dashboard view for product management"""
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    availability_filter = request.GET.get('availability', '')
    
    # Start with all products
    products = Product.objects.all().order_by('-created_at')
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply category filter
    if category_filter:
        products = products.filter(category__icontains=category_filter)
    
    # Apply availability filter
    if availability_filter == 'available':
        products = products.filter(is_available=True)
    elif availability_filter == 'unavailable':
        products = products.filter(is_available=False)
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_products = Product.objects.count()
    in_stock_products = Product.objects.filter(stock__gt=10).count()
    low_stock_products = Product.objects.filter(stock__lte=10, stock__gt=0).count()
    out_of_stock_products = Product.objects.filter(stock=0).count()
    
    # Get unique categories for filter dropdown
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')
    
    context = {
        'current_page': 'dashboard',
        'products': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
        'categories': categories,
        'total_products': total_products,
        'in_stock_products': in_stock_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    }
    return render(request, 'dashboard.html', context)


def add_product(request):
    """View for adding a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been added successfully!')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    context = {
        'current_page': 'dashboard',
        'form': form,
        'product': None
    }
    return render(request, 'product_form.html', context)


def edit_product(request, product_id):
    """View for editing an existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully!')
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'current_page': 'dashboard',
        'form': form,
        'product': product
    }
    return render(request, 'product_form.html', context)


@require_POST
@csrf_exempt
def delete_product(request, product_id):
    """AJAX endpoint for deleting a product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        product.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Product "{product_name}" has been deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting product: {str(e)}'
        }, status=400)


@require_POST
@csrf_exempt
def update_product_partial(request, product_id):
    """AJAX endpoint for partial product updates"""
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        
        # List of allowed fields for partial update
        allowed_fields = ['name', 'category', 'price', 'stock', 'discount', 'description', 'is_available']
        updated_fields = []
        
        for field, value in data.items():
            if field in allowed_fields and hasattr(product, field):
                # Type conversion and validation
                if field in ['price', 'discount']:
                    try:
                        value = float(value) if value else 0
                        if value < 0:
                            raise ValueError(f"{field} cannot be negative")
                    except (ValueError, TypeError):
                        return JsonResponse({
                            'success': False,
                            'message': f'Invalid {field} value. Must be a positive number.'
                        }, status=400)
                elif field == 'stock':
                    try:
                        value = int(value) if value else 0
                        if value < 0:
                            raise ValueError("Stock cannot be negative")
                    except (ValueError, TypeError):
                        return JsonResponse({
                            'success': False,
                            'message': 'Invalid stock value. Must be a positive integer.'
                        }, status=400)
                elif field == 'is_available':
                    value = bool(value)
                elif field in ['name', 'category', 'description']:
                    if not value or not value.strip():
                        return JsonResponse({
                            'success': False,
                            'message': f'{field.title()} cannot be empty.'
                        }, status=400)
                    value = value.strip()
                
                # Update the field
                setattr(product, field, value)
                updated_fields.append(field)
        
        if updated_fields:
            product.save()
            return JsonResponse({
                'success': True,
                'message': f'Product updated successfully. Updated fields: {", ".join(updated_fields)}',
                'updated_fields': updated_fields
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No valid fields provided for update.'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating product: {str(e)}'
        }, status=400)


@require_POST
@csrf_exempt
def submit_review(request):
    """AJAX endpoint to submit a product review"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        rating = int(data.get('rating'))
        comment = data.get('comment', '').strip()
        reviewer_name = data.get('reviewer_name', 'Anonymous').strip()
        
        # Validate input
        if not product_id or not rating or rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'message': 'Invalid product ID or rating.'
            }, status=400)
            
        if not comment:
            return JsonResponse({
                'success': False,
                'message': 'Comment is required.'
            }, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        
        # Create the review
        review = Review.objects.create(
            product=product,
            reviewer_name=reviewer_name if reviewer_name else 'Anonymous',
            rating=rating,
            comment=comment
        )
        
        # Calculate new average rating
        reviews = Review.objects.filter(product=product)
        avg_rating = 0
        if reviews.exists():
            total_rating = sum(r.rating for r in reviews)
            avg_rating = round(total_rating / reviews.count(), 1)
        
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review': {
                'id': review.id,
                'reviewer_name': review.reviewer_name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%B %d, %Y')
            },
            'avg_rating': avg_rating,
            'review_count': reviews.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error submitting review: {str(e)}'
        }, status=400)


def toggle_product_availability(request, product_id):
    """AJAX endpoint for toggling product availability"""
    try:
        product = get_object_or_404(Product, id=product_id)
        product.is_available = not product.is_available
        product.save()
        
        status = 'available' if product.is_available else 'unavailable'
        return JsonResponse({
            'success': True,
            'is_available': product.is_available,
            'message': f'Product "{product.name}" is now {status}.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating product: {str(e)}'
        }, status=400)


@require_POST
@csrf_exempt
def submit_site_review(request):
    """AJAX endpoint to submit site-wide review"""
    try:
        # Handle FormData from the form submission
        reviewer_name = request.POST.get('reviewer_name', '').strip()
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validate required fields
        if not rating or rating < 1 or rating > 5:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a valid rating (1-5 stars)'
            }, status=400)
        
        if not comment:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a comment'
            }, status=400)
        
        # Create the site review
        site_review = SiteReview.objects.create(
            reviewer_name=reviewer_name if reviewer_name else 'Anonymous',
            rating=rating,
            comment=comment,
            email=email if email else None
        )
        
        # Calculate new average rating
        site_reviews = SiteReview.objects.filter(is_approved=True)
        site_avg_rating = 0
        if site_reviews.exists():
            total_rating = sum(review.rating for review in site_reviews)
            site_avg_rating = round(total_rating / site_reviews.count(), 1)
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your review!',
            'review': {
                'id': site_review.id,
                'reviewer_name': site_review.reviewer_name,
                'rating': site_review.rating,
                'comment': site_review.comment,
                'created_at': site_review.created_at.strftime('%B %d, %Y')
            },
            'new_average': site_avg_rating,
            'review_count': site_reviews.count()
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': 'Invalid rating value'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while submitting your review'
        }, status=500)