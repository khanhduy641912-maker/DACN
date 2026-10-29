from django.db import models
from django.contrib.auth.models import User

# 1. Bảng Môn học
class MonHoc(models.Model):
    ma_mon = models.CharField(max_length=15, primary_key=True, verbose_name="Mã môn học")
    ten_mon = models.CharField(max_length=100, verbose_name="Tên môn học")
    so_tin_chi = models.IntegerField(verbose_name="Số tín chỉ")

    class Meta:
        verbose_name = "Môn học"
        verbose_name_plural = "Môn học"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(so_tin_chi__gt=0),
                name="course_credits_must_be_positive",
            )
        ]

    def __str__(self):
        return f"{self.ma_mon} - {self.ten_mon}"


class HocKy(models.Model):
    ma_hoc_ky = models.CharField(max_length=20, primary_key=True, verbose_name="Mã học kỳ")
    ten_hoc_ky = models.CharField(max_length=100, verbose_name="Tên học kỳ")
    ngay_bat_dau = models.DateField(verbose_name="Ngày bắt đầu")
    ngay_ket_thuc = models.DateField(verbose_name="Ngày kết thúc")

    class Meta:
        verbose_name = "Học kỳ"
        verbose_name_plural = "Học kỳ"
        ordering = ["-ngay_bat_dau"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ngay_ket_thuc__gte=models.F("ngay_bat_dau")),
                name="semester_dates_in_order",
            )
        ]

    def __str__(self):
        return self.ten_hoc_ky


class ChuongTrinhDaoTao(models.Model):
    ma_chuong_trinh = models.CharField(max_length=20, primary_key=True, verbose_name="Mã chương trình")
    ten_chuong_trinh = models.CharField(max_length=150, verbose_name="Tên chương trình")
    nganh = models.CharField(max_length=100, verbose_name="Ngành")
    khoa_ap_dung = models.CharField(max_length=20, verbose_name="Khóa áp dụng")
    mon_hoc = models.ManyToManyField(
        MonHoc,
        through="ChuongTrinhMonHoc",
        related_name="chuong_trinh_dao_tao",
        verbose_name="Môn học",
    )

    class Meta:
        verbose_name = "Chương trình đào tạo"
        verbose_name_plural = "Chương trình đào tạo"

    def __str__(self):
        return f"{self.ma_chuong_trinh} - {self.ten_chuong_trinh}"


class ChuongTrinhMonHoc(models.Model):
    chuong_trinh = models.ForeignKey(ChuongTrinhDaoTao, on_delete=models.CASCADE)
    mon_hoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE)
    bat_buoc = models.BooleanField(default=True, verbose_name="Môn bắt buộc")

    class Meta:
        verbose_name = "Môn trong chương trình"
        verbose_name_plural = "Môn trong chương trình"
        constraints = [
            models.UniqueConstraint(
                fields=["chuong_trinh", "mon_hoc"],
                name="unique_course_in_curriculum",
            )
        ]

    def __str__(self):
        return f"{self.chuong_trinh}: {self.mon_hoc}"


# 2. Bảng Môn tiên quyết
class MonTienQuyet(models.Model):
    LOAI_DIEU_KIEN_CHOICES = [
        ("TIEN_QUYET", "Môn tiên quyết"),
        ("SONG_HANH", "Môn song hành"),
    ]

    mon_hoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE, related_name="mon_chinh")
    mon_tien_quyet = models.ForeignKey(MonHoc, on_delete=models.CASCADE, related_name="mon_bat_buoc")
    loai_dieu_kien = models.CharField(
        max_length=12,
        choices=LOAI_DIEU_KIEN_CHOICES,
        default="TIEN_QUYET",
        verbose_name="Loại điều kiện",
    )

    class Meta:
        verbose_name = "Điều kiện môn học"
        verbose_name_plural = "Điều kiện tiên quyết / song hành"
        constraints = [
            models.UniqueConstraint(
                fields=["mon_hoc", "mon_tien_quyet"],
                name="unique_course_prerequisite",
            ),
            models.CheckConstraint(
                condition=~models.Q(mon_hoc=models.F("mon_tien_quyet")),
                name="course_cannot_prerequisite_itself",
            ),
        ]

