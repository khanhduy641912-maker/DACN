-- =========================================================
-- ĐỀ ÁN: HỆ THỐNG QUẢN LÝ ĐĂNG KÝ MÔN HỌC
-- CƠ SỞ DỮ LIỆU: PostgreSQL
-- =========================================================

-- 1. TẠO DATABASE
CREATE DATABASE "QL_DangKyMonHoc";

BEGIN;

-- =========================================================
-- 2. TẠO CÁC BẢNG (SCHEMA DEFINITION)
-- =========================================================

-- 2.1. Bảng Môn học
CREATE TABLE registration_monhoc (
    ma_mon      VARCHAR(15) PRIMARY KEY,
    ten_mon     VARCHAR(100) NOT NULL,
    so_tin_chi  INTEGER NOT NULL CHECK (so_tin_chi > 0)
);

-- 2.2. Bảng Môn tiên quyết
CREATE TABLE registration_montienquyet (
    id                  SERIAL PRIMARY KEY,
    mon_hoc_id          VARCHAR(15) NOT NULL REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    mon_tien_quyet_id   VARCHAR(15) NOT NULL REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    CONSTRAINT unique_mon_tien_quyet UNIQUE (mon_hoc_id, mon_tien_quyet_id)
);

-- 2.3. Bảng Phòng học
CREATE TABLE registration_phonghoc (
    ma_phong VARCHAR(20) PRIMARY KEY,
    suc_chua INTEGER NOT NULL DEFAULT 40 CHECK (suc_chua > 0)
);

-- 2.4. Bảng Lớp học phần
CREATE TABLE registration_lophocphan (
    ma_lhp          VARCHAR(25) PRIMARY KEY,
    giang_vien      VARCHAR(100) NOT NULL,
    thu             INTEGER NOT NULL CHECK (thu BETWEEN 2 AND 7),
    ca_hoc          VARCHAR(10) NOT NULL CHECK (ca_hoc IN ('SANG', 'CHIEU')),
    tiet_bat_dau    INTEGER NOT NULL CHECK (tiet_bat_dau BETWEEN 1 AND 10),
    so_tiet         INTEGER NOT NULL DEFAULT 3,
    si_so_toi_da    INTEGER NOT NULL DEFAULT 50 CHECK (si_so_toi_da > 0),
    si_so_hien_tai  INTEGER NOT NULL DEFAULT 0 CHECK (si_so_hien_tai <= si_so_toi_da),
    mon_hoc_id      VARCHAR(15) NOT NULL REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    phong_hoc_id    VARCHAR(20) REFERENCES registration_phonghoc(ma_phong) ON DELETE SET NULL
);

-- 2.5. Bảng Sinh viên (Liên kết 1-1 với auth_user của Django)
CREATE TABLE registration_sinhvien (
    mssv    VARCHAR(15) PRIMARY KEY,
    ho_ten  VARCHAR(100) NOT NULL,
    lop     VARCHAR(30) NOT NULL,
    nganh   VARCHAR(100) NOT NULL,
    user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

-- 2.6. Bảng Đợt đăng ký môn học
CREATE TABLE registration_dotdangky (
    id            SERIAL PRIMARY KEY,
    ten_dot       VARCHAR(100) NOT NULL,
    ngay_bat_dau  TIMESTAMPTZ NOT NULL,
    ngay_ket_thuc TIMESTAMPTZ NOT NULL,
    kich_hoat     BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2.7. Bảng Đăng ký môn học (Giao dịch chính)
CREATE TABLE registration_dangky (
    id                SERIAL PRIMARY KEY,
    thoi_gian_dang_ky TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sinh_vien_id      VARCHAR(15) NOT NULL REFERENCES registration_sinhvien(mssv) ON DELETE CASCADE,
    lop_hoc_phan_id   VARCHAR(25) NOT NULL REFERENCES registration_lophocphan(ma_lhp) ON DELETE CASCADE,
    dot_dang_ky_id    INTEGER NOT NULL REFERENCES registration_dotdangky(id) ON DELETE CASCADE,
    CONSTRAINT unique_sinhvien_lhp_dot UNIQUE (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id)
);

-- =========================================================
-- 3. TẠO INDEX TỐI ƯU TRUY VẤN
-- =========================================================
CREATE INDEX idx_lhp_thu_ca ON registration_lophocphan (thu, ca_hoc);
CREATE INDEX idx_dangky_sinhvien ON registration_dangky (sinh_vien_id, dot_dang_ky_id);

COMMIT;


-- =========================================================
-- 4. THÊM DỮ LIỆU BAN ĐẦU (SEED DATA)
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
INSERT INTO registration_dotdangky (id, ten_dot, ngay_bat_dau, ngay_ket_thuc, kich_hoat) VALUES
    (1, 'Đợt 1 - Học kỳ 1 Năm học 2026-2027', '2026-09-01 00:00:00+07', '2026-10-30 23:59:59+07', TRUE)
ON CONFLICT (id) DO NOTHING;

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

-- 4.6. Tạo tài khoản người dùng cho Sinh viên (Bảng auth_user)
INSERT INTO auth_user (username, password, is_superuser, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES 
    ('sv01', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv01@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv02', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv02@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv03', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv03@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv04', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv04@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv05', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv05@student.edu.vn', FALSE, TRUE, NOW()),
    ('sv06', 'pbkdf2_sha256$260000$dummyhash123456$', FALSE, '', '', 'sv06@student.edu.vn', FALSE, TRUE, NOW())
ON CONFLICT (username) DO NOTHING;

-- 4.7. Danh sách Sinh viên
INSERT INTO registration_sinhvien (mssv, ho_ten, lop, nganh, user_id)
VALUES 
    ('1250080038', 'Nguyễn Khánh Duy', '08_ĐH_CNTT', 'Công nghệ thông tin', (SELECT id FROM auth_user WHERE username IN ('Admin', 'Rita') LIMIT 1)),
    ('20260001',   'Trần Thị Thu Hà',   '08_ĐH_CNTT', 'Công nghệ thông tin', (SELECT id FROM auth_user WHERE username = 'sv01')),
    ('20260002',   'Lê Hoàng Nam',      '08_ĐH_CNTT', 'Công nghệ thông tin', (SELECT id FROM auth_user WHERE username = 'sv02')),
    ('20260003',   'Phạm Quốc Bảo',     '08_ĐH_KTPM', 'Kỹ thuật phần mềm',  (SELECT id FROM auth_user WHERE username = 'sv03')),
    ('20260004',   'Vũ Minh Anh',       '08_ĐH_KTPM', 'Kỹ thuật phần mềm',  (SELECT id FROM auth_user WHERE username = 'sv04')),
    ('20260005',   'Đặng Hoàng Long',   '08_ĐH_HTTT', 'Hệ thống thông tin', (SELECT id FROM auth_user WHERE username = 'sv05')),
    ('20260006',   'Nguyễn Mai Phương', '08_ĐH_HTTT', 'Hệ thống thông tin', (SELECT id FROM auth_user WHERE username = 'sv06'))
ON CONFLICT (mssv) DO UPDATE SET
    ho_ten = EXCLUDED.ho_ten,
    lop    = EXCLUDED.lop,
    nganh  = EXCLUDED.nganh;

COMMIT;