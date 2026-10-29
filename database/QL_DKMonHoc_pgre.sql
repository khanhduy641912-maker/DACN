-- =========================================================
-- ĐỀ ÁN: HỆ THỐNG QUẢN LÝ ĐĂNG KÝ MÔN HỌC
-- CƠ SỞ DỮ LIỆU: PostgreSQL
-- Lưu ý: File này tạo bảng bằng Django migrations.
-- Nếu cần tạo hoàn toàn bằng SQL thủ công, dùng QL_DKMonHoc_manual.sql.
-- =========================================================

-- CẢNH BÁO: Script xóa hoàn toàn database QL_DangKyMonHoc và toàn bộ dữ liệu.
-- Chỉ chạy khi đã sao lưu và chắc chắn muốn tạo lại database từ đầu.
--
-- Chạy bằng psql từ thư mục gốc dự án:
--   .\venv\Scripts\Activate.ps1
--   psql -U postgres -f database/QL_DKMonHoc_pgre.sql
--
-- Script dùng lệnh riêng của psql (\connect, \!) nên không chạy trực tiếp
-- toàn bộ file trong pgAdmin Query Tool.
-- Tài khoản demo dùng mật khẩu Demo@12345; đổi trước khi triển khai thật.
\set ON_ERROR_STOP on

\connect postgres

-- Ngắt các kết nối đang mở để có thể xóa database.
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'QL_DangKyMonHoc'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS "QL_DangKyMonHoc";
CREATE DATABASE "QL_DangKyMonHoc" ENCODING 'UTF8';
\connect "QL_DangKyMonHoc"

-- Django migrations là nguồn định nghĩa schema chính thức.
-- Lệnh này tạo cả bảng Django (auth_user, django_migrations, ...) và các
-- bảng registration_* theo models.py, bao gồm khóa ngoại, kiểu ID và index.
\! python manage.py migrate --noinput


-- =========================================================
-- THÊM DỮ LIỆU BAN ĐẦU (SEED DATA)
-- =========================================================

BEGIN;

-- 4.1. Danh mục Môn học
INSERT INTO registration_monhoc (ma_mon, ten_mon, so_tin_chi) VALUES
    ('INT101', 'Lập trình Python', 3),
    ('INT102', 'Cơ sở dữ liệu', 3),
    ('INT103', 'Cấu trúc dữ liệu và Giải thuật', 3),
    ('INT104', 'Lập trình Web Django', 3),
    ('INT105', 'Mạng máy tính', 3),
    ('INT106', 'Hệ điều hành', 3),
    ('INT107', 'Kiến trúc máy tính', 2),
    ('INT108', 'Phân tích & Thiết kế hệ thống', 3),
    ('INT109', 'Trí tuệ nhân tạo', 3),
    ('INT110', 'Học máy & Khai phá dữ liệu', 3),
    ('INT111', 'Bảo mật thông tin', 3),
    ('INT112', 'Lập trình Java Nâng cao', 3),
    ('INT113', 'Phát triển ứng dụng Di động', 3),
    ('MTH101', 'Toán rời rạc', 3),
    ('MTH102', 'Đại số tuyến tính', 3),
    ('MTH103', 'Xác suất thống kê', 3),
    ('ENG101', 'Tiếng Anh chuyên ngành CNTT 1', 2),
    ('ENG102', 'Tiếng Anh chuyên ngành CNTT 2', 2),
    ('POL101', 'Triết học Mác - Lênin', 3),
    ('POL102', 'Tư tưởng Hồ Chí Minh', 2)
ON CONFLICT (ma_mon) DO UPDATE SET 
    ten_mon = EXCLUDED.ten_mon,
    so_tin_chi = EXCLUDED.so_tin_chi;

INSERT INTO registration_hocky
    (ma_hoc_ky, ten_hoc_ky, ngay_bat_dau, ngay_ket_thuc)
VALUES
    ('2026-1', 'Học kỳ 1 năm học 2026-2027', '2026-08-24', '2026-12-04')
ON CONFLICT (ma_hoc_ky) DO NOTHING;

