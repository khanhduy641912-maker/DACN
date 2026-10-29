-- =========================================================
-- TẠO LẠI DATABASE CHO HỆ THỐNG ĐĂNG KÝ MÔN HỌC
-- Dùng trong pgAdmin Query Tool, kết nối database "postgres".
--
-- CẢNH BÁO: Xóa toàn bộ database QL_DangKyMonHoc và dữ liệu bên trong.
-- Đóng ứng dụng đang dùng database này và sao lưu trước khi tiếp tục.
--
-- Trong pgAdmin, bật Auto-commit. Chạy TỪNG câu lệnh riêng biệt:
-- 1. Chọn và chạy câu SELECT pg_terminate_backend.
-- 2. Chọn và chạy câu DROP DATABASE.
-- 3. Chọn và chạy câu CREATE DATABASE.
-- Sau đó mở Query Tool mới, kết nối QL_DangKyMonHoc và chạy
-- QL_DKMonHoc_manual.sql.
-- =========================================================

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'QL_DangKyMonHoc'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS "QL_DangKyMonHoc";

CREATE DATABASE "QL_DangKyMonHoc"
    WITH ENCODING 'UTF8'
    TEMPLATE template0;
