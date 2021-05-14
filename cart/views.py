from django.shortcuts import get_object_or_404, reverse, redirect
from django.views import generic
from .forms import AddToCartForm
from .models import Product, OrderItem
from .utils import get_or_set_order_session


class ProductListView(generic.ListView):
    # links this view to the html for it
    template_name = 'product_list.html'
    # links this view to the model for it
    queryset = Product.objects.all()


class ProductDetailView(generic.FormView):
    template_name = 'cart/product_detail.html'
    form_class = AddToCartForm

    def get_object(self):
        # return the product that we are getting
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("home")  # TODO: cart

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        # get the product
        product = self.get_object()

        # check if the item is already in the cart
        item_filter = order.items.filter(product=product)
        # if an item is already in the cart, increase the quantity of that item
        if item_filter.exists():
            item = item_filter.first()
            item.quantity += int(form.cleaned_data['quantity'])
            item.save()

        # if the item is not already in the cart, add it to the cart
        else:
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()

        return super(ProductDetailView, self).form_valid(form)

    # displays product info in the product detail view
    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['product'] = self.get_object()
        return context


class CartView(generic.TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

# increments quantity, then redirects back to the cart


class IncreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()
        return redirect("cart:summary")


class DecreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])

        # if quantity <= 1, delete when decremented
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()
        return redirect("cart:summary")


class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("cart:summary")
