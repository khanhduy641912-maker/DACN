-- =========================================================
-- HỆ THỐNG ĐĂNG KÝ MÔN HỌC - POSTGRESQL
-- Tạo thủ công bảng, ràng buộc, index và dữ liệu mẫu bằng pgAdmin.
--
-- BƯỚC 1: Tạo database "QL_DangKyMonHoc" bằng script
--         QL_DKMonHoc_pgadmin_database.sql, hoặc tạo trong pgAdmin.
-- BƯỚC 2: Trong pgAdmin, mở Query Tool kết nối đúng database
--         "QL_DangKyMonHoc", sau đó chạy toàn bộ file này.
--
-- CẢNH BÁO: Script xóa các bảng nghiệp vụ/Django hiện có trong database
-- đích rồi tạo lại schema và dữ liệu mẫu. Sao lưu trước khi chạy.
--
-- File này không gọi psql, manage.py, ORM hay Django migrations.
-- Bao gồm học kỳ/chương trình đào tạo, môn đã hoàn thành và tiêu chí ưu tiên.
-- Tài khoản mẫu: admin_demo, sv_duy, sv01, sv02, sv03, sv04, sv05, sv06
-- Mật khẩu chung cho tài khoản mẫu: Demo@12345
-- Đổi mật khẩu mẫu trước khi đưa hệ thống lên môi trường thật.
-- =========================================================

BEGIN;

-- Database vừa được tạo lại nên các bảng không tồn tại. Giữ lệnh DROP
-- tường minh để thể hiện thứ tự xóa phụ thuộc và thuận tiện tái sử dụng
-- phần schema khi cần chạy riêng bên trong một database khác.
DROP TABLE IF EXISTS
    registration_dangky,
    registration_lophocphan,
    registration_sinhvien,
    registration_tieuchiuutien,
    registration_monhocdahoanthanh,
    registration_chuongtrinhmonhoc,
    registration_montienquyet,
    registration_chuongtrinhdaotao,
    registration_monhoc,
    registration_hocky,
    registration_phonghoc,
    registration_dotdangky,
    django_admin_log,
    django_migrations,
    auth_user_user_permissions,
    auth_user_groups,
    auth_group_permissions,
    auth_permission,
    auth_group,
    django_session,
    django_content_type
CASCADE;

-- =========================================================
-- 1. CÁC BẢNG DỊCH VỤ DỰNG SẴN CỦA DJANGO
-- Cần thiết cho đăng nhập, phân quyền, session và trang quản trị.
-- =========================================================

CREATE TABLE django_content_type (
    id          SERIAL PRIMARY KEY,
    app_label   VARCHAR(100) NOT NULL,
    model       VARCHAR(100) NOT NULL,
    CONSTRAINT django_content_type_app_model_uniq UNIQUE (app_label, model)
);

