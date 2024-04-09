from django.urls import path
from . import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('goldenrags/', RedirectView.as_view(url='/goldenrags/scrape/'), name='go-to-scrape'),
    path('goldenrags/scrape/', views.scrape_view , name='scrape'),
]
