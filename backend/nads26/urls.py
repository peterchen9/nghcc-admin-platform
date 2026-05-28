"""
URL configuration for nads26 project.

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
from modules.humnos import views as humnos_views
from modules.hymns import views as hymns_views
from nads26.health import health_check

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('users/', include('modules.accounts.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('api/humnos/', include('modules.humnos.api_urls')),
    path('api/hymns/', include('modules.hymns.api_urls')),
    path('hymn_resources/htm/<str:filename>', hymns_views.serve_htm_resource, name='serve-htm-resource'),
    path('worship/hymns/', hymns_views.hymns_page_view, name='hymns-page'),
    path('hymns/', hymns_views.hymns_page_view, name='hymns-page-direct'),
    path('webav/', humnos_views.humnos_page_view, name='webav'),
    path('eureka/', include('modules.eureka.urls')),
    path('', include('modules.pages.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
