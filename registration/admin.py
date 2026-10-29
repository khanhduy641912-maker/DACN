from django.contrib import admin
from .models import MonHoc, MonTienQuyet, SinhVien, PhongHoc, LopHocPhan, DotDangKy, DangKy

@admin.register(MonHoc)
class MonHocAdmin(admin.ModelAdmin):
    list_display = ('ma_mon', 'ten_mon', 'so_tin_chi')
    search_fields = ('ma_mon', 'ten_mon')

@admin.register(MonTienQuyet)
class MonTienQuyetAdmin(admin.ModelAdmin):
    list_display = ('mon_hoc', 'mon_tien_quyet')

@admin.register(SinhVien)
class SinhVienAdmin(admin.ModelAdmin):
    list_display = ('mssv', 'ho_ten', 'lop', 'nganh')
    search_fields = ('mssv', 'ho_ten')

@admin.register(PhongHoc)
class PhongHocAdmin(admin.ModelAdmin):
    list_display = ('ma_phong', 'suc_chua')

@admin.register(LopHocPhan)
class LopHocPhanAdmin(admin.ModelAdmin):
    list_display = ('ma_lhp', 'mon_hoc', 'giang_vien', 'thu', 'ca_hoc', 'si_so_hien_tai', 'si_so_toi_da')
    list_filter = ('thu', 'ca_hoc')
    search_fields = ('ma_lhp', 'mon_hoc__ten_mon')

@admin.register(DotDangKy)
class DotDangKyAdmin(admin.ModelAdmin):
    list_display = ('ten_dot', 'ngay_bat_dau', 'ngay_ket_thuc', 'kich_hoat')

@admin.register(DangKy)
class DangKyAdmin(admin.ModelAdmin):
    list_display = ('sinh_vien', 'lop_hoc_phan', 'dot_dang_ky', 'thoi_gian_dang_ky')