# 3. Bảng Sinh viên
class SinhVien(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    mssv = models.CharField(max_length=15, primary_key=True, verbose_name="Mã số sinh viên")
    ho_ten = models.CharField(max_length=100, verbose_name="Họ và tên")
    lop = models.CharField(max_length=30, verbose_name="Lớp sinh hoạt")
    nganh = models.CharField(max_length=100, verbose_name="Ngành học")
    chuong_trinh = models.ForeignKey(
        ChuongTrinhDaoTao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sinh_vien",
        verbose_name="Chương trình đào tạo",
    )

    class Meta:
        verbose_name = "Sinh viên"
        verbose_name_plural = "Sinh viên"

    def __str__(self):
        return f"{self.mssv} - {self.ho_ten}"

# 4. Bảng Phòng học
class PhongHoc(models.Model):
    ma_phong = models.CharField(max_length=20, primary_key=True, verbose_name="Mã phòng")
    suc_chua = models.IntegerField(default=40, verbose_name="Sức chứa")

    class Meta:
        verbose_name = "Phòng học"
        verbose_name_plural = "Phòng học"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(suc_chua__gt=0),
                name="room_capacity_must_be_positive",
            )
        ]

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
    hoc_ky = models.ForeignKey(
        HocKy,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="lop_hoc_phan",
        verbose_name="Học kỳ",
    )
    giang_vien = models.CharField(max_length=100, verbose_name="Giảng viên")
    phong_hoc = models.ForeignKey(PhongHoc, on_delete=models.SET_NULL, null=True, verbose_name="Phòng học")
    
    thu = models.IntegerField(choices=THU_CHOICES, verbose_name="Thứ")
    ca_hoc = models.CharField(max_length=10, choices=CA_HOC_CHOICES, verbose_name="Ca học")
    tiet_bat_dau = models.IntegerField(verbose_name="Tiết bắt đầu (1-10)")
    so_tiet = models.IntegerField(default=3, verbose_name="Số tiết học")
    
    si_so_toi_da = models.IntegerField(default=50, verbose_name="Sĩ số tối đa")
    si_so_hien_tai = models.IntegerField(default=0, verbose_name="Sĩ số hiện tại")

    class Meta:
        verbose_name = "Lớp học phần"
        verbose_name_plural = "Lớp học phần"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(thu__gte=2) & models.Q(thu__lte=7),
                name="section_weekday_between_2_and_7",
            ),
            models.CheckConstraint(
                condition=models.Q(ca_hoc__in=["SANG", "CHIEU"]),
                name="section_shift_is_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(tiet_bat_dau__gte=1)
                & models.Q(tiet_bat_dau__lte=10),
                name="section_start_period_between_1_and_10",
            ),
            models.CheckConstraint(
                condition=models.Q(so_tiet__gt=0),
                name="section_period_count_must_be_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(tiet_bat_dau__lte=11 - models.F("so_tiet")),
                name="section_must_end_by_period_10",
            ),
            models.CheckConstraint(
                condition=models.Q(si_so_toi_da__gt=0),
                name="section_capacity_must_be_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(si_so_hien_tai__gte=0)
                & models.Q(si_so_hien_tai__lte=models.F("si_so_toi_da")),
                name="section_enrollment_within_capacity",
            ),
        ]

    def __str__(self):
        return f"{self.ma_lhp} - {self.mon_hoc.ten_mon} (Thứ {self.thu}, Ca {self.ca_hoc})"

    @property
    def tiet_ket_thuc(self):
        return self.tiet_bat_dau + self.so_tiet - 1

