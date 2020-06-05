from . import views
from django.urls import path

# app_name = 'store'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home-page'),
    path('product/<slug>', views.ItemDetailView.as_view(), name='product-page'),
    path('add-to-cart/<slug>', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>',
         views.remove_from_cart, name='remove-from-cart'),
    path('checkout/', views.checkout_page, name='checkout-page')
]
