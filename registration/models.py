from django.db import models
from django.contrib.auth.models import User

# 1. Bảng Môn học
class MonHoc(models.Model):
    ma_mon = models.CharField(max_length=15, primary_key=True, verbose_name="Mã môn học")
    ten_mon = models.CharField(max_length=100, verbose_name="Tên môn học")
    so_tin_chi = models.IntegerField(verbose_name="Số tín chỉ")

    def __str__(self):
        return f"{self.ma_mon} - {self.ten_mon}"

# 2. Bảng Môn tiên quyết
class MonTienQuyet(models.Model):
    mon_hoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, related_name="mon_chinh")
    mon_tien_quyet = models.ForeignKey(MonHoc, on_delete=models.CASCADE, related_name="mon_bat_buoc")

# 3. Bảng Sinh viên
class SinhVien(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    mssv = models.CharField(max_length=15, primary_key=True, verbose_name="Mã số sinh viên")
    ho_ten = models.CharField(max_length=100, verbose_name="Họ và tên")
    lop = models.CharField(max_length=30, verbose_name="Lớp sinh hoạt")
    nganh = models.CharField(max_length=100, verbose_name="Ngành học")

    def __str__(self):
        return f"{self.mssv} - {self.ho_ten}"

# 4. Bảng Phòng học
class PhongHoc(models.Model):
    ma_phong = models.CharField(max_length=20, primary_key=True, verbose_name="Mã phòng")
    suc_chua = models.IntegerField(default=40, verbose_name="Sức chứa")

    def __str__(self):
        return self.ma_phong

# 5. Bảng Lớp học phần
class LopHocPhan(models.Model):
    CA_HOC_CHOICES = [
        ('SANG', 'Ca Sáng (Tiết 1-5)'),
        ('CHIEU', 'Ca Chiều (Tiết 6-10)'),
    ]
    THU_CHOICES = [
        (2, 'Thứ Hai'),
        (3, 'Thứ Ba'),
        (4, 'Thứ Tư'),
        (5, 'Thứ Năm'),
        (6, 'Thứ Sáu'),
        (7, 'Thứ Bảy'),
    ]

    ma_lhp = models.CharField(max_length=25, primary_key=True, verbose_name="Mã lớp học phần")
    mon_hoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, verbose_name="Môn học")
    giang_vien = models.CharField(max_length=100, verbose_name="Giảng viên")
    phong_hoc = models.ForeignKey(PhongHoc, on_delete=models.SET_NULL, null=True, verbose_name="Phòng học")
    
    thu = models.IntegerField(choices=THU_CHOICES, verbose_name="Thứ")
    ca_hoc = models.CharField(max_length=10, choices=CA_HOC_CHOICES, verbose_name="Ca học")
    tiet_bat_dau = models.IntegerField(verbose_name="Tiết bắt đầu (1-10)")
    so_tiet = models.IntegerField(default=3, verbose_name="Số tiết học")
    
    si_so_toi_da = models.IntegerField(default=50, verbose_name="Sĩ số tối đa")
    si_so_hien_tai = models.IntegerField(default=0, verbose_name="Sĩ số hiện tại")

    def __str__(self):
        return f"{self.ma_lhp} - {self.mon_hoc.ten_mon} (Thứ {self.thu}, Ca {self.ca_hoc})"

# 6. Bảng Đợt đăng ký môn học
class DotDangKy(models.Model):
    ten_dot = models.CharField(max_length=100, verbose_name="Tên đợt đăng ký")
    ngay_bat_dau = models.DateTimeField(verbose_name="Ngày bắt đầu")
    ngay_ket_thuc = models.DateTimeField(verbose_name="Ngày kết thúc")
    kich_hoat = models.BooleanField(default=True, verbose_name="Mở đợt đăng ký")

    def __str__(self):
        return self.ten_dot

# 7. Bảng Đăng ký môn học
class DangKy(models.Model):
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE, verbose_name="Sinh viên")
    lop_hoc_phan = models.ForeignKey(LopHocPhan, on_delete=models.CASCADE, verbose_name="Lớp học phần")
    dot_dang_ky = models.ForeignKey(DotDangKy, on_delete=models.CASCADE, verbose_name="Đợt đăng ký")
    thoi_gian_dang_ky = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian đăng ký")

    class Meta:
        unique_together = ('sinh_vien', 'lop_hoc_phan', 'dot_dang_ky')

    def __str__(self):
        return f"{self.sinh_vien.mssv} -> {self.lop_hoc_phan.ma_lhp}"