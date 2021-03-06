from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.shortcuts import reverse
from django.utils.text import slugify

User = get_user_model()


class Address(models.Model):
    # we use a tuple of choices so we don't need multiple address models
    ADDRESS_CHOICES = (
        ('B', 'Billing'),
        ('S', 'Shipping'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    # allows users to select their default address without having to select a new one each time
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}"

    class Meta:
        # ensures correct plural of address is used
        verbose_name_plural = 'Addresses'


class Product(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    # price will be set in cents
    price = models.IntegerField(default=0)
    image = models.ImageField(upload_to='product_images')
    # stores the date the product was created
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    # filters out inactive products
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cart:product-detail", kwargs={'slug': self.slug})

    # gets the price to display
    def get_price(self):
        # price will always be display with 2 decmials
        # divide by 100 so that cents is converted into dollars
        return "{:.2f}".format(self.price / 100)

# these are products that have been added to the cart


class OrderItem(models.Model):
    # links an order item to a specfic order
    order = models.ForeignKey(
        "Order", related_name='items', on_delete=models.CASCADE)
    # on delete ensures that an item that has been deleted from the website cannot be added to the cart
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # must be = 1 otherwise not in cart
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_raw_total_item_price(self):
        return self.quantity * self.product.price

    def get_total_item_price(self):
        price = self.get_raw_total_item_price()  # this will be in cents
        return "{:.2f}".format(price / 100)  # convert cents value to dollars


# all of the OrderItems within the cart
class Order(models.Model):
    # if user is deleted, there won't be any orders for that user
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE)
    # stores the date the order was created
    start_date = models.DateTimeField(auto_now_add=True)
    # stores the date an order was payed for
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)

    # every order is linked to an address
    # note: if an address is deleted, we don't want to delete the order history. Hence the address is set to null upon deletion
    billing_address = models.ForeignKey(
        Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.reference_number

    # the unique number that is used to identify an order
    @ property
    def reference_number(self):
        return f"ORDER-{self.pk}"

    def get_raw_subtotal(self):
        total = 0
        # sums all items in cart
        for order_item in self.items.all():
            total += order_item.get_raw_total_item_price()
        return total

    def get_subtotal(self):
        subtotal = self.get_raw_subtotal()  # this will be in cents
        # convert cents value to dollars
        return "{:.2f}".format(subtotal / 100)

    def get_raw_total(self):
        subtotal = self.get_raw_subtotal()
        # add tax, add delivery, subtract discounts
        # total = subtotal - discounts + tax + delivery
        tax = .0725 * subtotal
        subtotal += tax
        return subtotal

    def get_total(self):
        total = self.get_raw_subtotal()  # this will be in cents
        # convert cents value to dollars
        return "{:.2f}".format(total / 100)

# records all of the attempted payments on an order


class Payment(models.Model):
    # every payment is linked to an order
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(
        ('Paypal', 'Paypal'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField()
    # stores the actual response from the PayPal API (error message, status code, etc.)
    raw_response = models.TextField()

    def __str__(self):
        return self.reference_number

    # self.order gives the order reference #. self.pk is the payment ID
    @ property
    def reference_number(self):
        return f"PAYMENT-{self.order}-{self.pk}"


def pre_save_product_receiver(sender, instance, *args, **kwargs):
    # if a slug is not set for a product
    if not instance.slug:
        # create a slug from the title automatically
        instance.slug = slugify(instance.title)


pre_save.connect(pre_save_product_receiver, sender=Product)