INSERT INTO registration_chuongtrinhdaotao
    (ma_chuong_trinh, ten_chuong_trinh, nganh, khoa_ap_dung)
VALUES
    ('CNPM-2023', 'Công nghệ phần mềm khóa 2023', 'Công nghệ phần mềm', '2023')
ON CONFLICT (ma_chuong_trinh) DO NOTHING;

INSERT INTO registration_chuongtrinhmonhoc
    (chuong_trinh_id, mon_hoc_id, bat_buoc)
SELECT 'CNPM-2023', ma_mon, TRUE
FROM registration_monhoc
ON CONFLICT (chuong_trinh_id, mon_hoc_id) DO NOTHING;

-- 4.2. Danh mục Phòng học
INSERT INTO registration_phonghoc (ma_phong, suc_chua) VALUES
    ('A101', 50), ('A102', 40), ('A201', 60),
    ('B101', 45), ('B202', 40), ('B301', 50),
    ('C201', 50), ('C303', 60), ('C401', 45),
    ('E101', 80), ('E201', 75), ('LAB01', 35)
ON CONFLICT (ma_phong) DO NOTHING;

-- 4.3. Ràng buộc Môn tiên quyết
INSERT INTO registration_montienquyet (mon_hoc_id, mon_tien_quyet_id) VALUES
    ('INT103', 'INT101'), -- CTDL&GT -> Python
    ('INT104', 'INT102'), -- Web Django -> CSDL
    ('INT109', 'MTH101'), -- AI -> Toán rời rạc
    ('INT110', 'INT109'), -- Học máy -> AI
    ('INT112', 'INT101'), -- Java nâng cao -> Python
    ('ENG102', 'ENG101')  -- Tiếng Anh 2 -> Tiếng Anh 1
ON CONFLICT DO NOTHING;

-- 4.4. Đợt đăng ký môn học
INSERT INTO registration_dotdangky
    (ten_dot, hoc_ky_id, ngay_bat_dau, ngay_ket_thuc, kich_hoat)
VALUES
    ('Đợt 1 - Học kỳ 1 Năm học 2026-2027', '2026-1',
     '2026-09-01 00:00:00+07', '2026-10-30 23:59:59+07', TRUE);

-- 4.5. Danh sách Lớp học phần
INSERT INTO registration_lophocphan 
    (ma_lhp, giang_vien, thu, ca_hoc, tiet_bat_dau, so_tiet, si_so_toi_da, si_so_hien_tai, mon_hoc_id, phong_hoc_id) 
