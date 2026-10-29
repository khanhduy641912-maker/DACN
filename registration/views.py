import logging
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import TieuChiUuTienForm
from .models import (
    ChuongTrinhDaoTao,
    DangKy,
    DotDangKy,
    LopHocPhan,
    MonHoc,
    MonHocDaHoanThanh,
    MonTienQuyet,
    SinhVien,
    TieuChiUuTien,
)
from .utils import validate_registration, suggest_timetable_options_csp
from django.db.models import Q
from django.utils import timezone

# Cấu hình Logger ghi nhật ký giao dịch
logger = logging.getLogger('registration_audit')
logging.basicConfig(
    filename='registration.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


def _active_registration_period():
    now = timezone.now()
    return (
        DotDangKy.objects.filter(
            kich_hoat=True,
            ngay_bat_dau__lte=now,
            ngay_ket_thuc__gte=now,
        )
        .select_related("hoc_ky")
        .order_by("ngay_bat_dau")
        .first()
    )


# 1. View Đăng nhập
def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin:index' if request.user.is_staff else 'dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            logger.info(f"User '{u}' đăng nhập thành công.")
            return redirect('admin:index' if user.is_staff else 'dashboard')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác!")
            logger.warning(f"Thất bại đăng nhập với username '{u}'.")
            
    return render(request, 'registration/login.html')

# 2. View Đăng ký tài khoản Sinh viên mới
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    programs = ChuongTrinhDaoTao.objects.order_by(
        "nganh", "khoa_ap_dung", "ma_chuong_trinh"
    )

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        mssv = request.POST.get('mssv', '').strip()
        ho_ten = request.POST.get('ho_ten', '').strip()
        lop = request.POST.get('lop', '').strip()
        chuong_trinh = programs.filter(
            pk=request.POST.get("chuong_trinh", "").strip()
        ).first()

        if not chuong_trinh:
            messages.error(request, "Vui lòng chọn chương trình đào tạo hợp lệ.")
            return render(
                request,
                'registration/signup.html',
                {'programs': programs},
            )

        if password != confirm_password:
            messages.error(request, "Mật khẩu xác nhận không trùng khớp!")
            return render(request, 'registration/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại trên hệ thống!")
            return render(request, 'registration/signup.html')

        if SinhVien.objects.filter(mssv=mssv).exists():
            messages.error(request, "Mã số sinh viên (MSSV) này đã được đăng ký!")
            return render(request, 'registration/signup.html')

        try:
            with transaction.atomic():
                new_user = User.objects.create_user(username=username, password=password)
                SinhVien.objects.create(
                    user=new_user,
                    mssv=mssv,
                    ho_ten=ho_ten,
                    lop=lop,
                    nganh=chuong_trinh.nganh,
                    chuong_trinh=chuong_trinh,
                )
            messages.success(request, "Tạo tài khoản thành công! Bạn có thể đăng nhập ngay.")
            logger.info(f"Sinh viên mới đăng ký tài khoản: MSSV {mssv} - User {username}")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Lỗi đăng ký tài khoản: {str(e)}")

    return render(request, 'registration/signup.html', {'programs': programs})

# 3. View Đăng xuất
def logout_view(request):
    username = request.user.username
    logout(request)
    logger.info(f"User '{username}' đã đăng xuất.")
    return redirect('login')

# 4. View Dashboard chính (Có Lọc, Tìm kiếm, Phân trang & Thuật toán CSP)
@login_required
def dashboard_view(request):
    if request.user.is_staff:
        return redirect('admin:index')

    try:
        sinh_vien = request.user.profile
    except SinhVien.DoesNotExist:
        messages.error(request, "Tài khoản chưa liên kết hồ sơ Sinh viên!")
        return render(request, 'registration/dashboard.html', {'sinh_vien': None})

    active_dot = _active_registration_period()
    preferences, _ = TieuChiUuTien.objects.get_or_create(sinh_vien=sinh_vien)
    preference_form = TieuChiUuTienForm(instance=preferences)

    if request.method == 'POST' and 'action_save_preferences' in request.POST:
        preference_form = TieuChiUuTienForm(request.POST, instance=preferences)
        if preference_form.is_valid():
            preference_form.save()
            messages.success(request, "Đã lưu tiêu chí ưu tiên thời khóa biểu.")
            return redirect('dashboard')
        messages.error(request, "Vui lòng kiểm tra lại tiêu chí ưu tiên.")
    
    # Lấy tham số Tìm kiếm & Lọc
    search_query = request.GET.get('search', '').strip()
    ca_filter = request.GET.get('ca_hoc', '').strip()

    lhp_qs = LopHocPhan.objects.all().select_related('mon_hoc', 'phong_hoc')
    if not active_dot:
        lhp_qs = lhp_qs.none()
    elif active_dot.hoc_ky_id:
        lhp_qs = lhp_qs.filter(hoc_ky_id=active_dot.hoc_ky_id)
    else:
        lhp_qs = lhp_qs.filter(hoc_ky__isnull=True)
    if sinh_vien.chuong_trinh_id:
        lhp_qs = lhp_qs.filter(
            mon_hoc__chuong_trinh_dao_tao=sinh_vien.chuong_trinh
        )

    # TÌM KIẾM THÔNG MINH BẰNG Q OBJECTS
    if search_query:
        lhp_qs = lhp_qs.filter(
            Q(mon_hoc__ten_mon__icontains=search_query) |  
            Q(mon_hoc__ma_mon__icontains=search_query)  |  
            Q(ma_lhp__icontains=search_query)           | 
            Q(giang_vien__icontains=search_query)         
        ).distinct()

    if ca_filter in ['SANG', 'CHIEU']:
        lhp_qs = lhp_qs.filter(ca_hoc=ca_filter)

    # Phân trang (10 LHP / trang)
    paginator = Paginator(lhp_qs.order_by('ma_lhp'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Danh sách môn đã đăng ký
    registered_lhps = []
    registered_ids = []
    if active_dot:
        dangkys = DangKy.objects.filter(
            sinh_vien=sinh_vien, dot_dang_ky=active_dot
        ).select_related('lop_hoc_phan__mon_hoc', 'lop_hoc_phan__phong_hoc')
        registered_lhps = [dk.lop_hoc_phan for dk in dangkys]
        registered_ids = [lhp.ma_lhp for lhp in registered_lhps]

    # Xử lý gợi ý TKB CSP
    suggested_schedules = []
    selected_mon_ids = []
    prerequisite_schedule_groups = []
    completed_course_ids = set(
        sinh_vien.mon_hoc_da_hoan_thanh.values_list("mon_hoc_id", flat=True)
    )
    registered_course_ids = set(
        DangKy.objects.filter(
            sinh_vien=sinh_vien,
            dot_dang_ky=active_dot,
        ).values_list("lop_hoc_phan__mon_hoc_id", flat=True)
    ) if active_dot else set()
    if request.method == 'POST' and 'action_suggest' in request.POST:
        selected_mon_ids = list(dict.fromkeys(request.POST.getlist('selected_mon')))
        if not active_dot:
            messages.error(request, "Hiện không có đợt đăng ký đang diễn ra.")
        elif not selected_mon_ids:
            messages.warning(request, "Hãy chọn ít nhất một môn học để tìm thời khóa biểu.")
        else:
            suggested_schedules = suggest_timetable_options_csp(
                selected_mon_ids, active_dot, sinh_vien, preferences
            )
            if not suggested_schedules:
                missing_prerequisite = (
                    MonTienQuyet.objects.filter(
                        mon_hoc_id__in=selected_mon_ids,
                        loai_dieu_kien="TIEN_QUYET",
                    )
                    .exclude(mon_tien_quyet_id__in=completed_course_ids)
                    .select_related("mon_hoc", "mon_tien_quyet")
                    .first()
                )
                if missing_prerequisite:
                    missing_prerequisites = list(
                        MonTienQuyet.objects.filter(
                            mon_hoc_id__in=selected_mon_ids,
                            loai_dieu_kien="TIEN_QUYET",
                        )
                        .exclude(mon_tien_quyet_id__in=completed_course_ids)
                        .select_related("mon_hoc", "mon_tien_quyet")
                        .order_by("mon_tien_quyet__ma_mon", "mon_hoc__ma_mon")
                    )
                    prerequisite_course_ids = list(
                        dict.fromkeys(
                            condition.mon_tien_quyet_id
                            for condition in missing_prerequisites
                        )
                    )
                    prerequisite_sections = LopHocPhan.objects.filter(
                        mon_hoc_id__in=prerequisite_course_ids,
                        si_so_hien_tai__lt=F("si_so_toi_da"),
                    ).select_related("mon_hoc", "phong_hoc", "hoc_ky")
                    if active_dot.hoc_ky_id:
                        prerequisite_sections = prerequisite_sections.filter(
                            hoc_ky_id=active_dot.hoc_ky_id
                        )
                    else:
                        prerequisite_sections = prerequisite_sections.filter(
                            hoc_ky__isnull=True
                        )
                    sections_by_course = {}
                    for section in prerequisite_sections.order_by(
                        "mon_hoc_id", "thu", "tiet_bat_dau", "ma_lhp"
                    ):
                        sections_by_course.setdefault(
                            section.mon_hoc_id, []
                        ).append(section)
                    prerequisite_schedule_groups = [
                        {
                            "condition": condition,
                            "sections": sections_by_course.get(
                                condition.mon_tien_quyet_id, []
                            ),
                        }
                        for condition in missing_prerequisites
                    ]
                    messages.warning(
                        request,
                        f"Chưa tìm được lịch: môn {missing_prerequisite.mon_hoc.ten_mon} "
                        f"({missing_prerequisite.mon_hoc_id}) yêu cầu bạn hoàn thành "
                        f"môn tiên quyết {missing_prerequisite.mon_tien_quyet.ten_mon} "
                        f"({missing_prerequisite.mon_tien_quyet_id}) trước.",
                    )
                else:
                    missing_corequisite = (
                        MonTienQuyet.objects.filter(
                            mon_hoc_id__in=selected_mon_ids,
                            loai_dieu_kien="SONG_HANH",
                        )
                        .exclude(
                            mon_tien_quyet_id__in=(
                                completed_course_ids
                                | set(selected_mon_ids)
                                | set(registered_course_ids)
                            )
                        )
                        .select_related("mon_hoc", "mon_tien_quyet")
                        .first()
                    )
                    if missing_corequisite:
                        messages.warning(
                            request,
                            f"Chưa tìm được lịch: môn {missing_corequisite.mon_hoc.ten_mon} "
                            f"cần đăng ký đồng thời môn "
                            f"{missing_corequisite.mon_tien_quyet.ten_mon}.",
                        )
                    else:
                        messages.warning(
                            request,
                            "Không tìm thấy phương án phù hợp. Có thể các lớp đã hết chỗ, "
                            "không thuộc học kỳ/chương trình, hoặc bị trùng lịch với các "
                            "môn đã đăng ký.",
                        )
            else:
                messages.success(
                    request,
                    f"Đã tìm được {len(suggested_schedules)} phương án thời khóa biểu phù hợp.",
                )

    available_sections = lhp_qs.filter(si_so_hien_tai__lt=F("si_so_toi_da"))
    all_mon_hoc = MonHoc.objects.filter(
        lophocphan__in=available_sections
    ).exclude(
        ma_mon__in=completed_course_ids | registered_course_ids
    ).prefetch_related("mon_chinh__mon_tien_quyet").distinct().order_by('ma_mon')
    completed_courses = MonHocDaHoanThanh.objects.filter(
        sinh_vien=sinh_vien
    ).select_related("mon_hoc", "hoc_ky").order_by("mon_hoc__ma_mon")

    context = {
        'sinh_vien': sinh_vien,
        'active_dot': active_dot,
        'page_obj': page_obj,
        'registered_lhps': registered_lhps,
        'registered_ids': registered_ids,
        'all_mon_hoc': all_mon_hoc,
        'suggested_schedules': suggested_schedules,
        'prerequisite_schedule_groups': prerequisite_schedule_groups,
        'search_query': search_query,
        'ca_filter': ca_filter,
        'preferences': preferences,
        'preference_form': preference_form,
        'selected_mon_ids': selected_mon_ids,
        'completed_course_ids': completed_course_ids,
        'completed_courses': completed_courses,
    }
    return render(request, 'registration/dashboard.html', context)


@login_required
@require_POST
def register_schedule(request):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = _active_registration_period()
    if not active_dot:
        messages.error(request, "Hiện không có đợt đăng ký nào mở!")
        return redirect('dashboard')

    section_ids = list(dict.fromkeys(request.POST.getlist("selected_lhp")))
    if not section_ids:
        messages.error(request, "Thời khóa biểu không có lớp học phần để đăng ký.")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            sinh_vien = SinhVien.objects.select_for_update().get(pk=sinh_vien.pk)
            sections = list(
                LopHocPhan.objects.select_for_update()
                .filter(ma_lhp__in=section_ids)
                .select_related("mon_hoc")
                .order_by("ma_lhp")
            )
            if len(sections) != len(section_ids):
                raise ValueError("Một hoặc nhiều lớp học phần không còn tồn tại.")

            course_ids = [section.mon_hoc_id for section in sections]
            if len(course_ids) != len(set(course_ids)):
                raise ValueError("Thời khóa biểu có nhiều lớp của cùng một môn.")

            for section in sections:
                valid, reason = validate_registration(
                    sinh_vien,
                    section,
                    active_dot,
                    planned_course_ids=course_ids,
                )
                if not valid:
                    raise ValueError(reason)

                DangKy.objects.create(
                    sinh_vien=sinh_vien,
                    lop_hoc_phan=section,
                    dot_dang_ky=active_dot,
                )
                section.si_so_hien_tai += 1
                section.save(update_fields=["si_so_hien_tai"])

        messages.success(
            request,
            f"Đăng ký thành công {len(sections)} lớp học phần theo thời khóa biểu.",
        )
        logger.info(
            "SUCCESS: SV %s đăng ký thời khóa biểu gồm %s lớp trong đợt %s",
            sinh_vien.mssv,
            len(sections),
            active_dot.pk,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
    except Exception:
        logger.exception("Lỗi đăng ký thời khóa biểu của sinh viên %s", sinh_vien.mssv)
        messages.error(request, "Đăng ký thất bại do lỗi dữ liệu. Vui lòng thử lại.")

    return redirect('dashboard')


# 5. View Đăng ký Môn học (Khóa dòng Row-Level Lock chống Race Condition)
@login_required
@require_POST
def register_course(request, ma_lhp):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = _active_registration_period()

    if not active_dot:
        messages.error(request, "Hiện không có đợt đăng ký nào mở!")
        return redirect('dashboard')

    try:
        # Sử dụng select_for_update() để khóa dòng trong PostgreSQL
        with transaction.atomic():
            sinh_vien = SinhVien.objects.select_for_update().get(pk=sinh_vien.pk)
            lhp = LopHocPhan.objects.select_for_update().get(ma_lhp=ma_lhp)
            
            is_valid, msg = validate_registration(sinh_vien, lhp, active_dot)
            if not is_valid:
                messages.error(request, msg)
                return redirect('dashboard')

            DangKy.objects.create(
                sinh_vien=sinh_vien,
                lop_hoc_phan=lhp,
                dot_dang_ky=active_dot
            )
            lhp.si_so_hien_tai += 1
            lhp.save()

            logger.info(f"SUCCESS: SV {sinh_vien.mssv} đã đăng ký LHP {lhp.ma_lhp}")
            messages.success(request, f"Đăng ký thành công lớp {lhp.ma_lhp} ({lhp.mon_hoc.ten_mon})!")

    except Exception as e:
        logger.error(f"ERROR: SV {sinh_vien.mssv} đăng ký LHP {ma_lhp} thất bại: {str(e)}")
        messages.error(request, f"Thao tác thất bại do xung đột dữ liệu. Vui lòng thử lại!")

    return redirect('dashboard')

# 6. View Hủy Đăng ký Môn học
@login_required
@require_POST
def cancel_course(request, ma_lhp):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = _active_registration_period()
    if not active_dot:
        messages.error(request, "Hiện không có đợt đăng ký nào mở để hủy môn.")
        return redirect('dashboard')

    try:
        with transaction.atomic():
            sinh_vien = SinhVien.objects.select_for_update().get(pk=sinh_vien.pk)
            lhp = LopHocPhan.objects.select_for_update().get(ma_lhp=ma_lhp)
            dk = DangKy.objects.filter(
                sinh_vien=sinh_vien, lop_hoc_phan=lhp, dot_dang_ky=active_dot
            ).first()

            if dk:
                dk.delete()
                if lhp.si_so_hien_tai > 0:
                    lhp.si_so_hien_tai -= 1
                    lhp.save()
                logger.info(f"CANCEL: SV {sinh_vien.mssv} đã hủy LHP {lhp.ma_lhp}")
                messages.success(request, f"Đã hủy đăng ký lớp {lhp.ma_lhp}!")
            else:
                messages.error(request, "Không tìm thấy thông tin đăng ký!")

    except Exception as e:
        logger.error(f"ERROR: SV {sinh_vien.mssv} hủy LHP {ma_lhp} thất bại: {str(e)}")
        messages.error(request, "Có lỗi xảy ra khi hủy môn học!")

    return redirect('dashboard')

# 7. View Xuất Thời khóa biểu dạng CSV
@login_required
def export_schedule_csv(request):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = _active_registration_period()

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="ThoiKhoaBieu_{sinh_vien.mssv}.csv"'

    writer = csv.writer(response)
    writer.writerow(['STT', 'Mã LHP', 'Tên Môn Học', 'Số Tín Chỉ', 'Giảng Viên', 'Thứ', 'Ca Học', 'Tiết BĐ', 'Phòng'])

    if active_dot:
        dangkys = DangKy.objects.filter(
            sinh_vien=sinh_vien, dot_dang_ky=active_dot
        ).select_related('lop_hoc_phan__mon_hoc', 'lop_hoc_phan__phong_hoc')

        for idx, dk in enumerate(dangkys, 1):
            lhp = dk.lop_hoc_phan
            writer.writerow([
                idx, lhp.ma_lhp, lhp.mon_hoc.ten_mon, lhp.mon_hoc.so_tin_chi,
                lhp.giang_vien, f"Thứ {lhp.thu}", lhp.ca_hoc, lhp.tiet_bat_dau,
                lhp.phong_hoc.ma_phong if lhp.phong_hoc else ''
            ])

    return response

# 8. Custom Error Views (404 & 500)
def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

def custom_server_error(request):
    return render(request, '500.html', status=500)