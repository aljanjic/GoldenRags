from django.urls import path
from . import views

urlpatterns = [
    path('goldenrags/scrape/', views.scrape_view , name='scrape'),
]
