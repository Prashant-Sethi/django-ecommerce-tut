from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon, Refund


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update refund requests'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ordered',
        'coupon',
        'payment',
        'billing_address',
        'shipped',
        'delivered',
        'refund_requested',
        'refund_granted'
    ]

    list_display_links = [
        'user',
        'billing_address',
        'payment',
        'coupon'
    ]

    list_filter = [
        'ordered',
        'shipped',
        'delivered',
        'refund_requested',
        'refund_granted'
    ]

    search_fields = [
        'user__username',
        'ref_code'
    ]

    actions = [make_refund_accepted]


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'ordered']


# Register your models here.
admin.site.register(Item)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
