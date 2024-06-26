from django import forms

class ScrapeForm(forms.Form):
    product_url = forms.URLField(label='Product URL', required=True)
    item_color = forms.CharField(label='Item Color', required=True)
    item_size = forms.CharField(label='Item Size', required=True)
    receivers_email = forms.CharField(label='Email for notification', required=True) # Remove False after finish testing
    send_sms = forms.BooleanField(label='WhatsApp notifications are available for Premium users only', required=False)
    phone_number = forms.CharField(label='WhatsApp number', required=False)