CREATE TABLE auth_group (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_permission (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    content_type_id INTEGER NOT NULL
        REFERENCES django_content_type(id) ON DELETE CASCADE,
    codename        VARCHAR(100) NOT NULL,
    CONSTRAINT auth_permission_content_type_codename_uniq
        UNIQUE (content_type_id, codename)
);

CREATE INDEX auth_permission_content_type_id_idx
    ON auth_permission (content_type_id);

CREATE TABLE auth_group_permissions (
    id            BIGSERIAL PRIMARY KEY,
    group_id      INTEGER NOT NULL
        REFERENCES auth_group(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL
        REFERENCES auth_permission(id) ON DELETE CASCADE,
    CONSTRAINT auth_group_permissions_group_permission_uniq
        UNIQUE (group_id, permission_id)
);

CREATE INDEX auth_group_permissions_group_id_idx
    ON auth_group_permissions (group_id);
CREATE INDEX auth_group_permissions_permission_id_idx
    ON auth_group_permissions (permission_id);

CREATE TABLE auth_user (
    id           SERIAL PRIMARY KEY,
    password     VARCHAR(128) NOT NULL,
    last_login   TIMESTAMPTZ,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username     VARCHAR(150) NOT NULL UNIQUE,
    first_name   VARCHAR(150) NOT NULL DEFAULT '',
    last_name    VARCHAR(150) NOT NULL DEFAULT '',
    email        VARCHAR(254) NOT NULL DEFAULT '',
    is_staff     BOOLEAN NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth_user_groups (
    id       BIGSERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
    CONSTRAINT auth_user_groups_user_group_uniq UNIQUE (user_id, group_id)
);

CREATE INDEX auth_user_groups_user_id_idx
    ON auth_user_groups (user_id);
CREATE INDEX auth_user_groups_group_id_idx
    ON auth_user_groups (group_id);

CREATE TABLE auth_user_user_permissions (
    id            BIGSERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL
        REFERENCES auth_permission(id) ON DELETE CASCADE,
    CONSTRAINT auth_user_user_permissions_user_permission_uniq
        UNIQUE (user_id, permission_id)
);

CREATE INDEX auth_user_user_permissions_user_id_idx
    ON auth_user_user_permissions (user_id);
CREATE INDEX auth_user_user_permissions_permission_id_idx
    ON auth_user_user_permissions (permission_id);

CREATE TABLE django_session (
    session_key  VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date  TIMESTAMPTZ NOT NULL
);

CREATE INDEX django_session_expire_date_idx
    ON django_session (expire_date);

CREATE TABLE django_admin_log (
    id             SERIAL PRIMARY KEY,
    action_time    TIMESTAMPTZ NOT NULL,
    object_id      TEXT,
    object_repr    VARCHAR(200) NOT NULL,
    action_flag    SMALLINT NOT NULL
        CHECK (action_flag BETWEEN 1 AND 3),
    change_message TEXT NOT NULL,
    content_type_id INTEGER
        REFERENCES django_content_type(id) ON DELETE SET NULL,
    user_id        INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
);

CREATE INDEX django_admin_log_content_type_id_idx
    ON django_admin_log (content_type_id);
CREATE INDEX django_admin_log_user_id_idx
    ON django_admin_log (user_id);

-- =========================================================
-- 2. CÁC BẢNG NGHIỆP VỤ ĐĂNG KÝ MÔN HỌC
-- =========================================================

CREATE TABLE registration_monhoc (
    ma_mon      VARCHAR(15) PRIMARY KEY,
    ten_mon     VARCHAR(100) NOT NULL,
    so_tin_chi  INTEGER NOT NULL CHECK (so_tin_chi > 0)
);

CREATE TABLE registration_hocky (
    ma_hoc_ky      VARCHAR(20) PRIMARY KEY,
    ten_hoc_ky     VARCHAR(100) NOT NULL,
    ngay_bat_dau   DATE NOT NULL,
    ngay_ket_thuc  DATE NOT NULL,
    CONSTRAINT registration_hocky_thoi_gian_hop_le
        CHECK (ngay_ket_thuc >= ngay_bat_dau)
);

CREATE TABLE registration_chuongtrinhdaotao (
    ma_chuong_trinh VARCHAR(20) PRIMARY KEY,
    ten_chuong_trinh VARCHAR(150) NOT NULL,
    nganh            VARCHAR(100) NOT NULL,
    khoa_ap_dung     VARCHAR(20) NOT NULL
);

CREATE TABLE registration_chuongtrinhmonhoc (
    id               BIGSERIAL PRIMARY KEY,
    chuong_trinh_id  VARCHAR(20) NOT NULL
        REFERENCES registration_chuongtrinhdaotao(ma_chuong_trinh) ON DELETE CASCADE,
    mon_hoc_id       VARCHAR(15) NOT NULL
        REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    bat_buoc         BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT registration_chuongtrinhmonhoc_pair_uniq
        UNIQUE (chuong_trinh_id, mon_hoc_id)
);

CREATE INDEX registration_chuongtrinhmonhoc_program_idx
    ON registration_chuongtrinhmonhoc (chuong_trinh_id);
CREATE INDEX registration_chuongtrinhmonhoc_course_idx
    ON registration_chuongtrinhmonhoc (mon_hoc_id);

CREATE TABLE registration_montienquyet (
    id                  BIGSERIAL PRIMARY KEY,
    mon_hoc_id          VARCHAR(15) NOT NULL
        REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    mon_tien_quyet_id   VARCHAR(15) NOT NULL
        REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    loai_dieu_kien      VARCHAR(12) NOT NULL DEFAULT 'TIEN_QUYET'
        CHECK (loai_dieu_kien IN ('TIEN_QUYET', 'SONG_HANH')),
    CONSTRAINT registration_montienquyet_pair_uniq
        UNIQUE (mon_hoc_id, mon_tien_quyet_id),
    CONSTRAINT registration_montienquyet_not_self
        CHECK (mon_hoc_id <> mon_tien_quyet_id)
);

CREATE INDEX registration_montienquyet_mon_hoc_id_idx
    ON registration_montienquyet (mon_hoc_id);
CREATE INDEX registration_montienquyet_tien_quyet_id_idx
    ON registration_montienquyet (mon_tien_quyet_id);

CREATE TABLE registration_phonghoc (
    ma_phong VARCHAR(20) PRIMARY KEY,
    suc_chua INTEGER NOT NULL DEFAULT 40 CHECK (suc_chua > 0)
);

CREATE TABLE registration_lophocphan (
    ma_lhp          VARCHAR(25) PRIMARY KEY,
    mon_hoc_id      VARCHAR(15) NOT NULL
        REFERENCES registration_monhoc(ma_mon) ON DELETE CASCADE,
    hoc_ky_id       VARCHAR(20)
        REFERENCES registration_hocky(ma_hoc_ky) ON DELETE RESTRICT,
    giang_vien      VARCHAR(100) NOT NULL,
    phong_hoc_id    VARCHAR(20)
        REFERENCES registration_phonghoc(ma_phong) ON DELETE SET NULL,
    thu             INTEGER NOT NULL CHECK (thu BETWEEN 2 AND 7),
    ca_hoc          VARCHAR(10) NOT NULL CHECK (ca_hoc IN ('SANG', 'CHIEU')),
    tiet_bat_dau    INTEGER NOT NULL CHECK (tiet_bat_dau BETWEEN 1 AND 10),
    so_tiet         INTEGER NOT NULL DEFAULT 3 CHECK (so_tiet > 0),
    si_so_toi_da    INTEGER NOT NULL DEFAULT 50 CHECK (si_so_toi_da > 0),
    si_so_hien_tai  INTEGER NOT NULL DEFAULT 0
        CHECK (si_so_hien_tai >= 0 AND si_so_hien_tai <= si_so_toi_da),
    CONSTRAINT registration_lophocphan_tiet_trong_ngay
        CHECK (tiet_bat_dau + so_tiet - 1 <= 10)
);

CREATE INDEX registration_lophocphan_mon_hoc_id_idx
    ON registration_lophocphan (mon_hoc_id);
CREATE INDEX registration_lophocphan_phong_hoc_id_idx
    ON registration_lophocphan (phong_hoc_id);
CREATE INDEX registration_lophocphan_hoc_ky_id_idx
    ON registration_lophocphan (hoc_ky_id);
CREATE INDEX registration_lophocphan_thu_ca_idx
    ON registration_lophocphan (thu, ca_hoc);

CREATE TABLE registration_sinhvien (
    mssv    VARCHAR(15) PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE
        REFERENCES auth_user(id) ON DELETE CASCADE,
    ho_ten  VARCHAR(100) NOT NULL,
    lop     VARCHAR(30) NOT NULL,
    nganh   VARCHAR(100) NOT NULL,
    chuong_trinh_id VARCHAR(20)
        REFERENCES registration_chuongtrinhdaotao(ma_chuong_trinh) ON DELETE SET NULL
);

CREATE INDEX registration_sinhvien_chuong_trinh_id_idx
    ON registration_sinhvien (chuong_trinh_id);

CREATE TABLE registration_dotdangky (
    id              BIGSERIAL PRIMARY KEY,
    ten_dot         VARCHAR(100) NOT NULL,
    hoc_ky_id       VARCHAR(20)
        REFERENCES registration_hocky(ma_hoc_ky) ON DELETE RESTRICT,
    ngay_bat_dau    TIMESTAMPTZ NOT NULL,
    ngay_ket_thuc   TIMESTAMPTZ NOT NULL,
    kich_hoat       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT registration_dotdangky_thoi_gian_hop_le
        CHECK (ngay_ket_thuc > ngay_bat_dau)
);

CREATE INDEX registration_dotdangky_hoc_ky_id_idx
    ON registration_dotdangky (hoc_ky_id);

CREATE TABLE registration_dangky (
    id                  BIGSERIAL PRIMARY KEY,
    sinh_vien_id        VARCHAR(15) NOT NULL
        REFERENCES registration_sinhvien(mssv) ON DELETE CASCADE,
    lop_hoc_phan_id     VARCHAR(25) NOT NULL
        REFERENCES registration_lophocphan(ma_lhp) ON DELETE CASCADE,
    dot_dang_ky_id      BIGINT NOT NULL
        REFERENCES registration_dotdangky(id) ON DELETE CASCADE,
    thoi_gian_dang_ky   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT registration_dangky_sv_lhp_dot_uniq
        UNIQUE (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id)
);

CREATE INDEX registration_dangky_sinh_vien_dot_idx
    ON registration_dangky (sinh_vien_id, dot_dang_ky_id);
CREATE INDEX registration_dangky_lop_hoc_phan_id_idx
    ON registration_dangky (lop_hoc_phan_id);
CREATE INDEX registration_dangky_dot_dang_ky_id_idx
    ON registration_dangky (dot_dang_ky_id);

CREATE TABLE registration_monhocdahoanthanh (
    id                BIGSERIAL PRIMARY KEY,
    sinh_vien_id      VARCHAR(15) NOT NULL
        REFERENCES registration_sinhvien(mssv) ON DELETE CASCADE,
    mon_hoc_id        VARCHAR(15) NOT NULL
        REFERENCES registration_monhoc(ma_mon) ON DELETE RESTRICT,
    hoc_ky_id         VARCHAR(20)
        REFERENCES registration_hocky(ma_hoc_ky) ON DELETE SET NULL,
    diem              NUMERIC(4, 2),
    ngay_hoan_thanh   DATE,
    CONSTRAINT registration_monhocdahoanthanh_student_course_uniq
        UNIQUE (sinh_vien_id, mon_hoc_id),
    CONSTRAINT registration_monhocdahoanthanh_grade_range
        CHECK (diem IS NULL OR (diem >= 0 AND diem <= 10))
);

CREATE INDEX registration_monhocdahoanthanh_sinh_vien_id_idx
    ON registration_monhocdahoanthanh (sinh_vien_id);
CREATE INDEX registration_monhocdahoanthanh_mon_hoc_id_idx
    ON registration_monhocdahoanthanh (mon_hoc_id);
CREATE INDEX registration_monhocdahoanthanh_hoc_ky_id_idx
    ON registration_monhocdahoanthanh (hoc_ky_id);

CREATE TABLE registration_tieuchiuutien (
    id                    BIGSERIAL PRIMARY KEY,
    sinh_vien_id          VARCHAR(15) NOT NULL UNIQUE
        REFERENCES registration_sinhvien(mssv) ON DELETE CASCADE,
    ca_uu_tien            VARCHAR(10) NOT NULL DEFAULT 'BAT_KY'
        CHECK (ca_uu_tien IN ('BAT_KY', 'SANG', 'CHIEU')),
    so_ngay_hoc_toi_da    SMALLINT NOT NULL DEFAULT 6
        CHECK (so_ngay_hoc_toi_da BETWEEN 1 AND 6),
    han_che_tiet_trong    BOOLEAN NOT NULL DEFAULT TRUE
);

-- =========================================================
-- 3. DỮ LIỆU MẪU CHO DJANGO AUTH VÀ QUYỀN TRUY CẬP
-- =========================================================

INSERT INTO django_content_type (app_label, model) VALUES
    ('admin', 'logentry'),
    ('auth', 'group'),
    ('auth', 'permission'),
    ('auth', 'user'),
    ('registration', 'dangky'),
    ('registration', 'chuongtrinhdaotao'),
    ('registration', 'chuongtrinhmonhoc'),
    ('registration', 'dotdangky'),
    ('registration', 'hocky'),
    ('registration', 'lophocphan'),
    ('registration', 'monhoc'),
    ('registration', 'monhocdahoanthanh'),
    ('registration', 'montienquyet'),
    ('registration', 'phonghoc'),
    ('registration', 'sinhvien'),
    ('registration', 'tieuchiuutien');

INSERT INTO auth_permission (name, content_type_id, codename)
SELECT 'Can ' || permission_action.action_name || ' ' || ct.model,
       ct.id,
       permission_action.action_name || '_' || ct.model
FROM django_content_type AS ct
CROSS JOIN (
    VALUES ('add'), ('change'), ('delete'), ('view')
) AS permission_action(action_name);

-- Mật khẩu mẫu được mã hóa theo PBKDF2 của Django, không lưu mật khẩu rõ.
INSERT INTO auth_user
    (username, password, is_superuser, first_name, last_name, email,
     is_staff, is_active, date_joined)
VALUES
    ('admin_demo', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', TRUE, 'Quản trị', 'Viên', 'admin@example.local', TRUE, TRUE, CURRENT_TIMESTAMP),
    ('sv_duy', 'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Khánh Duy', 'Nguyễn', '1250080038@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv01',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Thu Hà', 'Trần', 'sv01@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv02',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Hoàng Nam', 'Lê', 'sv02@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv03',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Quốc Bảo', 'Phạm', 'sv03@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv04',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Minh Anh', 'Vũ', 'sv04@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv05',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Hoàng Long', 'Đặng', 'sv05@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP),
    ('sv06',   'pbkdf2_sha256$1500000$4FHrAqqnJk1F9vA9RFIAnz$lgkNIfDf+ezN9A+46Vb5amsLlasi2tyWJ4hfp3+p1Ig=', FALSE, 'Mai Phương', 'Nguyễn', 'sv06@student.edu.vn', FALSE, TRUE, CURRENT_TIMESTAMP);

-- =========================================================
-- 4. DỮ LIỆU NGHIỆP VỤ MẪU
-- =========================================================

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
    ('POL102', 'Tư tưởng Hồ Chí Minh', 2);

INSERT INTO registration_hocky
    (ma_hoc_ky, ten_hoc_ky, ngay_bat_dau, ngay_ket_thuc)
VALUES
    ('2026-1', 'Học kỳ 1 năm học 2026-2027', '2026-08-24', '2026-12-04');

INSERT INTO registration_chuongtrinhdaotao
    (ma_chuong_trinh, ten_chuong_trinh, nganh, khoa_ap_dung)
VALUES
    ('CNPM-2023', 'Công nghệ phần mềm khóa 2023', 'Công nghệ phần mềm', '2023');

INSERT INTO registration_chuongtrinhmonhoc
    (chuong_trinh_id, mon_hoc_id, bat_buoc)
SELECT 'CNPM-2023', mon_hoc.ma_mon, TRUE
FROM registration_monhoc AS mon_hoc;

INSERT INTO registration_phonghoc (ma_phong, suc_chua) VALUES
    ('A101', 50), ('A102', 40), ('A201', 60),
    ('B101', 45), ('B202', 40), ('B301', 50),
    ('C201', 50), ('C303', 60), ('C401', 45),
    ('E101', 80), ('E201', 75), ('LAB01', 35);

INSERT INTO registration_montienquyet (mon_hoc_id, mon_tien_quyet_id) VALUES
    ('INT103', 'INT101'),
    ('INT104', 'INT102'),
    ('INT109', 'MTH101'),
    ('INT110', 'INT109'),
    ('INT112', 'INT101'),
    ('ENG102', 'ENG101');

INSERT INTO registration_dotdangky
    (ten_dot, hoc_ky_id, ngay_bat_dau, ngay_ket_thuc, kich_hoat)
VALUES
    ('Đợt 1 - Học kỳ 1 Năm học 2026-2027',
     '2026-1',
     '2026-08-24 00:00:00+07',
     '2026-12-04 23:59:59+07',
     TRUE);

INSERT INTO registration_lophocphan
    (ma_lhp, giang_vien, thu, ca_hoc, tiet_bat_dau, so_tiet,
     si_so_toi_da, si_so_hien_tai, mon_hoc_id, phong_hoc_id)
VALUES
    ('INT101_01', 'TS. Nguyễn Văn A',       2, 'SANG',  1, 3, 50, 1, 'INT101', 'A101'),
    ('INT101_02', 'ThS. Lê Thị B',          3, 'CHIEU', 6, 3, 50, 0, 'INT101', 'B202'),
    ('INT101_03', 'TS. Phạm Văn C',         5, 'SANG',  1, 3, 40, 0, 'INT101', 'LAB01'),
    ('INT102_01', 'TS. Dương Thị Thúy Nga', 2, 'SANG',  1, 3, 40, 0, 'INT102', 'B202'),
    ('INT102_02', 'TS. Dương Thị Thúy Nga', 4, 'CHIEU', 6, 3, 40, 1, 'INT102', 'A101'),
    ('INT102_03', 'ThS. Hoàng Văn D',       6, 'SANG',  1, 3, 50, 0, 'INT102', 'C201'),
    ('INT103_01', 'ThS. Trần Văn E',        5, 'SANG',  1, 3, 50, 0, 'INT103', 'C303'),
    ('INT103_02', 'TS. Nguyễn Văn A',       3, 'SANG',  1, 3, 45, 0, 'INT103', 'A102'),
    ('MTH101_01', 'PGS.TS. Vũ Văn F',       2, 'CHIEU', 6, 3, 60, 0, 'MTH101', 'E101'),
    ('MTH101_02', 'ThS. Đỗ Thị G',          4, 'SANG',  1, 3, 60, 0, 'MTH101', 'E201'),
    ('INT104_01', 'TS. Dương Thị Thúy Nga', 3, 'CHIEU', 6, 3, 40, 0, 'INT104', 'LAB01'),
    ('INT104_02', 'ThS. Lê Thị B',          6, 'CHIEU', 6, 3, 40, 0, 'INT104', 'B101'),
    ('INT105_01', 'TS. Ngô Văn H',          2, 'SANG',  4, 3, 50, 0, 'INT105', 'A201'),
    ('INT105_02', 'ThS. Bùi Văn I',         5, 'CHIEU', 6, 3, 50, 0, 'INT105', 'B301'),
    ('INT106_01', 'TS. Ngô Văn H',          3, 'SANG',  1, 3, 45, 0, 'INT106', 'A101'),
    ('INT106_02', 'ThS. Bùi Văn I',         7, 'SANG',  1, 3, 45, 0, 'INT106', 'C401'),
    ('INT107_01', 'ThS. Hoàng Văn D',       4, 'SANG',  4, 2, 50, 0, 'INT107', 'A102'),
    ('INT107_02', 'ThS. Bùi Văn I',         6, 'SANG',  4, 2, 50, 0, 'INT107', 'B202'),
    ('INT109_01', 'PGS.TS. Nguyễn Văn K',   2, 'CHIEU', 6, 3, 40, 0, 'INT109', 'C303'),
    ('INT109_02', 'PGS.TS. Nguyễn Văn K',   4, 'CHIEU', 6, 3, 40, 0, 'INT109', 'LAB01'),
    ('INT110_01', 'TS. Trần Thị L',         3, 'CHIEU', 6, 3, 35, 0, 'INT110', 'LAB01'),
    ('INT110_02', 'TS. Trần Thị L',         5, 'CHIEU', 6, 3, 35, 0, 'INT110', 'A201'),
    ('INT111_01', 'ThS. Trịnh Văn M',       4, 'SANG',  1, 3, 45, 0, 'INT111', 'B301'),
    ('INT111_02', 'ThS. Trịnh Văn M',       7, 'SANG',  1, 3, 45, 0, 'INT111', 'E101'),
    ('MTH102_01', 'TS. Phan Văn N',         2, 'SANG',  1, 3, 75, 0, 'MTH102', 'E201'),
    ('MTH103_01', 'TS. Phan Văn N',         3, 'SANG',  4, 3, 75, 0, 'MTH103', 'E101'),
    ('ENG101_01', 'ThS. Smith J.',          2, 'CHIEU', 6, 2, 40, 0, 'ENG101', 'A101'),
    ('ENG102_01', 'ThS. Smith J.',          4, 'CHIEU', 8, 2, 40, 0, 'ENG102', 'A102'),
    ('POL101_01', 'TS. Đặng Văn P',         6, 'SANG',  1, 3, 80, 0, 'POL101', 'E101'),
    ('POL102_01', 'TS. Đặng Văn P',         7, 'CHIEU', 6, 2, 80, 0, 'POL102', 'E201');

UPDATE registration_lophocphan
SET hoc_ky_id = '2026-1';

INSERT INTO registration_sinhvien
    (mssv, user_id, ho_ten, lop, nganh, chuong_trinh_id)
SELECT student.mssv,
       auth_user.id,
       student.ho_ten,
       student.lop,
       student.nganh,
       CASE WHEN student.mssv = '1250080038' THEN 'CNPM-2023' ELSE NULL END
FROM (VALUES
    ('1250080038', 'sv_duy', 'Nguyễn Khánh Duy', '12_ĐH_CNPM1', 'Công nghệ phần mềm'),
    ('20260001', 'sv01', 'Trần Thị Thu Hà', '08_ĐH_CNTT', 'Công nghệ thông tin'),
    ('20260002', 'sv02', 'Lê Hoàng Nam', '08_ĐH_CNTT', 'Công nghệ thông tin'),
    ('20260003', 'sv03', 'Phạm Quốc Bảo', '08_ĐH_KTPM', 'Kỹ thuật phần mềm'),
    ('20260004', 'sv04', 'Vũ Minh Anh', '08_ĐH_KTPM', 'Kỹ thuật phần mềm'),
    ('20260005', 'sv05', 'Đặng Hoàng Long', '08_ĐH_HTTT', 'Hệ thống thông tin'),
    ('20260006', 'sv06', 'Nguyễn Mai Phương', '08_ĐH_HTTT', 'Hệ thống thông tin')
) AS student(mssv, username, ho_ten, lop, nganh)
JOIN auth_user ON auth_user.username = student.username;

INSERT INTO registration_monhocdahoanthanh
    (sinh_vien_id, mon_hoc_id, hoc_ky_id, diem, ngay_hoan_thanh)
VALUES
    ('1250080038', 'INT101', NULL, 8.50, '2025-12-20'),
    ('1250080038', 'INT102', NULL, 8.00, '2026-05-25'),
    ('1250080038', 'MTH101', NULL, 7.50, '2025-12-20');

INSERT INTO registration_tieuchiuutien
    (sinh_vien_id, ca_uu_tien, so_ngay_hoc_toi_da, han_che_tiet_trong)
SELECT mssv, 'BAT_KY', 4, TRUE
FROM registration_sinhvien;

-- Hai bản ghi mẫu giúp kiểm tra danh sách đăng ký; sĩ số hiện tại tương ứng
-- đã được khởi tạo là 1 cho INT101_01 và INT102_02 ở phía trên.
INSERT INTO registration_dangky
    (sinh_vien_id, lop_hoc_phan_id, dot_dang_ky_id)
SELECT student.mssv, student.ma_lhp, registration_dotdangky.id
FROM (VALUES
    ('20260001', 'INT101_01'),
    ('20260002', 'INT102_02')
) AS student(mssv, ma_lhp)
CROSS JOIN registration_dotdangky
WHERE registration_dotdangky.ten_dot =
    'Đợt 1 - Học kỳ 1 Năm học 2026-2027';

COMMIT;

-- =========================================================
-- KIỂM TRA NHANH SAU KHI TẠO
-- =========================================================
SELECT 'registration_monhoc' AS bang, COUNT(*) AS so_ban_ghi FROM registration_monhoc
UNION ALL
SELECT 'registration_lophocphan', COUNT(*) FROM registration_lophocphan
UNION ALL
SELECT 'registration_chuongtrinhdaotao', COUNT(*) FROM registration_chuongtrinhdaotao
UNION ALL
SELECT 'registration_hocky', COUNT(*) FROM registration_hocky
UNION ALL
SELECT 'registration_sinhvien', COUNT(*) FROM registration_sinhvien
UNION ALL
SELECT 'registration_monhocdahoanthanh', COUNT(*) FROM registration_monhocdahoanthanh
UNION ALL
SELECT 'registration_tieuchiuutien', COUNT(*) FROM registration_tieuchiuutien
UNION ALL
SELECT 'registration_dangky', COUNT(*) FROM registration_dangky;
