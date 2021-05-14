from .models import Order


def get_or_set_order_session(request):
    order_id = request.session.get('order_id', None)

    if order_id is None:
        # Create an order if one has not been created already
        order = Order()
        order.save()
        request.session['order_id'] = order.id

    # if there already is an order id
    else:
        # get the order and make sure it is not already ordered
        try:
            order = Order.objects.get(id=order_id, ordered=False)
        except Order.DoesNotExist:
            order = Order()
            order.save()
            request.session['order_id'] = order.id

    # check if the user is authenticated and check if the order is associated with a user
    if request.user.is_authenticated and order.user is None:
        # assign the order user to the user that requested the order
        order.user = request.user
        order.save()
    return order
