import uuid

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST

from .forms import OrderStatusForm, ReturnOrderForm
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
        order_id_input = request.POST.get("order_id", "").strip().upper()  # normalize input

        # Remove unwanted characters (quotes or spaces)
        order_id_input = order_id_input.replace("“", "").replace("”", "")

        # Expected format: GEARUP001
        if order_id_input.startswith("GEARUP"):
            try:
                seq_number = int(order_id_input.replace("GEARUP", ""))
                order = get_object_or_404(Order, sequential_number=seq_number)
            except (ValueError, Order.DoesNotExist):
                error = "Order not found. Please check your Order ID."
        else:
            error = "Invalid Order ID format. Example: GEARUP001"

    return render(request, "registration/orders/track_orders.html", {
        "order": order,
        "error": error
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'registration/orders/order_details.html', {'order': order})




# @login_required
# def checkout(request):
#     cart = Cart.objects.filter(user=request.user).first()
#     addresses = request.user.addresses.all()

#     if not cart or not cart.items.exists():
#         messages.warning(request, "Your cart is empty.")
#         return redirect('view_cart')

#     if request.method == 'POST':
#         address_id = request.POST.get('address_id')
#         address = Address.objects.get(id=address_id, user=request.user)

#         total = sum(item.product.price * item.quantity for item in cart.items.all())

#         # Create Order
#         order = Order.objects.create(
#             user=request.user,
#             total_price=total,
#             status='PLACED',
#             address=address,
#         )

#         # Add items
#         for item in cart.items.all():
#             price = item.variant.price if item.variant else item.product.price
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 variant=item.variant,  # store selected variant
#                 quantity=item.quantity,
#                 price=price,
#             )
#             # Reduce stock from variant if selected, else from product
#             if item.variant:
#                 item.variant.stock -= item.quantity
#                 item.variant.save()
#             else:
#                 item.product.stock -= item.quantity
#                 item.product.save()

#         # Clear cart
#         cart.items.all().delete()

#         messages.success(request, "Order placed successfully!")
#         return redirect('order_detail', order_id=order.order_id)

#     return render(request, 'registration/orders/checkout.html', {
#         'cart': cart,
#         'addresses': addresses
#     })

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

@login_required
def order_success(request):
    return render(request, 'registration/orders/order_success.html')

@login_required
def checkout(request):
    """
    Handles checkout page display (GET) and order placement (POST).
    """
    cart = Cart.objects.filter(user=request.user).first()
    addresses = request.user.addresses.all()

    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')

    if request.method == "POST":
        # Get selected address
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, "Please select an address.")
            return redirect('checkout')

        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, "Selected address not found.")
            return redirect('checkout')

        # Calculate total price
        total = 0
        for item in cart.items.all():
            price = item.variant.price if item.variant else item.product.price
            total += price * item.quantity

        # Create Order
        order = Order.objects.create(
            user=request.user,
            total_price=total,
            status='PLACED',
            address=address,
        )

        # Create Order Items and update stock
        for item in cart.items.all():
            price = item.variant.price if item.variant else item.product.price

            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=price,
            )

            # Update stock
            if item.variant:
                item.variant.stock -= item.quantity
                item.variant.save()
            else:
                item.product.stock -= item.quantity
                item.product.save()

        # Clear cart
        cart.items.all().delete()

        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_success')  # redirect to success page

    # Handle GET: Show checkout page
    return render(request, 'registration/orders/checkout.html', {
        'cart': cart,
        'addresses': addresses
    })

@login_required
@require_POST
def cancel_order(request, order_id):
    """
    Allows the user to cancel their order if it's still cancellable.
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    # Only allow cancellation if status is PENDING or PLACED
    if order.status not in ['PENDING', 'PLACED']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('order_detail', order_id=order.order_id)

    # Restore stock
    for item in order.items.all():
        if item.variant:
            item.variant.stock += item.quantity
            item.variant.save()
        else:
            item.product.stock += item.quantity
            item.product.save()

    # Update order status
    order.status = 'CANCELLED'
    order.save()

    messages.success(request, f"Order #{order.order_id} has been cancelled successfully!")
    return redirect('order_detail', order_id=order.order_id)

@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    # Only allow return if delivered and no return already requested
    if order.status != 'DELIVERED' or order.return_status != 'NONE':
        messages.error(request, "This order cannot be returned.")
        return redirect('order_detail', order_id=order.order_id)

    if request.method == 'POST':
        form = ReturnOrderForm(request.POST)
        if form.is_valid():
            order.return_reason = form.cleaned_data['reason']
            order.return_status = 'REQUESTED'
            order.save()
            messages.success(request, "Your return request has been submitted successfully!")
            return redirect('order_detail', order_id=order.order_id)
    else:
        form = ReturnOrderForm()

    return render(request, 'registration/orders/return_order.html', {'order': order, 'form': form})


@staff_member_required
def admin_return_requests(request):
    """
    View all return requests for admin to approve or reject.
    """
    orders = Order.objects.filter(return_status='REQUESTED').order_by('-created_at')
    return render(request, 'custom_admin/return_request.html', {'orders': orders})

@staff_member_required
def admin_return_detail(request, order_id):
    """
    Show details of a return request and allow approve/reject actions.
    """
    order = get_object_or_404(Order, order_id=order_id, return_status='REQUESTED')

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            order.approve_return()
            messages.success(request, f"Return approved for Order #{order.order_number}. Stock restored.")
            return redirect('admin_return_requests')
        elif action == "reject":
            order.reject_return()
            messages.warning(request, f"Return rejected for Order #{order.order_number}.")
            return redirect('admin_return_requests')

    return render(request, 'custom_admin/return_detail.html', {'order': order})

@staff_member_required
def admin_return_action(request, order_id, action):
    """
    Approve or reject return requests.
    """
    order = get_object_or_404(Order, order_id=order_id)

    if order.return_status != 'REQUESTED':
        messages.error(request, "This order does not have a pending return request.")
        return redirect('admin_return_requests')

    if action == 'approve':
        order.approve_return()
        messages.success(request, f"Return approved and stock restored for Order #{order.order_id}.")
    elif action == 'reject':
        order.reject_return()
        messages.warning(request, f"Return request rejected for Order #{order.order_id}.")
    else:
        messages.error(request, "Invalid action.")

    return redirect('admin_return_requests')



