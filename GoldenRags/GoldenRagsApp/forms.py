from django import forms

class ScrapeForm(forms.Form):
    product_url = forms.URLField(label='Product URL')
    item_color = forms.CharField(label='Item Color')
    item_size = forms.CharField(label='Item Size')
    receivers_email = forms.CharField(label='Email for notification')
    send_sms = forms.BooleanField(label='Send SMS', required=False)
    phone_number = forms.CharField(label='Phone for SMS', required=False)