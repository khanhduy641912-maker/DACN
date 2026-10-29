from django.contrib import admin
from .models import (
    ChuongTrinhDaoTao,
    ChuongTrinhMonHoc,
    DangKy,
    DotDangKy,
    HocKy,
    LopHocPhan,
    MonHoc,
    MonHocDaHoanThanh,
    MonTienQuyet,
    PhongHoc,
    SinhVien,
    TieuChiUuTien,
)

admin.site.site_header = "Hệ thống đăng ký môn học"
admin.site.site_title = "Quản trị đăng ký môn học"
admin.site.index_title = "Trung tâm quản lý dữ liệu"


@admin.register(HocKy)
class HocKyAdmin(admin.ModelAdmin):
    verbose_name_plural = "Học kỳ"
    list_display = ("ma_hoc_ky", "ten_hoc_ky", "ngay_bat_dau", "ngay_ket_thuc")
    search_fields = ("ma_hoc_ky", "ten_hoc_ky")
    list_per_page = 20


class ChuongTrinhMonHocInline(admin.TabularInline):
    model = ChuongTrinhMonHoc
    extra = 1
    verbose_name = "Môn học"
    verbose_name_plural = "Danh sách môn học trong chương trình"


@admin.register(ChuongTrinhDaoTao)
class ChuongTrinhDaoTaoAdmin(admin.ModelAdmin):
    verbose_name_plural = "Chương trình đào tạo"
    list_display = ("ma_chuong_trinh", "ten_chuong_trinh", "nganh", "khoa_ap_dung")
    search_fields = ("ma_chuong_trinh", "ten_chuong_trinh", "nganh")
    inlines = (ChuongTrinhMonHocInline,)


@admin.register(MonHoc)
class MonHocAdmin(admin.ModelAdmin):
    verbose_name_plural = "Môn học"
    list_display = ('ma_mon', 'ten_mon', 'so_tin_chi')
    search_fields = ('ma_mon', 'ten_mon')
    list_per_page = 25

@admin.register(MonTienQuyet)
class MonTienQuyetAdmin(admin.ModelAdmin):
    verbose_name_plural = "Điều kiện tiên quyết / song hành"
    list_display = ('mon_hoc', 'mon_tien_quyet', 'loai_dieu_kien')
    list_filter = ('loai_dieu_kien',)
    search_fields = ('mon_hoc__ma_mon', 'mon_hoc__ten_mon', 'mon_tien_quyet__ma_mon', 'mon_tien_quyet__ten_mon')
    list_select_related = ('mon_hoc', 'mon_tien_quyet')

@admin.register(SinhVien)
class SinhVienAdmin(admin.ModelAdmin):
    verbose_name_plural = "Sinh viên"
    list_display = ('mssv', 'ho_ten', 'lop', 'nganh', 'chuong_trinh')
    list_filter = ('chuong_trinh', 'nganh')
    search_fields = ('mssv', 'ho_ten', 'lop', 'user__username')
    list_select_related = ('chuong_trinh', 'user')

@admin.register(PhongHoc)
class PhongHocAdmin(admin.ModelAdmin):
    verbose_name_plural = "Phòng học"
    list_display = ('ma_phong', 'suc_chua')
    search_fields = ('ma_phong',)

@admin.register(LopHocPhan)
class LopHocPhanAdmin(admin.ModelAdmin):
    verbose_name_plural = "Lớp học phần"
    list_display = ('ma_lhp', 'mon_hoc', 'hoc_ky', 'giang_vien', 'thu', 'ca_hoc', 'si_so_hien_tai', 'si_so_toi_da')
    list_filter = ('hoc_ky', 'thu', 'ca_hoc')
    search_fields = ('ma_lhp', 'mon_hoc__ma_mon', 'mon_hoc__ten_mon', 'giang_vien')
    list_select_related = ('mon_hoc', 'hoc_ky', 'phong_hoc')
    list_per_page = 25

@admin.register(DotDangKy)
class DotDangKyAdmin(admin.ModelAdmin):
    verbose_name_plural = "Đợt đăng ký"
    list_display = ('ten_dot', 'hoc_ky', 'ngay_bat_dau', 'ngay_ket_thuc', 'kich_hoat')
    list_filter = ('kich_hoat', 'hoc_ky')
    search_fields = ('ten_dot',)
    list_select_related = ('hoc_ky',)


@admin.register(MonHocDaHoanThanh)
class MonHocDaHoanThanhAdmin(admin.ModelAdmin):
    verbose_name_plural = "Lịch sử học tập"
    list_display = ("sinh_vien", "mon_hoc", "hoc_ky", "diem", "ngay_hoan_thanh")
    list_filter = ("hoc_ky", "mon_hoc")
    search_fields = ("sinh_vien__mssv", "sinh_vien__ho_ten", "mon_hoc__ma_mon", "mon_hoc__ten_mon")
    list_select_related = ("sinh_vien", "mon_hoc", "hoc_ky")

@admin.register(TieuChiUuTien)
class TieuChiUuTienAdmin(admin.ModelAdmin):
    verbose_name_plural = "Tiêu chí thời khóa biểu"
    list_display = ("sinh_vien", "ca_uu_tien", "so_ngay_hoc_toi_da", "han_che_tiet_trong")
    search_fields = ("sinh_vien__mssv", "sinh_vien__ho_ten")
    list_select_related = ("sinh_vien",)

@admin.register(DangKy)
class DangKyAdmin(admin.ModelAdmin):
    verbose_name_plural = "Đăng ký môn học"
    list_display = ('sinh_vien', 'lop_hoc_phan', 'dot_dang_ky', 'thoi_gian_dang_ky')
    list_filter = ('dot_dang_ky', 'lop_hoc_phan__hoc_ky')
    search_fields = ('sinh_vien__mssv', 'sinh_vien__ho_ten', 'lop_hoc_phan__ma_lhp')
    list_select_related = ('sinh_vien', 'lop_hoc_phan', 'dot_dang_ky')