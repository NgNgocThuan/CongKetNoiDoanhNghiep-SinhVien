-- ==============================================================================
-- Student Connect: Seed Tài khoản mẫu ĐÃ XÁC THỰC 100% cho từng Actor
-- Database: student_connect_dev
-- Mật khẩu cho tất cả tài khoản: Password@123
-- Hash: $2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG
-- ==============================================================================

USE `student_connect_dev`;

-- 1. Thêm Khoa & Ngành mẫu nếu chưa có
INSERT IGNORE INTO `faculties` (`id`, `code`, `name`) VALUES (1, 'CNTT', 'Khoa Công nghệ thông tin');
INSERT IGNORE INTO `majors` (`id`, `faculty_id`, `code`, `name`) VALUES (1, 1, '7480201', 'Kỹ thuật Phần mềm');

-- 2. Thêm Kỹ năng mẫu
INSERT IGNORE INTO `skills` (`name`, `category`) VALUES 
('Python', 'Backend'),
('FastAPI', 'Backend'),
('React', 'Frontend'),
('TypeScript', 'Frontend'),
('MariaDB', 'Database');

-- ==============================================================================
-- ACTOR 1: ADMIN (Quản trị viên nhà trường)
-- Email: admin@school.edu.vn | Pass: Password@123
-- ==============================================================================
INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `status`, `email_verified_at`, `phone_verified_at`, `created_at`, `updated_at`)
VALUES (101, 'admin@school.edu.vn', '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG', 'ADMIN', 'ACTIVE', NOW(6), NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `role` = 'ADMIN',
    `status` = 'ACTIVE',
    `password_hash` = '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG',
    `email_verified_at` = NOW(6);

SET @admin_user_id = (SELECT `id` FROM `users` WHERE `email` = 'admin@school.edu.vn');

INSERT INTO `admins` (`user_id`, `full_name`, `position`)
VALUES (@admin_user_id, 'Quản trị viên Nhà trường', 'Phòng Hợp tác Doanh nghiệp & Đào tạo')
ON DUPLICATE KEY UPDATE 
    `full_name` = 'Quản trị viên Nhà trường',
    `position` = 'Phòng Hợp tác Doanh nghiệp & Đào tạo';

-- ==============================================================================
-- ACTOR 2: COMPANY (Doanh nghiệp tuyển dụng - Xác thực đầy đủ)
-- Email: company@techcorp.vn | Pass: Password@123
-- ==============================================================================
INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `status`, `email_verified_at`, `phone_verified_at`, `created_at`, `updated_at`)
VALUES (102, 'company@techcorp.vn', '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG', 'COMPANY', 'ACTIVE', NOW(6), NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `role` = 'COMPANY',
    `status` = 'ACTIVE',
    `password_hash` = '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG',
    `email_verified_at` = NOW(6);

SET @company_user_id = (SELECT `id` FROM `users` WHERE `email` = 'company@techcorp.vn');

INSERT INTO `companies` (`user_id`, `name`, `tax_code`, `contact_name`, `contact_phone`, `website`, `address`, `description`, `verification_status`, `business_status`, `operation_status`)
VALUES (@company_user_id, 'Công ty Cổ phần Công nghệ TechCorp', '0109998888', 'Nguyễn Văn Giám Đốc', '02439998888', 'https://techcorp.vn', 'Tầng 10, Keangnam Landmark 72, Hà Nội', 'Doanh nghiệp phát triển phần mềm và giải pháp số.', 'APPROVED', 'VERIFIED', 'ENABLED')
ON DUPLICATE KEY UPDATE 
    `name` = 'Công ty Cổ phần Công nghệ TechCorp',
    `tax_code` = '0109998888',
    `verification_status` = 'APPROVED',
    `business_status` = 'VERIFIED',
    `operation_status` = 'ENABLED';

SET @company_id = (SELECT `id` FROM `companies` WHERE `user_id` = @company_user_id);

-- File lưu trữ mẫu cho MOU
INSERT INTO `stored_files` (`id`, `uploaded_by`, `storage_key`, `original_name`, `content_type`, `size_bytes`, `checksum_sha256`, `category`, `scan_status`, `availability_status`, `created_at`)
VALUES (999, @company_user_id, 'mou_techcorp_2026.pdf', 'mou_techcorp_2026.pdf', 'application/pdf', 1024, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'MOU_DOCUMENT', 'CLEAN', 'AVAILABLE', NOW(6))
ON DUPLICATE KEY UPDATE `availability_status` = 'AVAILABLE';

-- Xác thực doanh nghiệp (CompanyVerification)
INSERT INTO `company_verifications` (`company_id`, `tax_code`, `company_name`, `legal_representative`, `business_address`, `email_otp_verified`, `verification_status`, `reviewer_user_id`, `reviewed_at`, `created_at`, `updated_at`)
VALUES (@company_id, '0109998888', 'Công ty Cổ phần Công nghệ TechCorp', 'Nguyễn Văn Giám Đốc', 'Tầng 10, Keangnam Landmark 72, Hà Nội', 1, 'VERIFIED', @admin_user_id, NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `tax_code` = '0109998888',
    `company_name` = 'Công ty Cổ phần Công nghệ TechCorp',
    `email_otp_verified` = 1,
    `verification_status` = 'VERIFIED',
    `reviewer_user_id` = @admin_user_id,
    `reviewed_at` = NOW(6);

-- Thỏa thuận hợp tác MOU (MouAgreement - Digital Signature)
INSERT INTO `mou_agreements` (`company_id`, `agreement_code`, `document_file_id`, `school_name`, `school_signer_name`, `school_signer_position`, `company_signer_name`, `company_signer_position`, `mou_type`, `signature_method`, `signature_verification_status`, `status`, `signer_tax_code`, `signer_common_name`, `certificate_issuer`, `signed_at`, `effective_from`, `effective_until`, `scope_json`, `reviewed_by`, `reviewed_at`, `created_at`, `updated_at`)
VALUES (@company_id, 'MOU-TECHCORP-2026', 999, 'Trường Đại học Công nghệ', 'PGS.TS. Trần Hiệu Trưởng', 'Hiệu trưởng', 'Nguyễn Văn Giám Đốc', 'Tổng Giám Đốc', 'DIGITAL_SIGNATURE', 'EXTERNALLY_DIGITALLY_SIGNED', 'CRYPTOGRAPHICALLY_VERIFIED', 'ACTIVE', '0109998888', 'CONG TY CO PHAN CONG NGHE TECHCORP', 'VNPT-CA', NOW(6), CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), '{"internship": true, "recruitment": true, "sponsorship": true}', @admin_user_id, NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `status` = 'ACTIVE',
    `signature_verification_status` = 'CRYPTOGRAPHICALLY_VERIFIED',
    `mou_type` = 'DIGITAL_SIGNATURE';

-- ==============================================================================
-- ACTOR 3: STUDENT (Sinh viên / Freelancer)
-- Email: student@school.edu.vn | Pass: Password@123
-- ==============================================================================
INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `status`, `email_verified_at`, `phone_verified_at`, `created_at`, `updated_at`)
VALUES (103, 'student@school.edu.vn', '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG', 'STUDENT', 'ACTIVE', NOW(6), NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `role` = 'STUDENT',
    `status` = 'ACTIVE',
    `password_hash` = '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG',
    `email_verified_at` = NOW(6);

SET @student_user_id = (SELECT `id` FROM `users` WHERE `email` = 'student@school.edu.vn');

INSERT INTO `students` (`user_id`, `student_code`, `full_name`, `class_name`, `cohort`, `faculty_id`, `major_id`, `gpa`, `phone`, `date_of_birth`)
VALUES (@student_user_id, 'SV2026001', 'Nguyễn Văn Sinh Viên', 'CNTT1-K65', 'K65', 1, 1, 3.65, '0912345678', '2003-05-20')
ON DUPLICATE KEY UPDATE 
    `student_code` = 'SV2026001',
    `full_name` = 'Nguyễn Văn Sinh Viên',
    `gpa` = 3.65;

SET @student_id = (SELECT `id` FROM `students` WHERE `user_id` = @student_user_id);

INSERT INTO `student_profiles` (`student_id`, `is_open_to_work`, `show_gpa`, `show_contact`, `show_achievements`, `bio`)
VALUES (@student_id, 1, 1, 1, 1, 'Sinh viên năm 4 chuyên ngành Kỹ thuật Phần mềm, có kinh nghiệm làm Fullstack Web và Freelancer.')
ON DUPLICATE KEY UPDATE 
    `is_open_to_work` = 1,
    `bio` = 'Sinh viên năm 4 chuyên ngành Kỹ thuật Phần mềm, có kinh nghiệm làm Fullstack Web và Freelancer.';

-- ==============================================================================
-- ACTOR 4: CLIENT (Khách hàng thuê Freelancer)
-- Email: client@clientcorp.vn | Pass: Password@123
-- ==============================================================================
INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `status`, `email_verified_at`, `phone_verified_at`, `created_at`, `updated_at`)
VALUES (104, 'client@clientcorp.vn', '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG', 'CLIENT', 'ACTIVE', NOW(6), NOW(6), NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE 
    `role` = 'CLIENT',
    `status` = 'ACTIVE',
    `password_hash` = '$2b$12$qaNrH5RQYups7C0zjNKjsefgcUW.nKK6yNKEPdCbGd5rlMRDa71bG',
    `email_verified_at` = NOW(6);

SET @client_user_id = (SELECT `id` FROM `users` WHERE `email` = 'client@clientcorp.vn');

INSERT INTO `client_profiles` (`user_id`, `full_name`, `address`)
VALUES (@client_user_id, 'Trần Thị Tuyển Dụng', 'Số 20 Duy Tân, Cầu Giấy, Hà Nội')
ON DUPLICATE KEY UPDATE 
    `full_name` = 'Trần Thị Tuyển Dụng',
    `address` = 'Số 20 Duy Tân, Cầu Giấy, Hà Nội';
