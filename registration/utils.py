from django.utils import timezone
from django.db.models import F

from .models import (
    DangKy,
    LopHocPhan,
    MonHocDaHoanThanh,
    MonTienQuyet,
)


def check_time_conflict(lhp1, lhp2):
    """Return whether two course sections overlap on the same weekday."""
    if lhp1.thu != lhp2.thu:
        return False

    end1 = lhp1.tiet_bat_dau + lhp1.so_tiet - 1
    end2 = lhp2.tiet_bat_dau + lhp2.so_tiet - 1
    return max(lhp1.tiet_bat_dau, lhp2.tiet_bat_dau) <= min(end1, end2)


def _course_ids_in_curriculum(sinh_vien):
    if not sinh_vien.chuong_trinh_id:
        return None
    return set(
        sinh_vien.chuong_trinh.chuongtrinhmonhoc_set.values_list(
            "mon_hoc_id", flat=True
        )
    )


def _completed_course_ids(sinh_vien):
    return set(
        MonHocDaHoanThanh.objects.filter(sinh_vien=sinh_vien).values_list(
            "mon_hoc_id", flat=True
        )
    )


def validate_registration(
    sinh_vien,
    lhp,
    dot_dang_ky,
    planned_course_ids=None,
):
    """Validate a class against enrollment, curriculum, prerequisite, and schedule rules."""
    now = timezone.now()
    if (
        not dot_dang_ky.kich_hoat
        or not dot_dang_ky.ngay_bat_dau <= now <= dot_dang_ky.ngay_ket_thuc
    ):
        return False, "Đợt đăng ký hiện tại đang đóng hoặc không hợp lệ!"

    if dot_dang_ky.hoc_ky_id:
        if lhp.hoc_ky_id != dot_dang_ky.hoc_ky_id:
            return False, "Lớp học phần không thuộc học kỳ của đợt đăng ký!"
    elif lhp.hoc_ky_id:
        return False, "Đợt đăng ký chưa được liên kết với học kỳ của lớp học phần."

    curriculum_course_ids = _course_ids_in_curriculum(sinh_vien)
    if curriculum_course_ids is not None and lhp.mon_hoc_id not in curriculum_course_ids:
        return False, "Môn học không thuộc chương trình đào tạo của bạn!"

    if lhp.si_so_hien_tai >= lhp.si_so_toi_da:
        return False, "Lớp học phần đã hết sĩ số trống!"

    completed_course_ids = _completed_course_ids(sinh_vien)
    if lhp.mon_hoc_id in completed_course_ids:
        return False, "Bạn đã hoàn thành môn học này nên không thể đăng ký lại trong đợt này."
    registered_course_ids = set(
        DangKy.objects.filter(sinh_vien=sinh_vien, dot_dang_ky=dot_dang_ky)
        .values_list("lop_hoc_phan__mon_hoc_id", flat=True)
    )
    planned_course_ids = set(planned_course_ids or ())
    for condition in MonTienQuyet.objects.filter(mon_hoc=lhp.mon_hoc):
        if condition.loai_dieu_kien == "TIEN_QUYET":
            if condition.mon_tien_quyet_id not in completed_course_ids:
                return False, (
                    f"Bạn chưa hoàn thành môn tiên quyết "
                    f"{condition.mon_tien_quyet.ten_mon}."
                )
        elif condition.mon_tien_quyet_id not in (
            completed_course_ids | registered_course_ids | planned_course_ids
        ):
            return False, (
                f"Môn {condition.mon_tien_quyet.ten_mon} là môn song hành; "
                "hãy chọn hoặc đăng ký môn này cùng đợt."
            )

    registered_sections = (
        DangKy.objects.filter(sinh_vien=sinh_vien, dot_dang_ky=dot_dang_ky)
        .select_related("lop_hoc_phan__mon_hoc")
    )
    for enrollment in registered_sections:
        registered_section = enrollment.lop_hoc_phan
        if registered_section == lhp:
            return False, "Bạn đã đăng ký lớp học phần này rồi!"
        if registered_section.mon_hoc_id == lhp.mon_hoc_id:
            return False, f"Bạn đã đăng ký một lớp khác của môn {lhp.mon_hoc.ten_mon}!"
        if check_time_conflict(lhp, registered_section):
            return False, (
                f"Lịch học bị trùng với lớp {registered_section.ma_lhp} "
                f"({registered_section.mon_hoc.ten_mon})!"
            )

    return True, "Hợp lệ"


def _schedule_score(schedule, preferences, fixed_sections=()):
    study_days = {}
    gaps = 0
    preferred_shift = preferences.ca_uu_tien
    score = 0

    for section in [*fixed_sections, *schedule]:
        study_days.setdefault(section.thu, []).append(
            (section.tiet_bat_dau, section.tiet_bat_dau + section.so_tiet - 1)
        )
        if preferred_shift != "BAT_KY":
            score += 10 if section.ca_hoc == preferred_shift else -4

    for intervals in study_days.values():
        intervals.sort()
        for (_, previous_end), (next_start, _) in zip(intervals, intervals[1:]):
            gaps += max(0, next_start - previous_end - 1)

    number_of_days = len(study_days)
    score -= number_of_days * 5
    score -= max(0, number_of_days - preferences.so_ngay_hoc_toi_da) * 25
    if preferences.han_che_tiet_trong:
        score -= gaps * 4
    return score


