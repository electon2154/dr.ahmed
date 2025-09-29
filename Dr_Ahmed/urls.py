"""
URL configuration for Dr_Ahmed project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    home, catalog, contact, about, product, cart, search,
    add_to_cart, remove_from_cart, update_cart_quantity, get_cart_info,
    dashboard, add_product, edit_product, delete_product, toggle_product_availability,
    update_product_partial
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('catalog/', catalog, name='catalog'),
    path('search/', search, name='search'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('product/<int:product_id>/', product, name='product'),
    path('product/', product, name='product_default'),
    path('cart/', cart, name='cart'),
    # AJAX Cart endpoints
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/remove/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/info/', get_cart_info, name='get_cart_info'),
    # Dashboard endpoints
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/add-product/', add_product, name='add_product'),
    path('dashboard/edit-product/<int:product_id>/', edit_product, name='edit_product'),
    path('dashboard/delete-product/<int:product_id>/', delete_product, name='delete_product'),
    path('dashboard/toggle-availability/<int:product_id>/', toggle_product_availability, name='toggle_product_availability'),
    path('dashboard/update-product/<int:product_id>/', update_product_partial, name='update_product_partial'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
