from django.urls import path
from . import views

app_name = 'core'  # Important for namespacing

urlpatterns = [
    # Main pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('programs/', views.programs_view, name='programs'),
    path('contact/', views.contact_view, name='contact'),
    
    # Team member detail
    
]