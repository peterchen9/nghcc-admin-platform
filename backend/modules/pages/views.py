from django.shortcuts import render, get_object_or_404
from .models import Page

def page_detail(request, slug='home'):
    # Default to 'home' if no slug is provided
    page = Page.objects.filter(slug=slug, is_active=True).first()
    return render(request, 'pages/page_detail.html', {'page': page, 'slug': slug})