VALUES
    -- Python (INT101)
    ('INT101_01', 'TS. Nguyễn Văn A',         2, 'SANG',  1, 3, 50, 15, 'INT101', 'A101'),
    ('INT101_02', 'ThS. Lê Thị B',            3, 'CHIEU', 6, 3, 50, 42, 'INT101', 'B202'),
    ('INT101_03', 'TS. Phạm Văn C',           5, 'SANG',  1, 3, 40, 40, 'INT101', 'LAB01'),

    -- Cơ sở dữ liệu (INT102)
    ('INT102_01', 'TS. Dương Thị Thúy Nga',   2, 'SANG',  1, 3, 40, 20, 'INT102', 'B202'),
    ('INT102_02', 'TS. Dương Thị Thúy Nga',   4, 'CHIEU', 6, 3, 40, 10, 'INT102', 'A101'),
    ('INT102_03', 'ThS. Hoàng Văn D',         6, 'SANG',  1, 3, 50,  5, 'INT102', 'C201'),

    -- CTDL & Giải thuật (INT103)
    ('INT103_01', 'ThS. Trần Văn E',          5, 'SANG',  1, 3, 50, 12, 'INT103', 'C303'),
    ('INT103_02', 'TS. Nguyễn Văn A',         3, 'SANG',  1, 3, 45,  8, 'INT103', 'A102'),

    -- Toán rời rạc (MTH101)
    ('MTH101_01', 'PGS.TS. Vũ Văn F',         2, 'CHIEU', 6, 3, 60, 30, 'MTH101', 'E101'),
    ('MTH101_02', 'ThS. Đỗ Thị G',            4, 'SANG',  1, 3, 60, 25, 'MTH101', 'E201'),

    -- Web Django (INT104)
    ('INT104_01', 'TS. Dương Thị Thúy Nga',   3, 'CHIEU', 6, 3, 40, 18, 'INT104', 'LAB01'),
    ('INT104_02', 'ThS. Lê Thị B',            6, 'CHIEU', 6, 3, 40, 22, 'INT104', 'B101'),

    -- Mạng máy tính (INT105)
    ('INT105_01', 'TS. Ngô Văn H',            2, 'SANG',  4, 3, 50, 11, 'INT105', 'A201'),
    ('INT105_02', 'ThS. Bùi Văn I',           5, 'CHIEU', 6, 3, 50, 19, 'INT105', 'B301'),

    -- Hệ điều hành (INT106)
    ('INT106_01', 'TS. Ngô Văn H',            3, 'SANG',  1, 3, 45, 14, 'INT106', 'A101'),
    ('INT106_02', 'ThS. Bùi Văn I',           7, 'SANG',  1, 3, 45,  9, 'INT106', 'C401'),

    -- Kiến trúc máy tính (INT107)
    ('INT107_01', 'ThS. Hoàng Văn D',         4, 'SANG',  4, 2, 50, 28, 'INT107', 'A102'),
    ('INT107_02', 'ThS. Bùi Văn I',           6, 'SANG',  4, 2, 50, 16, 'INT107', 'B202'),

    -- Trí tuệ nhân tạo (INT109)
    ('INT109_01', 'PGS.TS. Nguyễn Văn K',     2, 'CHIEU', 6, 3, 40, 35, 'INT109', 'C303'),
    ('INT109_02', 'PGS.TS. Nguyễn Văn K',     4, 'CHIEU', 6, 3, 40, 20, 'INT109', 'LAB01'),

    -- Học máy & Khai phá dữ liệu (INT110)
    ('INT110_01', 'TS. Trần Thị L',           3, 'CHIEU', 6, 3, 35, 12, 'INT110', 'LAB01'),
    ('INT110_02', 'TS. Trần Thị L',           5, 'CHIEU', 6, 3, 35, 15, 'INT110', 'A201'),

    -- Bảo mật thông tin (INT111)
    ('INT111_01', 'ThS. Trịnh Văn M',         4, 'SANG',  1, 3, 45, 20, 'INT111', 'B301'),
    ('INT111_02', 'ThS. Trịnh Văn M',         7, 'SANG',  1, 3, 45,  5, 'INT111', 'E101'),

    -- Các môn khác
    ('MTH102_01', 'TS. Phan Văn N',           2, 'SANG',  1, 3, 75, 45, 'MTH102', 'E201'),
    ('MTH103_01', 'TS. Phan Văn N',           3, 'SANG',  4, 3, 75, 50, 'MTH103', 'E101'),
    ('ENG101_01', 'ThS. Smith J.',            2, 'CHIEU', 6, 2, 40, 30, 'ENG101', 'A101'),
    ('ENG102_01', 'ThS. Smith J.',            4, 'CHIEU', 8, 2, 40, 15, 'ENG102', 'A102'),
    ('POL101_01', 'TS. Đặng Văn P',           6, 'SANG',  1, 3, 80, 60, 'POL101', 'E101'),
    ('POL102_01', 'TS. Đặng Văn P',           7, 'CHIEU', 6, 2, 80, 40, 'POL102', 'E201')
ON CONFLICT (ma_lhp) DO NOTHING;

UPDATE registration_lophocphan
SET hoc_ky_id = '2026-1',
    si_so_hien_tai = 0;

