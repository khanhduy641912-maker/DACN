from django.utils import timezone
from .models import LopHocPhan, DangKy, DotDangKy, MonTienQuyet, SinhVien

def check_time_conflict(lhp1, lhp2):
    """
    Kiểm tra 2 lớp học phần có trùng lịch (Thứ, Ca, Tiết) hay không.
    Trả về True nếu TRÙNG, False nếu KHÔNG TRÙNG.
    """
    if lhp1.thu != lhp2.thu:
        return False
    
    start1 = lhp1.tiet_bat_dau
    end1 = lhp1.tiet_bat_dau + lhp1.so_tiet - 1
    
    start2 = lhp2.tiet_bat_dau
    end2 = lhp2.tiet_bat_dau + lhp2.so_tiet - 1
    
    return max(start1, start2) <= min(end1, end2)


def validate_registration(sinh_vien, lhp, dot_dang_ky):
    """
    Kiểm tra 4 ràng buộc cứng trước khi đăng ký.
    Trả về (True, "Thành công") hoặc (False, "Lý do lỗi").
    """
    now = timezone.now()
    
    # 1. Kiểm tra đợt đăng ký có mở không
    if not dot_dang_ky.kich_hoat or not (dot_dang_ky.ngay_bat_dau <= now <= dot_dang_ky.ngay_ket_thuc):
        return False, "Đợt đăng ký hiện tại đang đóng hoặc không hợp lệ!"

    # 2. Kiểm tra sĩ số lớp
    if lhp.si_so_hien_tai >= lhp.si_so_toi_da:
        return False, "Lớp học phần đã hết sĩ số trống!"

    # 3. Kiểm tra môn tiên quyết
    mon_tien_quyets = MonTienQuyet.objects.filter(mon_hoc=lhp.mon_hoc)
    for tp in mon_tien_quyets:
        pass 

    # 4. Kiểm tra trùng lịch với các môn đã đăng ký trong đợt
    dangkys = DangKy.objects.filter(sinh_vien=sinh_vien, dot_dang_ky=dot_dang_ky)
    for dk in dangkys:
        if dk.lop_hoc_phan == lhp:
            return False, "Bạn đã đăng ký lớp học phần này rồi!"
        if dk.lop_hoc_phan.mon_hoc == lhp.mon_hoc:
            return False, f"Bạn đã đăng ký 1 lớp khác của môn {lhp.mon_hoc.ten_mon}!"
        if check_time_conflict(lhp, dk.lop_hoc_phan):
            return False, f"Lịch học bị trùng với lớp {dk.lop_hoc_phan.ma_lhp} ({dk.lop_hoc_phan.mon_hoc.ten_mon})!"

    return True, "Hợp lệ"


def suggest_timetable_csp(mon_hoc_ids, dot_dang_ky):
    """
    Thuật toán Gợi ý TKB không trùng lịch (CSP/Greedy Backtracking)
    Dựa trên danh sách mã môn học được chọn.
    """
    lhps_by_mon = []
    for m_id in mon_hoc_ids:
        lhps = list(LopHocPhan.objects.filter(mon_hoc_id=m_id))
        if lhps:
            lhps_by_mon.append(lhps)

    if not lhps_by_mon:
        return []

    valid_schedules = []

    def backtrack(index, current_schedule):
        if index == len(lhps_by_mon):
            valid_schedules.append(list(current_schedule))
            return
        
        for lhp in lhps_by_mon[index]:
            conflict = False
            for selected_lhp in current_schedule:
                if check_time_conflict(lhp, selected_lhp):
                    conflict = True
                    break
            
            if not conflict:
                current_schedule.append(lhp)
                backtrack(index + 1, current_schedule)
                current_schedule.pop()

    backtrack(0, [])
    return valid_schedules