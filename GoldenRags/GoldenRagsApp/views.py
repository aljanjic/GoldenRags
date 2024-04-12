from django.shortcuts import render, redirect
from .forms import ScrapeForm
import re
from .tasks import get_rags_async  
from django.contrib import messages

def scrape_view(request):
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            product_url = form.cleaned_data['product_url']
            item_color = form.cleaned_data['item_color'].strip()
            item_size = form.cleaned_data['item_size'].upper()
            send_sms = form.cleaned_data['send_sms']       
            phone_number = form.cleaned_data['phone_number']
            receivers_email = form.cleaned_data['receivers_email']

            product_name = ''
            match = re.search(r"/([^/]+)-p\d+\.html", product_url)
            if match:
                product_name = match.group(1).replace("-", " ").upper()

            messages.success(request, 'Form has been submitted successfully.')
            get_rags_async.delay(product_url, item_color, item_size, send_sms, phone_number, receivers_email, product_name)
            return redirect('scrape')
            
    else:
        form = ScrapeForm()
    return render(request, 'GoldenRagsApp/index.html', {'form': form})
