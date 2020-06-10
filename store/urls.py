from . import views
from django.urls import path

# app_name = 'store'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home-page'),
    path('product/<slug>', views.ItemDetailView.as_view(), name='product-page'),
    path('add-to-cart/<slug>', views.add_to_cart, name='add-to-cart'),
    path('add-item-to-cart/<slug>',
         views.add_single_item_to_cart, name='add-item-to-cart'),
    path('remove-from-cart/<slug>',
         views.remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>',
         views.remove_single_item_from_cart, name='remove-item-from-cart'),
    path('remove-at-checkout/<slug>',
         views.remove_item_at_checkout, name='remove-at-checkout'),
    path('order-summary/', views.OrderSummaryView.as_view(),
         name='order-summary-page'),
    path('add_coupon/', views.AddCouponView.as_view(), name='add-coupon'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout-page'),
    path('payment/<payment_option>/',
         views.PaymentView.as_view(), name='payment-page'),
    path('request-refund/',
         views.RequestRefundView.as_view(), name='request-refund')
]
