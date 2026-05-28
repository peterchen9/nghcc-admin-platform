from django.db import models


class Member(models.Model):
    """會員/人員主檔 — 對應 members 表"""

    church_id = models.BigIntegerField('Church ID', primary_key=True)
    name = models.CharField('姓名', max_length=255, default='')
    address = models.CharField('地址', max_length=255, blank=True, default='')
    mobile1 = models.CharField('手機', max_length=50, blank=True, default='')
    email1 = models.CharField('Email', max_length=255, blank=True, default='')
    note = models.TextField('備註', blank=True, default='')
    family_id = models.BigIntegerField('Family ID', null=True, blank=True)
    section = models.CharField('牧區', max_length=100, blank=True, default='')
    family1 = models.CharField('小組', max_length=255, blank=True, default='')
    
    # 額外出席與其它資訊欄位
    dataindate = models.DateField('資料輸入日期', null=True, blank=True)
    att_y = models.CharField('出席總覽年份/代碼', max_length=255, blank=True, default='')
    att_12m = models.IntegerField('近12個月出席', null=True, blank=True)
    att_str = models.TextField('出席詳情', blank=True, default='')
    percent_year = models.CharField('年度出席率', max_length=255, blank=True, default='')
    data_str = models.TextField('出席詳情圖', blank=True, default='')
    percent_12_month = models.CharField('近12月出席率', max_length=255, blank=True, default='')
    first_daka = models.CharField('首次打卡', max_length=50, blank=True, default='')

    # 其它既有資料庫欄位 (可選，防寫入/讀取對不齊，設為 blank/null 即可)
    gender = models.CharField('性別', max_length=10, blank=True, default='')
    birthday = models.DateField('生日', null=True, blank=True)
    join_date = models.DateField('加入日期', null=True, blank=True)
    baptized = models.CharField('已洗禮', max_length=10, blank=True, default='')
    presence = models.IntegerField('在場/現況', default=0)
    marriage = models.CharField('婚姻狀況', max_length=50, blank=True, default='')
    phone_h = models.CharField('住家電話', max_length=50, blank=True, default='')
    phone_o = models.CharField('辦公電話', max_length=50, blank=True, default='')
    visitor_info = models.CharField('訪客資訊', max_length=255, blank=True, default='')
    car_number = models.CharField('車牌號碼', max_length=50, blank=True, default='')
    line_id = models.CharField('Line ID', max_length=100, blank=True, default='')
    photo_base64 = models.TextField('照片 Base64', blank=True, default='')

    class Meta:
        db_table = 'members'
        managed = False  # 已由外部 mysqldump 匯入，不由 Django 控管 schema
        verbose_name = '人員'
        verbose_name_plural = '人員'

    def __str__(self):
        return f'[{self.church_id}] {self.name}'