def _has_no_conflicts(schedule, fixed_sections):
    combined = list(fixed_sections)
    for section in schedule:
        if any(check_time_conflict(section, fixed) for fixed in combined):
            return False
        if any(existing.mon_hoc_id == section.mon_hoc_id for existing in combined):
            return False
        combined.append(section)
    return True


def suggest_timetable_options_csp(
    mon_hoc_ids,
    dot_dang_ky,
    sinh_vien,
    preferences,
    max_options=3,
):
    """Return up to three high-scoring distinct schedules within a bounded search."""
    requested_ids = list(dict.fromkeys(mon_hoc_ids))
    if not requested_ids:
        return []

    curriculum_course_ids = _course_ids_in_curriculum(sinh_vien)
    if curriculum_course_ids is not None and not set(requested_ids).issubset(
        curriculum_course_ids
    ):
        return []

    completed_course_ids = _completed_course_ids(sinh_vien)
    if set(requested_ids) & completed_course_ids:
        return []
    registered_sections = list(
        LopHocPhan.objects.filter(
            dangky__sinh_vien=sinh_vien,
            dangky__dot_dang_ky=dot_dang_ky,
        ).select_related("mon_hoc")
    )
    registered_course_ids = {section.mon_hoc_id for section in registered_sections}
    requested_ids = [
        course_id for course_id in requested_ids if course_id not in registered_course_ids
    ]
    if not requested_ids:
        return []

    selected_ids = set(requested_ids)
    for condition in MonTienQuyet.objects.filter(
        mon_hoc_id__in=selected_ids,
        loai_dieu_kien="TIEN_QUYET",
    ):
        if condition.mon_tien_quyet_id not in completed_course_ids:
            return []

    for condition in MonTienQuyet.objects.filter(
        mon_hoc_id__in=selected_ids,
        loai_dieu_kien="SONG_HANH",
    ):
        if condition.mon_tien_quyet_id not in (
            selected_ids | completed_course_ids | registered_course_ids
        ):
            return []

    courses = {}
    for course_id in requested_ids:
        sections = LopHocPhan.objects.filter(
            mon_hoc_id=course_id,
            si_so_hien_tai__lt=F("si_so_toi_da"),
        )
        if dot_dang_ky.hoc_ky_id:
            sections = sections.filter(hoc_ky_id=dot_dang_ky.hoc_ky_id)
        else:
            sections = sections.filter(hoc_ky__isnull=True)
        courses[course_id] = list(sections.select_related("mon_hoc", "phong_hoc"))
    if any(not sections for sections in courses.values()):
        return []

    ordered_course_ids = sorted(requested_ids, key=lambda course_id: len(courses[course_id]))
    schedule = []
    options = []
    seen_signatures = set()
    visited_nodes = 0
    max_search_nodes = 50000

    def search_schedules(index):
        nonlocal visited_nodes
        visited_nodes += 1
        if visited_nodes > max_search_nodes:
            return
        if index == len(ordered_course_ids):
            ordered_schedule = sorted(
                schedule,
                key=lambda section: (section.thu, section.tiet_bat_dau, section.ma_lhp),
            )
            signature = tuple(section.ma_lhp for section in ordered_schedule)
            if signature in seen_signatures:
                return
            seen_signatures.add(signature)
            options.append(
                {
                    "courses": ordered_schedule,
                    "score": _schedule_score(
                        ordered_schedule, preferences, registered_sections
                    ),
                }
            )
            options.sort(
                key=lambda option: (
                    -option["score"],
                    tuple(section.ma_lhp for section in option["courses"]),
                )
            )
            del options[max_options:]
            return

        course_id = ordered_course_ids[index]
        feasible = [
            section
            for section in courses[course_id]
            if _has_no_conflicts([*schedule, section], registered_sections)
        ]
        feasible.sort(
            key=lambda option: _schedule_score(
                [*schedule, option], preferences, registered_sections
            ),
            reverse=True,
        )
        for section in feasible:
            schedule.append(section)
            search_schedules(index + 1)
            schedule.pop()
            if visited_nodes >= max_search_nodes:
                break

    search_schedules(0)
    return options


def suggest_timetable_csp(mon_hoc_ids, dot_dang_ky, sinh_vien, preferences):
    """Return the highest-scoring feasible schedule for existing single-result callers."""
    options = suggest_timetable_options_csp(
        mon_hoc_ids, dot_dang_ky, sinh_vien, preferences, max_options=1
    )
    return options[0] if options else None
