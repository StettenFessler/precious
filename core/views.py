from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import reverse
from django.views import generic
from .forms import ContactForm


class HomeView(generic.TemplateView):
    template_name = 'index.html'


class ContactView(generic.FormView):
    form_class = ContactForm
    template_name = 'contact.html'

    # will redirect back to contact form after message sent
    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        # displays message after form has been correctly filled out
        messages.info(
            self.request, "Thank you for getting in touch. We have received your message.")

        # uses variables set in forms.py to get input
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        message = form.cleaned_data.get('message')

        # the format of the actual message that will be sent to us
        full_message = f"""
            Received message below from {name}, {email}
            ________________________________________________

            {message}
            """
        send_mail(
            subject="Received contact form submission",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NOTIFY_EMAIL]

        )
        return super(ContactView, self).form_valid(form)
