import os
import re
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings
from django.db.models import Q, Max, Count
from django.contrib import messages
from openpyxl import Workbook
from nads26.upload_validation import UploadValidationError, validate_uploaded_file
from .models import Member

# 照片目錄路徑
PHOTO_FOLDER = os.path.join(settings.MEDIA_ROOT, 'eureka', 'photo')
EUREKA_PHOTO_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

VARIANT_MAP = {'峰': '峰峯', '峯': '峰峯', '群': '群羣', '羣': '群羣'}


def get_search_results(request):
    """處理搜尋邏輯，支援 7 個搜尋條件 (AND / OR / NOT)"""
    query = Member.objects.all()
    # 支援的欄位
    fields = ['name', 'name2', 'mobile1', 'car_number', 'section', 'address', 'note']
    and_filters, or_filters, not_filters = [], [], []

    has_active_filter = False

    for f in fields:
        val = request.GET.get(f'val_{f}', '').strip()
        logic = request.GET.get(f'l_{f}', 'A')

        if val:
            has_active_filter = True
            condition = None
            
            if f == 'name' or f == 'name2':
                # 相似字擴展搜尋
                char_conds = []
                for char in val:
                    variants = VARIANT_MAP.get(char, char)
                    char_q = Q()
                    for v in variants:
                        char_q |= Q(name__contains=v)
                    char_conds.append(char_q)
                
                if char_conds:
                    condition = char_conds[0]
                    for cond in char_conds[1:]:
                        condition &= cond
            elif f == 'mobile1':
                clean_val = re.sub(r'\D', '', val)
                if clean_val:
                    condition = Q(mobile1__contains=clean_val)
            elif f == 'car_number':
                condition = Q(car_number__icontains=val)
            elif f == 'section':
                if val not in ('全部分區', '全分區', '全部', ''):
                    condition = Q(section__icontains=val)
            else:
                condition = Q(**{f"{f}__contains": val})

            if condition is not None:
                if logic == 'A':
                    and_filters.append(condition)
                elif logic == 'O':
                    or_filters.append(condition)
                elif logic == 'X':
                    not_filters.append(condition)

    if not has_active_filter:
        return None

    c_and = Q()
    if and_filters:
        c_and = and_filters[0]
        for cond in and_filters[1:]:
            c_and &= cond

    c_or = Q()
    if or_filters:
        c_or = or_filters[0]
        for cond in or_filters[1:]:
            c_or |= cond

    combined_filter = Q()
    if and_filters and or_filters:
        combined_filter = c_and | c_or
    elif and_filters:
        combined_filter = c_and
    elif or_filters:
        combined_filter = c_or

    if not_filters:
        c_not = not_filters[0]
        for cond in not_filters[1:]:
            c_not |= cond
        if combined_filter:
            combined_filter &= ~c_not
        else:
            combined_filter = ~c_not

    if combined_filter:
        query = query.filter(combined_filter)
    else:
        query = Member.objects.none()
    
    # 限制最多回傳 100 筆，並回傳同家族成員的資訊以優化搜尋卡片效能
    return query.order_by('church_id')[:100]


@login_required
def serve_photo(request, filename):
    """安全提供人員照片，若檔案不存在則回傳 404"""
    safe_filename = os.path.basename(filename)
    photo_path = os.path.join(PHOTO_FOLDER, safe_filename)
    if os.path.exists(photo_path):
        return FileResponse(open(photo_path, 'rb'), content_type='image/jpeg')
    raise Http404("照片不存在")


@login_required
def eureka_view(request):
    """找人搜尋主頁"""
    results = get_search_results(request)
    
    # 獲取所有不為空的牧區，供下拉選單選擇
    sections = Member.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    
    if results is not None:
        # 對於搜尋結果，我們可以直接獲取每個會員的家族成員，供卡片顯示
        for m in results:
            if m.family_id:
                m.family_list = Member.objects.filter(family_id=m.family_id).exclude(church_id=m.church_id)
            else:
                m.family_list = []
                
            # 解析卡片顯示出席率 (例如: "55 57 88 88 73 100")
            if m.percent_year:
                m.att_percent_display = m.percent_year.replace('-', ' ')
            else:
                m.att_percent_display = "無紀錄"
            
    return render(request, 'eureka/eureka.html', {
        'results': results,
        'sections': sections,
        'query_params': request.GET,
    })


