"""
URL configuration for victoryteens project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from core.views import home_view, about_view, contact_view, programs_view, volunteer_view, team_member_detail
from users.views import dashboard_view, profile_view


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('vicadmin/', admin.site.urls),

    path('', home_view, name='home'),
    path('volunteer/', volunteer_view, name='volunteer'),
    path('programs/', programs_view, name='programs'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    path('team/<int:member_id>/', team_member_detail, name='team_member_detail'),

    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    
    
    path('blog/', include('blog.urls')),

    path("__reload__/", include("django_browser_reload.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)