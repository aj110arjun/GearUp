import uuid

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError

from .forms import OrderStatusForm
from cart.models import Cart
from address.models import Address
from .models import Order, OrderItem
from products.models import Variant


@login_required
def view_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'registration/orders/order_history.html', {'orders': orders})


def track_orders(request):
    error = None
    order = None

    if request.method == "POST":
        order_id_input = request.POST.get("order_id", "").strip().replace("“", "").replace("”", "")
        try:
            order_uuid = uuid.UUID(order_id_input)
            order = get_object_or_404(Order, order_id=order_uuid)
        except (ValueError, ValidationError):
            error = "Invalid Order ID"

    return render(request, "registration/orders/track_orders.html", {
        "order": order,
        "error": error
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'registration/orders/order_details.html', {'order': order})




@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    addresses = request.user.addresses.all()

    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = Address.objects.get(id=address_id, user=request.user)

        total = sum(item.product.price * item.quantity for item in cart.items.all())

        # Create Order
        order = Order.objects.create(
            user=request.user,
            total_price=total,
            status='PLACED',
            address=address,
        )

        # Add items
        for item in cart.items.all():
            price = item.variant.price if item.variant else item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,  # store selected variant
                quantity=item.quantity,
                price=price,
            )
            # Reduce stock from variant if selected, else from product
            if item.variant:
                item.variant.stock -= item.quantity
                item.variant.save()
            else:
                item.product.stock -= item.quantity
                item.product.save()

        # Clear cart
        cart.items.all().delete()

        messages.success(request, "Order placed successfully!")
        return redirect('order_detail', order_id=order.order_id)

    return render(request, 'registration/orders/checkout.html', {
        'cart': cart,
        'addresses': addresses
    })

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/order_list.html', {'orders': orders})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        # Update status
        if 'status' in request.POST:
            form = OrderStatusForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, f"Order #{order.order_id} status updated!")
                return redirect('admin_order_detail', order_id=order_id)

        # Update variant
        if 'item_id' in request.POST and 'variant_id' in request.POST:
            item_id = request.POST['item_id']
            variant_id = request.POST['variant_id']
            item = get_object_or_404(OrderItem, id=item_id, order=order)

            if variant_id:
                variant = get_object_or_404(Variant, id=variant_id)
                item.variant = variant
                item.price = variant.price  # update price
            else:
                item.variant = None
                item.price = item.product.price

            item.save()

            # Update order total
            order.total_price = sum(i.subtotal() for i in order.items.all())
            order.save()

            messages.success(request, f"Variant updated for {item.product.name}!")
            return redirect('admin_order_detail', order_id=order_id)

    form = OrderStatusForm(instance=order)

    return render(request, 'custom_admin/order_detail.html', {
        'order': order,
        'form': form,
    })