@login_required
def melos_view(request, church_id):
    """人員資料編輯/詳情"""
    member = get_object_or_404(Member, church_id=church_id)
    if request.method == 'POST':
        member.name = request.POST.get('name', '').strip()
        member.mobile1 = request.POST.get('mobile1', '').strip()
        member.email1 = request.POST.get('email1', '').strip()
        member.address = request.POST.get('address', '').strip()
        member.note = request.POST.get('note', '').strip()
        member.section = request.POST.get('section', '').strip()
        fid = request.POST.get('family_id', '').strip()
        member.family_id = int(fid) if fid else None
        member.save()
        
        # 重新導向回搜尋結果，帶上之前的 query parameters
        get_params = request.GET.urlencode()
        redirect_url = '/eureka/'
        if get_params:
            redirect_url += f'?{get_params}'
        return redirect(redirect_url)

    # 取得同家族成員
    family = []
    if member.family_id:
        family = Member.objects.filter(family_id=member.family_id).exclude(church_id=member.church_id)

    # 處理舊的出席紀錄換行符號（保留相容性）
    att_records = member.att_str.replace('$', '\n') if member.att_str else "無紀錄"

    # 首次打卡日期 fallback：若欄位為空則動態查詢本機的 checkin_records
    first_checkin = member.first_daka
    if not first_checkin:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT MIN(timestamp) FROM checkin_records WHERE church_id = %s", [member.church_id])
            row = cursor.fetchone()
            if row and row[0]:
                first_checkin = row[0].strftime('%Y-%m-%d')
            else:
                first_checkin = "-"

    # 解析年度出席率以供圖表使用 (55-57-88-88-73-100 -> 2021~2026 年)
    yearly_attendance = []
    if member.percent_year:
        rates = member.percent_year.split('-')
        years = [2021, 2022, 2023, 2024, 2025, 2026]
        for y, r in zip(years, rates):
            try:
                yearly_attendance.append({
                    'year': y,
                    'rate': int(r),
                })
            except ValueError:
                pass

    results = get_search_results(request)
    sections = Member.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    
    if results is not None:
        for m_item in results:
            if m_item.family_id:
                m_item.family_list = Member.objects.filter(family_id=m_item.family_id).exclude(church_id=m_item.church_id)
            else:
                m_item.family_list = []
                
            if m_item.percent_year:
                m_item.att_percent_display = m_item.percent_year.replace('-', ' ')
            else:
                m_item.att_percent_display = "無紀錄"

    return render(request, 'eureka/eureka.html', {
        'results': results,
        'sections': sections,
        'query_params': request.GET,
        'show_modal': True,
        'm': member,
        'family': family,
        'att_records': att_records,
        'first_checkin': first_checkin,
        'yearly_attendance': yearly_attendance,
        'query_params_url': request.GET.urlencode(),
    })


@login_required
def neos_view(request):
    """新增人員"""
    if request.method == 'POST':
        church_id = request.POST.get('church_id')
        name = request.POST.get('name', '').strip()
        mobile1 = request.POST.get('mobile1', '').strip()
        email1 = request.POST.get('email1', '').strip()
        address = request.POST.get('address', '').strip()
        section = request.POST.get('section', '').strip()
        fid = request.POST.get('family_id', '').strip()
        family_id = int(fid) if fid else None

        new_m = Member.objects.create(
            church_id=church_id,
            name=name,
            mobile1=mobile1,
            email1=email1,
            address=address,
            section=section,
            family_id=family_id
        )
        return redirect('/eureka/')
    return render(request, 'eureka/neos.html')


