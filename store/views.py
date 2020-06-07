from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, View
from django.utils import timezone

from .models import Item, Order, OrderItem

# Create your views here.


class HomeView(ListView):
    template_name = 'store/home.html'
    model = Item
    context_object_name = 'items'

    paginate_by = 12


class ItemDetailView(DetailView):
    model = Item
    template_name = 'store/product.html'
    context_object_name = 'item'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'order': order
            }
            return render(self.request, 'store/order-summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect('home-page')


@login_required
def checkout_page(request):
    context = {}
    #     'items': Item.objects.all()
    # }
    return render(request, 'store/checkout.html', context)


def add_order_item(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        user=request.user,
        item=item,
        ordered=False)
    order, created = Order.objects.get_or_create(
        user=request.user,
        ordered=False,
        defaults={'ordered_date': timezone.now()})
    if order.items.filter(item=item).exists():
        order_item.quantity += 1
        messages.info(request,
                      'Item updated')
    else:
        order_item.quantity = 1
        order.items.add(order_item)
        messages.info(
            request, 'This item has been added to your cart')
    order_item.save()


@login_required
def add_to_cart(request, slug):
    add_order_item(request, slug)
    return redirect('product-page', slug=slug)


@login_required
def add_single_item_to_cart(request, slug):
    add_order_item(request, slug)
    return redirect('order-summary-page')


def remove_order_item(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item=item).exists():
            order_item = OrderItem.objects.filter(
                user=request.user,
                item=item,
                ordered=False
            )[0]
            if 'item' in request.get_full_path() and order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, 'Item updated')
            else:
                order.items.remove(order_item)
                messages.info(
                    request, 'Item has been removed from your cart')
        else:
            messages.info(
                request, 'This item was not in your cart')
    else:
        messages.info(
            request, 'You do not have an active order')


@login_required
def remove_from_cart(request, slug):
    remove_order_item(request, slug)
    return redirect('product-page', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    remove_order_item(request, slug)
    return redirect('order-summary-page')


@login_required
def remove_item_at_checkout(request, slug):
    remove_order_item(request, slug)
    return redirect('order-summary-page')