-- 4.6. Tạo tài khoản người dùng cho Sinh viên (Bảng auth_user)
INSERT INTO auth_user (username, password, is_superuser, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES 
    ('admin_demo', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', TRUE, 'Quản trị', 'Viên', 'admin@example.local', TRUE, TRUE, NOW()),
    ('sv_duy', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Khánh Duy', 'Nguyễn', '1250080038@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv01', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Thu Hà', 'Trần', 'sv01@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv02', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Hoàng Nam', 'Lê', 'sv02@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv03', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Quốc Bảo', 'Phạm', 'sv03@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv04', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Minh Anh', 'Vũ', 'sv04@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv05', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Hoàng Long', 'Đặng', 'sv05@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv06', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Mai Phương', 'Nguyễn', 'sv06@student.edu.vn', FALSE, TRUE, NOW())
ON CONFLICT (username) DO NOTHING;

-- 4.7. Danh sách Sinh viên
INSERT INTO registration_sinhvien
    (mssv, ho_ten, lop, nganh, user_id, chuong_trinh_id)
VALUES 
    ('1250080038', 'Nguyễn Khánh Duy', '12_ĐH_CNPM1', 'Công nghệ phần mềm', (SELECT id FROM auth_user WHERE username = 'sv_duy'), 'CNPM-2023'),
    ('20260001',   'Trần Thị Thu Hà',   '08_ĐH_CNTT', 'Công nghệ thông tin', (SELECT id FROM auth_user WHERE username = 'sv01'), NULL),
    ('20260002',   'Lê Hoàng Nam',      '08_ĐH_CNTT', 'Công nghệ thông tin', (SELECT id FROM auth_user WHERE username = 'sv02'), NULL),
    ('20260003',   'Phạm Quốc Bảo',     '08_ĐH_KTPM', 'Kỹ thuật phần mềm',  (SELECT id FROM auth_user WHERE username = 'sv03'), NULL),
    ('20260004',   'Vũ Minh Anh',        '08_ĐH_KTPM', 'Kỹ thuật phần mềm',  (SELECT id FROM auth_user WHERE username = 'sv04'), NULL),
    ('20260005',   'Đặng Hoàng Long',   '08_ĐH_HTTT', 'Hệ thống thông tin', (SELECT id FROM auth_user WHERE username = 'sv05'), NULL),
    ('20260006',   'Nguyễn Mai Phương', '08_ĐH_HTTT', 'Hệ thống thông tin', (SELECT id FROM auth_user WHERE username = 'sv06'), NULL)
ON CONFLICT (mssv) DO UPDATE SET
    ho_ten = EXCLUDED.ho_ten,
    lop    = EXCLUDED.lop,
    nganh  = EXCLUDED.nganh,
    chuong_trinh_id = EXCLUDED.chuong_trinh_id;

INSERT INTO registration_monhocdahoanthanh
    (sinh_vien_id, mon_hoc_id, diem, ngay_hoan_thanh)
VALUES
    ('1250080038', 'INT101', 8.50, '2025-12-20'),
    ('1250080038', 'INT102', 8.00, '2026-05-25'),
    ('1250080038', 'MTH101', 7.50, '2025-12-20')
ON CONFLICT (sinh_vien_id, mon_hoc_id) DO NOTHING;

INSERT INTO registration_tieuchiuutien
    (sinh_vien_id, ca_uu_tien, so_ngay_hoc_toi_da, han_che_tiet_trong)
SELECT mssv, 'BAT_KY', 4, TRUE
FROM registration_sinhvien
ON CONFLICT (sinh_vien_id) DO NOTHING;

INSERT INTO registration_dangky
    (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id)
SELECT '20260001', 'INT101_01', id
FROM registration_dotdangky
WHERE ten_dot = 'Đợt 1 - Học kỳ 1 Năm học 2026-2027'
ON CONFLICT (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id) DO NOTHING;

INSERT INTO registration_dangky
    (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id)
SELECT '20260002', 'INT102_02', id
FROM registration_dotdangky
WHERE ten_dot = 'Đợt 1 - Học kỳ 1 Năm học 2026-2027'
ON CONFLICT (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id) DO NOTHING;

UPDATE registration_lophocphan AS section
SET si_so_hien_tai = (
    SELECT COUNT(*)
    FROM registration_dangky AS enrollment
    WHERE enrollment.lop_hoc_phan_id = section.ma_lhp
);

COMMIT;