@login_required
def pastoral_view(request):
    """牧區小組檢視"""
    # 統計數據
    total_members = Member.objects.count()
    sections_count = Member.objects.exclude(section='').values('section').distinct().count()
    groups_count = Member.objects.exclude(family1='').values('family1').distinct().count()
    
    # 區牧結構與靜態資訊
    pastoral_structure = [
        {
            'overseer': '董牧',
            'sections': [
                {'name': '加樂牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '百合A區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '百合B區', 'leader1': '正傑', 'leader2': '', 'date': '', 'status': ''},
                {'name': '百合牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': '暫停'},
                {'name': '百合C區', 'leader1': '日勇', 'leader2': '', 'date': '', 'status': ''},
            ]
        },
        {
            'overseer': 'X',
            'sections': [
                {'name': '摩利亞牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': '解散'},
                {'name': '青少年團契', 'leader1': '', 'leader2': '', 'date': '', 'status': '解散'},
                {'name': '香柏樹牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': '解散'},
            ]
        },
        {
            'overseer': '主蒞',
            'sections': [
                {'name': '31婦女牧區', 'leader1': '淑如', 'leader2': '', 'date': '', 'status': ''},
                {'name': '敬愛團契', 'leader1': '', 'leader2': '', 'date': '', 'status': '解散'},
                {'name': '北門Young牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
            ]
        },
        {
            'overseer': '明珠',
            'sections': [
                {'name': '湧二牧區', 'leader1': '堯尹', 'leader2': '明玲', 'date': '', 'status': ''},
                {'name': '幸福牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
            ]
        },
        {
            'overseer': 'A',
            'sections': [
                {'name': '二魚牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '青橄欖牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '青草地牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '清心一區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '清心二區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '兒童牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
                {'name': '新朋友牧區', 'leader1': '', 'leader2': '', 'date': '', 'status': ''},
            ]
        }
    ]
    
    # 1. 預先載入所有家族成員的對照表 (僅執行 1 次 DB 查詢)
    family_map = {}
    family_members_qs = Member.objects.exclude(family_id__isnull=True).only('church_id', 'name', 'family_id')
    for m in family_members_qs:
        if m.family_id not in family_map:
            family_map[m.family_id] = []
        family_map[m.family_id].append({'church_id': m.church_id, 'name': m.name})
        
    # 2. 獲取所有相關牧區的成員 (僅執行 1 次 DB 查詢)
    active_sections = []
    for cat in pastoral_structure:
        for sec in cat['sections']:
            active_sections.append(sec['name'])
            
    all_members = Member.objects.filter(section__in=active_sections).order_by('name')
    
    # 3. 在記憶體中進行分組與資料處理，避免 N+1 查詢
    members_by_section = {}
    for m in all_members:
        sec_name = m.section
        if sec_name not in members_by_section:
            members_by_section[sec_name] = []
        members_by_section[sec_name].append(m)
        
        # 填充家族成員資訊 (記憶體查詢)
        if m.family_id and m.family_id in family_map:
            m.family_list = [f for f in family_map[m.family_id] if f['church_id'] != m.church_id]
        else:
            m.family_list = []
            
        if m.percent_year:
            m.att_percent_display = m.percent_year.replace('-', ' ')
        else:
            m.att_percent_display = "無紀錄"
            
    # 4. 組裝結構資料
    for category in pastoral_structure:
        cat_member_count = 0
        cat_group_count = 0
        cat_section_count = len(category['sections'])
        
        for sec in category['sections']:
            sec_name = sec['name']
            sec_members = members_by_section.get(sec_name, [])
            sec['member_count'] = len(sec_members)
            cat_member_count += sec['member_count']
            
            # 分組 (小組)
            groups_dict = {}
            for m in sec_members:
                g_name = m.family1
                if not g_name:
                    continue
                if g_name not in groups_dict:
                    groups_dict[g_name] = []
                groups_dict[g_name].append(m)
                
            sec['group_count'] = len(groups_dict)
            cat_group_count += sec['group_count']
            
            # 排序小組名稱
            sorted_groups = sorted(groups_dict.keys())
            sec['groups_data'] = []
            for g_name in sorted_groups:
                sec['groups_data'].append({
                    'name': g_name,
                    'member_count': len(groups_dict[g_name]),
                    'members': groups_dict[g_name]
                })
                
        category['member_count'] = cat_member_count
        category['group_count'] = cat_group_count
        category['section_count'] = cat_section_count
        
    return render(request, 'eureka/pastoral.html', {
        'total_members': total_members,
        'sections_count': sections_count,
        'groups_count': groups_count,
        'pastoral_structure': pastoral_structure,
    })


@login_required
def add_view(request):
    """新朋友登記"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip().replace(" ", "")
        if not name:
            messages.error(request, '姓名為必填欄位')
            return redirect('eureka:add')
            
        max_id = Member.objects.aggregate(Max('church_id'))['church_id__max']
        new_church_id = (max_id or 0) + 1
        
        gender_val = request.POST.get('gender', '')
        gender = 'M' if gender_val == 'male' else ('F' if gender_val == 'female' else '')
        
        marriage_val = request.POST.get('marriage', '')
        marriage = 'm' if marriage_val == 'yes' else ('s' if marriage_val == 'no' else '')
        
        baptized_val = request.POST.get('baptized', '')
        baptized = 'y' if baptized_val == 'yes' else ('n' if baptized_val == 'no' else '')
        
        b_year = request.POST.get('b_year', '')
        b_month = request.POST.get('b_month', '')
        b_day = request.POST.get('b_day', '')
        birthday = None
        if b_year.isdigit() and b_month.isdigit() and b_day.isdigit():
            try:
                birthday = datetime.date(int(b_year) + 1911, int(b_month), int(b_day))
            except ValueError:
                pass
                
        emer_name = request.POST.get('emer_contact_name', '').strip()
        emer_phone = request.POST.get('emer_contact_phone', '').strip()
        emer_relation = request.POST.get('emer_contact_relation', '').strip()
        
        note = request.POST.get('note', '').strip()
        if emer_name or emer_phone or emer_relation:
            relation_map = {'dad': '爸爸', 'mom': '媽媽'}
            rel = relation_map.get(emer_relation, emer_relation)
            note += f"\n[緊急聯絡人: {emer_name} ({rel}) {emer_phone}]".strip()
            
        visitor_notes = []
        if request.POST.get('checkbox1') == 'on':
            visitor_notes.append('我不是基督徒，願進一步了解基督教')
        if request.POST.get('checkbox2') == 'on':
            visitor_notes.append('我尚未受洗，願參加慕道班明白真理')
        if request.POST.get('checkbox3') == 'on':
            visitor_notes.append('我是基督徒，因臨時需要而參加貴堂之聚會')
        if request.POST.get('checkbox4') == 'on':
            visitor_notes.append('我是基督徒，我目前還沒有固定參加哪一個教會')
        if request.POST.get('checkbox5') == 'on':
            visitor_notes.append('我是基督徒，今後可能經常參加貴堂之聚會')
            
        if visitor_notes:
            note += " (訪客資訊: " + "，".join(visitor_notes) + ")"
            
        def parse_roc_date(date_str):
            if not date_str:
                return datetime.date.today()
            try:
                parts = date_str.split('-')
                if len(parts) == 3:
                    return datetime.date(int(parts[0]) + 1911, int(parts[1]), int(parts[2]))
            except Exception:
                pass
            return datetime.date.today()
            
        join_date = parse_roc_date(request.POST.get('joindate', ''))
        dataindate = parse_roc_date(request.POST.get('dataindate', ''))

        photo_file = request.FILES.get('photo')
        if photo_file:
            try:
                validate_uploaded_file(
                    photo_file,
                    allowed_extensions=EUREKA_PHOTO_ALLOWED_EXTENSIONS,
                )
            except UploadValidationError as exc:
                messages.error(request, str(exc))
                return redirect('eureka:add')

        new_m = Member.objects.create(
            church_id=new_church_id,
            name=name,
            gender=gender,
            marriage=marriage,
            birthday=birthday,
            phone_h=request.POST.get('home_phone', '').strip(),
            phone_o=request.POST.get('office_phone', '').strip(),
            mobile1=request.POST.get('mobile_phone', '').strip(),
            address=request.POST.get('home_address', '').strip(),
            email1=request.POST.get('e_mail', '').strip(),
            baptized=baptized,
            section='新朋友牧區',
            family1='新朋友',
            note=note,
            join_date=join_date,
            dataindate=dataindate,
            car_number=request.POST.get('reserved2', '').strip().upper(),
            line_id=request.POST.get('reserved3', '').strip(),
            presence=0
        )

        if photo_file:
            photo_dir = os.path.join(settings.MEDIA_ROOT, 'eureka', 'photo')
            os.makedirs(photo_dir, exist_ok=True)
            photo_path = os.path.join(photo_dir, f"{new_church_id}.jpg")
            with open(photo_path, 'wb+') as destination:
                for chunk in photo_file.chunks():
                    destination.write(chunk)
                    
        messages.success(request, f"成功新增新朋友: {name} (ID: {new_church_id})")
        return redirect('eureka:add')
        
    today = datetime.date.today()
    roc_today = f"{today.year - 1911}-{today.month}-{today.day}"
    return render(request, 'eureka/add.html', {'dataindate': roc_today})


@login_required
def download_add_view(request):
    """下載新朋友資料的 Excel 檔"""
    if request.method != 'POST':
        return redirect('eureka:add')
        
    date_str = request.POST.get('date', '').strip()
    if not date_str:
        messages.error(request, '請輸入日期')
        return redirect('eureka:add')
        
    try:
        query_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, '不正確的日期格式，請使用西元格式如 2013-11-10')
        return redirect('eureka:add')
        
    members = Member.objects.filter(section='新朋友牧區', family1='新朋友', dataindate=query_date)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "新朋友資料"
    
    headers = ["填卡日期", "姓名", "性別", "出生年日", "手機", "Email", "電話(H)", "電話(O)", "住址", "車號", "附註"]
    ws.append(headers)
    
    for m in members:
        b_str = ""
        if m.birthday:
            b_str = f"{m.birthday.year - 1911}.{m.birthday.month:02d}.{m.birthday.day:02d}"
            
        gender_display = '男' if m.gender == 'M' else ('女' if m.gender == 'F' else '')
        dataindate_str = m.dataindate.strftime('%Y-%m-%d') if m.dataindate else ''
        
        ws.append([
            dataindate_str,
            m.name,
            gender_display,
            b_str,
            m.mobile1,
            m.email1,
            m.phone_h,
            m.phone_o,
            m.address,
            m.car_number,
            m.note
        ])
        
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename=new_friends_{date_str}.xlsx'
    wb.save(response)
    return response


@login_required
def modify_view(request):
    """搜名單與管理介面"""
    results = get_search_results(request)
    key_word = request.GET.get('key_word', '').strip()
    
    if results is None:
        if key_word:
            results = Member.objects.filter(
                Q(name__contains=key_word) |
                Q(mobile1__contains=key_word) |
                Q(address__contains=key_word) |
                Q(note__contains=key_word) |
                Q(section__contains=key_word) |
                Q(family1__contains=key_word) |
                Q(car_number__contains=key_word) |
                Q(line_id__contains=key_word)
            ).order_by('church_id')[:100]
        else:
            results = []
            
    sections = Member.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    
    return render(request, 'eureka/modify.html', {
        'people_list': results,
        'key_word': key_word,
        'result_count': len(results) if results else 0,
        'sections': sections,
        'query_params': request.GET,
    })


@login_required
def duplicates_view(request):
    """搜尋重複姓名"""
    duplicate_names = Member.objects.values('name').annotate(name_count=Count('name')).filter(name_count__gt=1)
    names = [item['name'] for item in duplicate_names]
    people_list = Member.objects.filter(name__in=names).order_by('name')
    sections = Member.objects.exclude(section='').values_list('section', flat=True).distinct().order_by('section')
    
    return render(request, 'eureka/modify.html', {
        'people_list': people_list,
        'key_word': '重複姓名',
        'result_count': len(people_list),
        'sections': sections,
        'query_params': request.GET,
    })


@login_required
def delete_view(request, church_id):
    """刪除成員"""
    member = get_object_or_404(Member, church_id=church_id)
    name = member.name
    
    photo_path = os.path.join(settings.MEDIA_ROOT, 'eureka', 'photo', f"{church_id}.jpg")
    if os.path.exists(photo_path):
        try:
            os.remove(photo_path)
        except Exception:
            pass
            
    member.delete()
    messages.success(request, f"成功刪除成員: {name} (ID: {church_id})")
    return redirect('eureka:modify')


@login_required
def download_all_view(request):
    """下載全部名單 Excel 檔"""
    members = Member.objects.all().order_by('church_id')
    
    wb = Workbook()
    ws = wb.active
    ws.title = "北門聖教會通訊錄"
    
    headers = ["姓名", "Email", "手機號碼", "室內電話", "住址", "牧區", "小組", "生日"]
    ws.append(headers)
    
    for m in members:
        birthday_str = m.birthday.strftime('%Y-%m-%d') if m.birthday else ''
        ws.append([
            m.name,
            m.email1,
            m.mobile1,
            m.phone_h,
            m.address,
            m.section,
            m.family1,
            birthday_str
        ])
        
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename=church_address_book.xlsx'
    wb.save(response)
    return response
