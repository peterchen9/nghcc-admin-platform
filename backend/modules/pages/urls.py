from django.urls import path
from . import views

urlpatterns = [
    path('', views.page_detail, name='home'),
    path('p/<slug:slug>/', views.page_detail, name='page-detail'),
]
