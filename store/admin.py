from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered']


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'ordered']


# Register your models here.
admin.site.register(Item)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
