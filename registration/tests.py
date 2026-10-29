from django.test import TestCase
from django.utils import timezone
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
    SinhVien,
    TieuChiUuTien,
)
from .utils import (
    check_time_conflict,
    suggest_timetable_csp,
    suggest_timetable_options_csp,
    validate_registration,
)
from django.contrib.auth.models import User
from django.urls import reverse

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

    def test_prerequisite_requires_completed_course(self):
        MonTienQuyet.objects.create(
            mon_hoc=self.mon2,
            mon_tien_quyet=self.mon1,
            loai_dieu_kien="TIEN_QUYET",
        )

        valid, reason = validate_registration(self.sv, self.lhp2, self.dot)
        self.assertFalse(valid)
        self.assertIn("chưa hoàn thành", reason)

        MonHocDaHoanThanh.objects.create(sinh_vien=self.sv, mon_hoc=self.mon1)
        valid, _ = validate_registration(self.sv, self.lhp2, self.dot)
        self.assertTrue(valid)

    def test_completed_course_cannot_be_registered_again(self):
        MonHocDaHoanThanh.objects.create(sinh_vien=self.sv, mon_hoc=self.mon1)

        valid, reason = validate_registration(self.sv, self.lhp1, self.dot)

        self.assertFalse(valid)
        self.assertIn("đã hoàn thành", reason)

    def test_corequisite_can_be_registered_as_one_schedule(self):
        MonTienQuyet.objects.create(
            mon_hoc=self.mon2,
            mon_tien_quyet=self.mon1,
            loai_dieu_kien="SONG_HANH",
        )

        valid_without_pair, _ = validate_registration(self.sv, self.lhp2, self.dot)
        valid_with_pair, _ = validate_registration(
            self.sv,
            self.lhp2,
            self.dot,
            planned_course_ids={self.mon1.ma_mon, self.mon2.ma_mon},
        )
        self.assertFalse(valid_without_pair)
        self.assertTrue(valid_with_pair)

    def test_schedule_uses_saved_shift_preference_and_active_semester(self):
        semester = HocKy.objects.create(
            ma_hoc_ky="2026-1",
            ten_hoc_ky="Học kỳ 1 năm học 2026-2027",
            ngay_bat_dau=timezone.now().date(),
            ngay_ket_thuc=(timezone.now() + timezone.timedelta(days=90)).date(),
        )
        self.dot.hoc_ky = semester
        self.dot.save(update_fields=["hoc_ky"])

        LopHocPhan.objects.create(
            ma_lhp="INT101_MORNING",
            mon_hoc=self.mon1,
            hoc_ky=semester,
            giang_vien="GV Sáng",
            thu=2,
            ca_hoc="SANG",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT101_AFTERNOON",
            mon_hoc=self.mon1,
            hoc_ky=semester,
            giang_vien="GV Chiều",
            thu=3,
            ca_hoc="CHIEU",
            tiet_bat_dau=6,
            so_tiet=3,
        )
        preference = TieuChiUuTien.objects.create(
            sinh_vien=self.sv,
            ca_uu_tien="CHIEU",
            so_ngay_hoc_toi_da=3,
        )

        schedule = suggest_timetable_csp(
            [self.mon1.ma_mon], self.dot, self.sv, preference
        )

        self.assertIsNotNone(schedule)
        self.assertEqual(
            [section.ma_lhp for section in schedule["courses"]],
            ["INT101_AFTERNOON"],
        )

    def test_schedule_retries_greedy_choice_when_it_blocks_another_course(self):
        LopHocPhan.objects.create(
            ma_lhp="INT101_PREFERRED",
            mon_hoc=self.mon1,
            giang_vien="GV Ưu tiên",
            thu=2,
            ca_hoc="SANG",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT101_ALTERNATIVE",
            mon_hoc=self.mon1,
            giang_vien="GV Thay thế",
            thu=4,
            ca_hoc="CHIEU",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT102_CONFLICT_1",
            mon_hoc=self.mon2,
            giang_vien="GV B",
            thu=2,
            ca_hoc="SANG",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT102_CONFLICT_2",
            mon_hoc=self.mon2,
            giang_vien="GV C",
            thu=2,
            ca_hoc="SANG",
            tiet_bat_dau=2,
            so_tiet=3,
        )
        preference = TieuChiUuTien.objects.create(
            sinh_vien=self.sv,
            ca_uu_tien="SANG",
        )

        schedule = suggest_timetable_csp(
            [self.mon1.ma_mon, self.mon2.ma_mon],
            self.dot,
            self.sv,
            preference,
        )

        self.assertIsNotNone(schedule)
        self.assertIn(
            "INT101_ALTERNATIVE",
            [section.ma_lhp for section in schedule["courses"]],
        )

    def test_curriculum_limits_suggested_courses(self):
        program = ChuongTrinhDaoTao.objects.create(
            ma_chuong_trinh="CNTT-2026",
            ten_chuong_trinh="Công nghệ thông tin",
            nganh="Công nghệ thông tin",
            khoa_ap_dung="2026",
        )
        ChuongTrinhMonHoc.objects.create(
            chuong_trinh=program,
            mon_hoc=self.mon1,
        )
        self.sv.chuong_trinh = program
        self.sv.save(update_fields=["chuong_trinh"])
        preference = TieuChiUuTien.objects.create(sinh_vien=self.sv)

        schedule = suggest_timetable_csp(
            [self.mon2.ma_mon], self.dot, self.sv, preference
        )

        self.assertIsNone(schedule)

    def test_dashboard_saves_student_preferences(self):
        self.client.force_login(self.user)
        MonHocDaHoanThanh.objects.create(
            sinh_vien=self.sv,
            mon_hoc=self.mon2,
            diem="8.00",
        )
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Môn học đã hoàn thành")
        self.assertContains(response, "Cơ sở dữ liệu")

        response = self.client.post(
            reverse("dashboard"),
            {
                "action_save_preferences": "1",
                "ca_uu_tien": "CHIEU",
                "so_ngay_hoc_toi_da": "3",
                "han_che_tiet_trong": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        preference = TieuChiUuTien.objects.get(sinh_vien=self.sv)
        self.assertEqual(preference.ca_uu_tien, "CHIEU")
        self.assertEqual(preference.so_ngay_hoc_toi_da, 3)
        self.assertTrue(preference.han_che_tiet_trong)

    def test_staff_dashboard_redirects_to_admin_site(self):
        admin = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="AdminPass123!",
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("admin:index"))
        admin_response = self.client.get(reverse("admin:index"))
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "HỆ THỐNG ĐĂNG KÝ MÔN HỌC")
        self.assertContains(admin_response, "Các phân hệ quản lý")
        self.assertContains(admin_response, "Chương trình đào tạo")
        self.assertContains(admin_response, "registration/admin.css")

        program = ChuongTrinhDaoTao.objects.create(
            ma_chuong_trinh="ADMIN-2026",
            ten_chuong_trinh="Chương trình kiểm tra",
            nganh="Công nghệ thông tin",
            khoa_ap_dung="2026",
        )
        change_response = self.client.get(
            reverse(
                "admin:registration_chuongtrinhdaotao_change",
                args=[program.pk],
            )
        )
        self.assertEqual(change_response.status_code, 200)
        self.assertContains(change_response, "Quay lại danh sách")
        self.assertContains(
            change_response,
            reverse("admin:registration_chuongtrinhdaotao_changelist"),
        )


    def test_signup_requires_and_assigns_training_program(self):
        program = ChuongTrinhDaoTao.objects.create(
            ma_chuong_trinh="CNTT-2026",
            ten_chuong_trinh="Công nghệ thông tin",
            nganh="Công nghệ thông tin",
            khoa_ap_dung="2026",
        )

        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_student",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "mssv": "20269999",
                "ho_ten": "Sinh viên mới",
                "lop": "CNTT-K2026",
                "chuong_trinh": program.ma_chuong_trinh,
            },
        )

        self.assertEqual(response.status_code, 302)
        student = SinhVien.objects.get(mssv="20269999")
        self.assertEqual(student.chuong_trinh, program)
        self.assertEqual(student.nganh, program.nganh)

    def test_dashboard_renders_preference_scored_schedule(self):
        self.client.force_login(self.user)
        additional_sections = [
            ("INT101_02", 3, "CHIEU", 1),
            ("INT101_03", 4, "SANG", 1),
        ]
        for section_id, weekday, shift, first_period in additional_sections:
            LopHocPhan.objects.create(
                ma_lhp=section_id,
                mon_hoc=self.mon1,
                giang_vien="GV Khác",
                thu=weekday,
                ca_hoc=shift,
                tiet_bat_dau=first_period,
                so_tiet=3,
                si_so_toi_da=40,
            )

        response = self.client.post(
            reverse("dashboard"),
            {"action_suggest": "1", "selected_mon": [self.mon1.ma_mon]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thời khóa biểu đề xuất")
        self.assertContains(response, self.lhp1.ma_lhp)
        self.assertContains(response, "Phương án 1")
        self.assertContains(response, "Phương án 2")
        self.assertContains(response, "Phương án 3")
        self.assertContains(response, "Đăng ký toàn bộ thời khóa biểu")

    def test_schedule_search_explains_missing_prerequisite(self):
        advanced_course = MonHoc.objects.create(
            ma_mon="INT110",
            ten_mon="Học máy và Khai phá dữ liệu",
            so_tin_chi=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT110_01",
            mon_hoc=advanced_course,
            giang_vien="GV A",
            thu=3,
            ca_hoc="CHIEU",
            tiet_bat_dau=6,
            so_tiet=3,
        )
        MonTienQuyet.objects.create(
            mon_hoc=advanced_course,
            mon_tien_quyet=self.mon1,
            loai_dieu_kien="TIEN_QUYET",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("dashboard"),
            {"action_suggest": "1", "selected_mon": [advanced_course.ma_mon]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "yêu cầu bạn hoàn thành")
        self.assertContains(response, "Lập trình Python")
        self.assertContains(response, "Lịch các môn tiên quyết cần học trước")
        self.assertContains(response, self.lhp1.ma_lhp)
        self.assertContains(response, "Thứ 2")

    def test_schedule_search_returns_up_to_three_distinct_feasible_options(self):
        LopHocPhan.objects.create(
            ma_lhp="INT101_02",
            mon_hoc=self.mon1,
            giang_vien="GV B",
            thu=3,
            ca_hoc="CHIEU",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        LopHocPhan.objects.create(
            ma_lhp="INT101_03",
            mon_hoc=self.mon1,
            giang_vien="GV C",
            thu=4,
            ca_hoc="SANG",
            tiet_bat_dau=1,
            so_tiet=3,
        )
        preference = TieuChiUuTien.objects.create(sinh_vien=self.sv)

        options = suggest_timetable_options_csp(
            [self.mon1.ma_mon], self.dot, self.sv, preference
        )

        self.assertEqual(len(options), 3)
        self.assertEqual(
            len({option["courses"][0].ma_lhp for option in options}),
            3,
        )

    def test_batch_registration_rolls_back_on_schedule_conflict(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("register_schedule"),
            {"selected_lhp": [self.lhp1.ma_lhp, self.lhp2.ma_lhp]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(DangKy.objects.filter(sinh_vien=self.sv).count(), 0)
        self.lhp1.refresh_from_db()
        self.lhp2.refresh_from_db()
        self.assertEqual(self.lhp1.si_so_hien_tai, 0)
        self.assertEqual(self.lhp2.si_so_hien_tai, 0)

    def test_batch_registration_accepts_selected_corequisite_pair(self):
        MonTienQuyet.objects.create(
            mon_hoc=self.mon2,
            mon_tien_quyet=self.mon1,
            loai_dieu_kien="SONG_HANH",
        )
        second_section = LopHocPhan.objects.create(
            ma_lhp="INT102_02",
            mon_hoc=self.mon2,
            giang_vien="GV C",
            thu=3,
            ca_hoc="SANG",
            tiet_bat_dau=1,
            so_tiet=3,
            si_so_toi_da=40,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("register_schedule"),
            {"selected_lhp": [self.lhp1.ma_lhp, second_section.ma_lhp]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(DangKy.objects.filter(sinh_vien=self.sv).count(), 2)