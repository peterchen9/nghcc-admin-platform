from django.urls import path
from . import views

urlpatterns = [
    path('', views.page_detail, name='home'),
    path('pages/edit-home/', views.edit_home, name='edit-home'),
    path('p/<slug:slug>/', views.page_detail, name='page-detail'),
]
