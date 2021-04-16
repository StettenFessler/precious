from django.views import generic
from .models import Product


class ProductListView(generic.ListView):
    # links this view to the html for it
    template_name = 'product_list.html'
    # links this view to the model for it
    queryset = Product.objects.all()
