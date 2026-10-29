import logging
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import SinhVien, LopHocPhan, DangKy, DotDangKy, MonHoc
from .utils import validate_registration, suggest_timetable_csp
from django.db.models import Q

# Cấu hình Logger ghi nhật ký giao dịch
logger = logging.getLogger('registration_audit')
logging.basicConfig(
    filename='registration.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# 1. View Đăng nhập
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            logger.info(f"User '{u}' đăng nhập thành công.")
            return redirect('dashboard')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác!")
            logger.warning(f"Thất bại đăng nhập với username '{u}'.")
            
    return render(request, 'registration/login.html')

# 2. View Đăng ký tài khoản Sinh viên mới
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        mssv = request.POST.get('mssv', '').strip()
        ho_ten = request.POST.get('ho_ten', '').strip()
        lop = request.POST.get('lop', '').strip()
        nganh = request.POST.get('nganh', '').strip()

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
                    user=new_user, mssv=mssv, ho_ten=ho_ten, lop=lop, nganh=nganh
                )
            messages.success(request, "Tạo tài khoản thành công! Bạn có thể đăng nhập ngay.")
            logger.info(f"Sinh viên mới đăng ký tài khoản: MSSV {mssv} - User {username}")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Lỗi đăng ký tài khoản: {str(e)}")

    return render(request, 'registration/signup.html')

# 3. View Đăng xuất
def logout_view(request):
    username = request.user.username
    logout(request)
    logger.info(f"User '{username}' đã đăng xuất.")
    return redirect('login')

# 4. View Dashboard chính (Có Lọc, Tìm kiếm, Phân trang & Thuật toán CSP)
@login_required
def dashboard_view(request):
    try:
        sinh_vien = request.user.profile
    except SinhVien.DoesNotExist:
        messages.error(request, "Tài khoản chưa liên kết hồ sơ Sinh viên!")
        return render(request, 'registration/dashboard.html', {'sinh_vien': None})

    active_dot = DotDangKy.objects.filter(kich_hoat=True).first()
    
    # Lấy tham số Tìm kiếm & Lọc
    search_query = request.GET.get('search', '').strip()
    ca_filter = request.GET.get('ca_hoc', '').strip()

    lhp_qs = LopHocPhan.objects.all().select_related('mon_hoc', 'phong_hoc')

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
    if request.method == 'POST' and 'action_suggest' in request.POST:
        selected_mon_ids = request.POST.getlist('selected_mon')
        if selected_mon_ids and active_dot:
            suggested_schedules = suggest_timetable_csp(selected_mon_ids, active_dot)
            if not suggested_schedules:
                messages.warning(request, "Không tìm thấy phương án TKB hợp lệ (bị trùng lịch)!")
            else:
                messages.success(request, f"Đã tìm thấy {len(suggested_schedules)} phương án TKB tối ưu!")

    all_mon_hoc = MonHoc.objects.all()

    context = {
        'sinh_vien': sinh_vien,
        'active_dot': active_dot,
        'page_obj': page_obj,
        'registered_lhps': registered_lhps,
        'registered_ids': registered_ids,
        'all_mon_hoc': all_mon_hoc,
        'suggested_schedules': suggested_schedules,
        'search_query': search_query,
        'ca_filter': ca_filter,
    }
    return render(request, 'registration/dashboard.html', context)

# 5. View Đăng ký Môn học (Khóa dòng Row-Level Lock chống Race Condition)
@login_required
def register_course(request, ma_lhp):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = DotDangKy.objects.filter(kich_hoat=True).first()

    if not active_dot:
        messages.error(request, "Hiện không có đợt đăng ký nào mở!")
        return redirect('dashboard')

    try:
        # Sử dụng select_for_update() để khóa dòng trong PostgreSQL
        with transaction.atomic():
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
def cancel_course(request, ma_lhp):
    sinh_vien = get_object_or_404(SinhVien, user=request.user)
    active_dot = DotDangKy.objects.filter(kich_hoat=True).first()

    try:
        with transaction.atomic():
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
    active_dot = DotDangKy.objects.filter(kich_hoat=True).first()

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