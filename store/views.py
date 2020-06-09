from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, View
from django.utils import timezone

from .forms import CheckoutForm, CouponForm
from .models import Item, Order, OrderItem, BillingAddress, Payment, Coupon

# Create your views here.


import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


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
            messages.warning(self.request, "You do not have an active order")
            return redirect('home-page')


class CheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect('home-page')
        context = {
            'form': form,
            'order': order,
            'couponform': CouponForm(),
            'DISPLAY_COUPON_FORM': True}
        return render(self.request, 'store/checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect('home-page')
        if form.is_valid():
            street_address = form.cleaned_data.get('street_address')
            apartment_address = form.cleaned_data.get('apartment_address')
            country = form.cleaned_data.get('country')
            zip_code = form.cleaned_data.get('zip_code')
            # TODO: add functionality for these fields
            # same_shipping_address = form.cleaned_data.get(
            #     'same_shipping_address')
            # save_info = form.cleaned_data.get('save_info')
            payment_option = form.cleaned_data.get('payment_option')
            billing_address = BillingAddress(
                user=self.request.user,
                street_address=street_address,
                apartment_address=apartment_address,
                country=country,
                zip_code=zip_code
            )
            billing_address.save()
            order.billing_address = billing_address
            order.save()

            if payment_option == 'S':
                return redirect('payment-page', payment_option='stripe')
            elif payment_option == 'P':
                return redirect('payment-page', payment_option='paypal')
            else:
                messages.warning(self.request, 'Invalid payment option')
                return redirect('checkout-page')

        messages.warning(self.request, 'Failed checkout')
        return redirect('checkout-page')


class PaymentView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'stripe_key': settings.STRIPE_PUBLIC_KEY,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, 'store/payment.html', context)
        else:
            messages.warning(self.request,
                             'Please fill out the checkout form properly before proceeding to payment')
            return redirect('checkout-page')

    def post(self, *args, **kwargs):
        order = Order.objects.get(
            user=self.request.user,
            ordered=False
        )
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_order_total() * 100)

        try:
            # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
                amount=amount,   # cents
                currency="inr",
                source=token
            )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_order_total()
            payment.save()

            # update the ordered items
            order_items = order.items.all()
            order_items.update(ordered=True)
            map(lambda item: item.save(), order_items)

            # assign the payment to the order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, 'Your order was successful')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f'{err.get("message")}')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, 'Rate Limit Error')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, 'Invalid parameters')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, 'Not authenticated')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, 'Network error')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(
                self.request, 'Something went wrong. You were not charged. Please try again')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(
                self.request, 'Something went wrong. You were not charged. We are working on this')

        finally:
            return redirect('home-page')


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


def get_coupon(request, code):
    try:
        return Coupon.objects.get(code=code)
    except ObjectDoesNotExist:
        messages.warning('Invalid coupon code')
        return redirect(request, 'checkout-page')


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = Coupon.objects.get(code=code)
                order.save()
                messages.success(self.request, 'Successfully applied Coupon')
            except ObjectDoesNotExist:
                messages.warning(
                    self.request, 'You do not have an active order')
            return redirect('checkout-page')
