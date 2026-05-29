from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Page

def page_detail(request, slug='home'):
    # Default to 'home' if no slug is provided
    page = Page.objects.filter(slug=slug, is_active=True).first()
    return render(request, 'pages/page_detail.html', {'page': page, 'slug': slug})

@login_required
def edit_home(request):
    if not request.user.is_superuser:
        raise PermissionDenied("您無權進行此操作。")
    page, created = Page.objects.get_or_create(
        slug='home',
        defaults={
            'title': '首頁',
            'content': '<h1>歡迎使用北門行政平台</h1>',
            'is_active': True,
        },
    )
    return redirect(f'/admin/pages/page/{page.id}/change/')