# 6. Bảng Đợt đăng ký môn học
class DotDangKy(models.Model):
    ten_dot = models.CharField(max_length=100, verbose_name="Tên đợt đăng ký")
    hoc_ky = models.ForeignKey(
        HocKy,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dot_dang_ky",
        verbose_name="Học kỳ",
    )
    ngay_bat_dau = models.DateTimeField(verbose_name="Ngày bắt đầu")
    ngay_ket_thuc = models.DateTimeField(verbose_name="Ngày kết thúc")
    kich_hoat = models.BooleanField(default=True, verbose_name="Mở đợt đăng ký")

    class Meta:
        verbose_name = "Đợt đăng ký"
        verbose_name_plural = "Đợt đăng ký"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ngay_ket_thuc__gt=models.F("ngay_bat_dau")),
                name="registration_period_dates_in_order",
            )
        ]

    def __str__(self):
        return self.ten_dot


class MonHocDaHoanThanh(models.Model):
    sinh_vien = models.ForeignKey(
        SinhVien, on_delete=models.CASCADE, related_name="mon_hoc_da_hoan_thanh"
    )
    mon_hoc = models.ForeignKey(
        MonHoc, on_delete=models.PROTECT, related_name="ket_qua_sinh_vien"
    )
    hoc_ky = models.ForeignKey(
        HocKy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ket_qua_hoc_tap",
    )
    diem = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    ngay_hoan_thanh = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Môn học đã hoàn thành"
        verbose_name_plural = "Lịch sử học tập"
        constraints = [
            models.UniqueConstraint(
                fields=["sinh_vien", "mon_hoc"],
                name="unique_completed_course_per_student",
            ),
            models.CheckConstraint(
                condition=models.Q(diem__isnull=True)
                | (models.Q(diem__gte=0) & models.Q(diem__lte=10)),
                name="completed_course_grade_between_0_and_10",
            ),
        ]

    def __str__(self):
        return f"{self.sinh_vien.mssv} - {self.mon_hoc.ma_mon}"


class TieuChiUuTien(models.Model):
    CA_UU_TIEN_CHOICES = [
        ("BAT_KY", "Không ưu tiên ca"),
        ("SANG", "Ưu tiên ca sáng"),
        ("CHIEU", "Ưu tiên ca chiều"),
    ]

    sinh_vien = models.OneToOneField(
        SinhVien,
        on_delete=models.CASCADE,
        related_name="tieu_chi_uu_tien",
    )
    ca_uu_tien = models.CharField(
        max_length=10,
        choices=CA_UU_TIEN_CHOICES,
        default="BAT_KY",
        verbose_name="Ca học ưu tiên",
    )
    so_ngay_hoc_toi_da = models.PositiveSmallIntegerField(
        default=6,
        verbose_name="Số ngày học tối đa",
    )
    han_che_tiet_trong = models.BooleanField(
        default=True,
        verbose_name="Hạn chế tiết trống",
    )

    class Meta:
        verbose_name = "Tiêu chí thời khóa biểu"
        verbose_name_plural = "Tiêu chí thời khóa biểu"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(so_ngay_hoc_toi_da__gte=1)
                & models.Q(so_ngay_hoc_toi_da__lte=6),
                name="preferred_max_study_days_between_1_and_6",
            )
        ]

    def __str__(self):
        return f"Tiêu chí của {self.sinh_vien.mssv}"


# 7. Bảng Đăng ký môn học
class DangKy(models.Model):
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE, verbose_name="Sinh viên")
    lop_hoc_phan = models.ForeignKey(LopHocPhan, on_delete=models.CASCADE, verbose_name="Lớp học phần")
    dot_dang_ky = models.ForeignKey(DotDangKy, on_delete=models.CASCADE, verbose_name="Đợt đăng ký")
    thoi_gian_dang_ky = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian đăng ký")

    class Meta:
        verbose_name = "Đăng ký môn học"
        verbose_name_plural = "Đăng ký môn học"
        unique_together = ('sinh_vien', 'lop_hoc_phan', 'dot_dang_ky')

    def __str__(self):
        return f"{self.sinh_vien.mssv} -> {self.lop_hoc_phan.ma_lhp}"