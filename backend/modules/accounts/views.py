import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from modules.menu.models import MenuItem

def _active_menu_items():
    return MenuItem.objects.filter(is_active=True)

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied("您無權進行此操作。")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@admin_required
def user_list(request):
    users = User.objects.all().select_related('profile').prefetch_related('profile__allowed_menu_items').order_by('id')
    return render(request, 'accounts/user_list.html', {'users': users})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def app_routes(request):
    if not request.user.is_superuser:
        return Response({'detail': 'Permission denied.'}, status=403)
        
    roots = MenuItem.objects.filter(parent=None, is_active=True).prefetch_related('children')
    data = []
    for r in roots:
        children_data = []
        for c in r.children.filter(is_active=True):
            children_data.append({
                'id': c.id,
                'title': c.title,
                'route': c.route,
            })
        data.append({
            'id': r.id,
            'title': r.title,
            'route': r.route,
            'children': children_data
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_create(request):
    if not request.user.is_superuser:
        return Response({'detail': 'Permission denied.'}, status=403)
        
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    display_name = request.data.get('display_name', '').strip()
    email = request.data.get('email', '').strip()
    department = request.data.get('department', '').strip()
    role = request.data.get('role', '').strip()
    is_active = request.data.get('is_active', True)
    is_staff = request.data.get('is_staff', True)

    if not username or not password:
        return Response({'error': '帳號與密碼為必填欄位'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': '此帳號已存在'}, status=400)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_active=is_active,
        is_staff=is_staff,
    )
    
    profile = user.profile
    profile.display_name = display_name
    profile.department = department
    profile.role = role
    profile.allowed_menu_items.set(_active_menu_items())
    profile.save()

    return Response({'status': 'success', 'user_id': user.id})

@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def user_update(request, pk):
    if not request.user.is_superuser:
        return Response({'detail': 'Permission denied.'}, status=403)
        
    user = get_object_or_404(User, pk=pk)
    
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    display_name = request.data.get('display_name', '').strip()
    email = request.data.get('email', '').strip()
    department = request.data.get('department', '').strip()
    role = request.data.get('role', '').strip()
    is_active = request.data.get('is_active', True)
    is_staff = request.data.get('is_staff', user.is_staff)

    if username and username != user.username:
        if User.objects.filter(username=username).exclude(pk=pk).exists():
            return Response({'error': '此帳號已存在'}, status=400)
        user.username = username

    if password:
        user.set_password(password)

    user.email = email
    user.is_active = is_active
    user.is_staff = is_staff
    user.save()

    profile = user.profile
    profile.display_name = display_name
    profile.department = department
    profile.role = role
    profile.save()

    return Response({'status': 'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_set_permissions(request, pk):
    if not request.user.is_superuser:
        return Response({'detail': 'Permission denied.'}, status=403)
        
    user = get_object_or_404(User, pk=pk)
    menu_ids = request.data.get('menu_ids', [])
    if not isinstance(menu_ids, list):
        return Response({'error': '選單權限格式錯誤。'}, status=400)
    
    profile = user.profile
    valid_menu_items = MenuItem.objects.filter(id__in=menu_ids, is_active=True)
    profile.allowed_menu_items.set(valid_menu_items)
    profile.save()

    return Response({'status': 'success'})

@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def user_delete(request, pk):
    if not request.user.is_superuser:
        return Response({'detail': 'Permission denied.'}, status=403)
        
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        return Response({'error': '您不能刪除自己！'}, status=400)
        
    user.delete()
    return Response({'status': 'success'})
