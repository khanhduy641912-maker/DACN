from django.test import TestCase
from django.utils import timezone
from .models import MonHoc, LopHocPhan, SinhVien, DotDangKy, DangKy
from .utils import check_time_conflict, validate_registration
from django.contrib.auth.models import User

class CourseRegistrationTestCase(TestCase):
    def setUp(self):
        # 1. Tạo Môn học
        self.mon1 = MonHoc.objects.create(ma_mon="INT101", ten_mon="Lập trình Python", so_tin_chi=3)
        self.mon2 = MonHoc.objects.create(ma_mon="INT102", ten_mon="Cơ sở dữ liệu", so_tin_chi=3)

        # 2. Tạo Lớp học phần
        self.lhp1 = LopHocPhan.objects.create(
            ma_lhp="INT101_01", mon_hoc=self.mon1, giang_vien="GV A",
            thu=2, ca_hoc="SANG", tiet_bat_dau=1, so_tiet=3, si_so_toi_da=50
        )
        self.lhp2 = LopHocPhan.objects.create(
            ma_lhp="INT102_01", mon_hoc=self.mon2, giang_vien="GV B",
            thu=2, ca_hoc="SANG", tiet_bat_dau=1, so_tiet=3, si_so_toi_da=40
        ) # Trùng lịch với lhp1

        # 3. Tạo Đợt đăng ký
        self.dot = DotDangKy.objects.create(
            ten_dot="Đợt Test",
            ngay_bat_dau=timezone.now() - timezone.timedelta(days=1),
            ngay_ket_thuc=timezone.now() + timezone.timedelta(days=10),
            kich_hoat=True
        )

        # 4. Tạo User & Sinh vien
        self.user = User.objects.create_user(username="test_user", password="123")
        self.sv = SinhVien.objects.create(
            user=self.user, mssv="123456", ho_ten="Test Student", lop="Lop 1", nganh="CNTT"
        )

    def test_time_conflict_detection(self):
        """Kiểm tra hàm phát hiện trùng lịch"""
        is_conflict = check_time_conflict(self.lhp1, self.lhp2)
        self.assertTrue(is_conflict, "Lớp 1 và Lớp 2 phải bị phát hiện trùng lịch!")

    def test_registration_constraint(self):
        """Kiểm tra logic chặn đăng ký khi bị trùng lịch"""
        # Đăng ký lớp 1
        DangKy.objects.create(sinh_vien=self.sv, lop_hoc_phan=self.lhp1, dot_dang_ky=self.dot)
        
        # Thử đăng ký lớp 2 (bị trùng lịch)
        is_valid, msg = validate_registration(self.sv, self.lhp2, self.dot)
        self.assertFalse(is_valid, "Hệ thống phải từ chối đăng ký lớp 2 vì bị trùng lịch!")