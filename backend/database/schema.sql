-- =====================================================================
-- NỀN TẢNG KẾT NỐI SINH VIÊN – DOANH NGHIỆP – NHÀ TRƯỜNG
-- Database schema cho MariaDB 10.5+ (InnoDB, utf8mb4)
-- =====================================================================
-- Quy ước:
--   * Khóa chính: BIGINT UNSIGNED AUTO_INCREMENT, tên cột `id`
--   * Khóa ngoại: <bảng_số_ít>_id, ràng buộc đặt tên fk_<bảng>_<cột>
--   * Thời gian: DATETIME, lưu UTC ở tầng ứng dụng
--   * Trạng thái cố định (workflow) dùng ENUM; danh mục do trường quản lý dùng bảng riêng
--   * Luồng tuyển dụng: jobs.term_id IS NULL  => Ứng tuyển tự do
--                       jobs.term_id NOT NULL => Thực tập theo đợt
--   * GPA theo thang 4.0 (đổi CHECK nếu trường dùng thang 10)
-- =====================================================================

SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS student_connect
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE student_connect;

-- =====================================================================
-- 1. AUTH & PHÂN QUYỀN
-- =====================================================================

CREATE TABLE users (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email          VARCHAR(255) NOT NULL,
  password_hash  VARCHAR(255) NULL COMMENT 'NULL khi tài khoản import chưa kích hoạt',
  role           ENUM('STUDENT','COMPANY','ADMIN') NOT NULL,
  status         ENUM('PENDING_ACTIVATION','PENDING_APPROVAL','ACTIVE','LOCKED')
                 NOT NULL DEFAULT 'PENDING_ACTIVATION'
                 COMMENT 'Student: PENDING_ACTIVATION->ACTIVE; Company: PENDING_APPROVAL->ACTIVE',
  locked_reason  VARCHAR(500) NULL,
  last_login_at  DATETIME NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_role_status (role, status)
) ENGINE=InnoDB;

CREATE TABLE password_reset_tokens (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  token_hash  CHAR(64) NOT NULL COMMENT 'SHA-256 của token, không lưu token gốc',
  expires_at  DATETIME NOT NULL,
  used_at     DATETIME NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_prt_token_hash (token_hash),
  KEY idx_prt_user (user_id),
  CONSTRAINT fk_prt_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- 2. DANH MỤC DÙNG CHUNG
-- =====================================================================

CREATE TABLE faculties (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code       VARCHAR(30) NOT NULL,
  name       VARCHAR(255) NOT NULL,
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_faculties_code (code),
  UNIQUE KEY uq_faculties_name (name)
) ENGINE=InnoDB;

CREATE TABLE majors (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  faculty_id  BIGINT UNSIGNED NOT NULL,
  code        VARCHAR(30) NOT NULL,
  name        VARCHAR(255) NOT NULL,
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_majors_code (code),
  KEY idx_majors_faculty (faculty_id),
  CONSTRAINT fk_majors_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(id)
) ENGINE=InnoDB;

CREATE TABLE industries (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name       VARCHAR(255) NOT NULL COMMENT 'Lĩnh vực / ngành nghề tuyển dụng',
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_industries_name (name)
) ENGINE=InnoDB;

CREATE TABLE job_types (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code       VARCHAR(30) NOT NULL COMMENT 'INTERN, FRESHER, PART_TIME, FULL_TIME...',
  name       VARCHAR(100) NOT NULL,
  is_active  TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_job_types_code (code)
) ENGINE=InnoDB;

CREATE TABLE skills (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name        VARCHAR(100) NOT NULL COMMENT 'Tên chuẩn hóa, vd: React',
  category    VARCHAR(100) NULL COMMENT 'Vd: Frontend, Backend, Database, Soft skill',
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_skills_name (name),
  KEY idx_skills_category (category)
) ENGINE=InnoDB;

-- Alias để chuẩn hóa kết quả LLM: "ReactJS", "React.js" => React
CREATE TABLE skill_aliases (
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  skill_id  BIGINT UNSIGNED NOT NULL,
  alias     VARCHAR(100) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_skill_aliases_alias (alias),
  KEY idx_skill_aliases_skill (skill_id),
  CONSTRAINT fk_skill_aliases_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- 3. HỒ SƠ NHÀ TRƯỜNG: ADMIN, GIẢNG VIÊN, IMPORT
-- =====================================================================

CREATE TABLE admins (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  full_name   VARCHAR(255) NOT NULL,
  faculty_id  BIGINT UNSIGNED NULL COMMENT 'NULL = quản trị toàn trường',
  position    VARCHAR(100) NULL,
  phone       VARCHAR(20) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_admins_user (user_id),
  CONSTRAINT fk_admins_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_admins_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(id)
) ENGINE=InnoDB;

CREATE TABLE lecturers (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code        VARCHAR(30) NULL,
  full_name   VARCHAR(255) NOT NULL,
  faculty_id  BIGINT UNSIGNED NOT NULL,
  email       VARCHAR(255) NULL,
  phone       VARCHAR(20) NULL,
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_lecturers_code (code),
  KEY idx_lecturers_faculty (faculty_id),
  CONSTRAINT fk_lecturers_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(id)
) ENGINE=InnoDB;

CREATE TABLE import_batches (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  type          ENUM('STUDENTS','TERM_STUDENTS','SYNC') NOT NULL,
  file_name     VARCHAR(255) NULL,
  total_rows    INT UNSIGNED NOT NULL DEFAULT 0,
  success_rows  INT UNSIGNED NOT NULL DEFAULT 0,
  failed_rows   INT UNSIGNED NOT NULL DEFAULT 0,
  error_report  JSON NULL COMMENT 'Danh sách dòng lỗi + lý do',
  imported_by   BIGINT UNSIGNED NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_import_batches_user (imported_by),
  CONSTRAINT fk_import_batches_user FOREIGN KEY (imported_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- =====================================================================
-- 4. SINH VIÊN
-- =====================================================================

-- 4.1 Dữ liệu CHÍNH THỨC từ nhà trường (chỉ đọc với sinh viên)
CREATE TABLE students (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id          BIGINT UNSIGNED NOT NULL,
  student_code     VARCHAR(30) NOT NULL,
  full_name        VARCHAR(255) NOT NULL,
  date_of_birth    DATE NULL,
  class_name       VARCHAR(50) NULL,
  faculty_id       BIGINT UNSIGNED NOT NULL,
  major_id         BIGINT UNSIGNED NOT NULL,
  cohort           VARCHAR(20) NOT NULL COMMENT 'Khóa học, vd: K65',
  gpa              DECIMAL(3,2) NULL,
  academic_result  VARCHAR(50) NULL COMMENT 'Xếp loại học lực',
  phone            VARCHAR(20) NULL,
  import_batch_id  BIGINT UNSIGNED NULL,
  synced_at        DATETIME NULL COMMENT 'Lần đồng bộ gần nhất từ nhà trường',
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_students_user (user_id),
  UNIQUE KEY uq_students_code (student_code),
  KEY idx_students_faculty_major (faculty_id, major_id),
  KEY idx_students_cohort (cohort),
  CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_students_faculty FOREIGN KEY (faculty_id) REFERENCES faculties(id),
  CONSTRAINT fk_students_major FOREIGN KEY (major_id) REFERENCES majors(id),
  CONSTRAINT fk_students_import FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE SET NULL,
  CONSTRAINT chk_students_gpa CHECK (gpa IS NULL OR (gpa >= 0 AND gpa <= 4))
) ENGINE=InnoDB;

-- Nghiên cứu khoa học, thành tích: do nhà trường xác nhận
CREATE TABLE student_achievements (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id   BIGINT UNSIGNED NOT NULL,
  type         ENUM('RESEARCH','ACHIEVEMENT','OTHER') NOT NULL,
  title        VARCHAR(255) NOT NULL,
  description  TEXT NULL,
  achieved_at  DATE NULL,
  import_batch_id BIGINT UNSIGNED NULL,
  PRIMARY KEY (id),
  KEY idx_sach_student (student_id),
  CONSTRAINT fk_sach_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_sach_import FOREIGN KEY (import_batch_id) REFERENCES import_batches(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 4.2 Dữ liệu TỰ KHAI BÁO của sinh viên
CREATE TABLE student_profiles (
  student_id          BIGINT UNSIGNED NOT NULL,
  avatar_url          VARCHAR(500) NULL,
  bio                 TEXT NULL,
  career_goal         TEXT NULL,
  contact_email       VARCHAR(255) NULL,
  contact_phone       VARCHAR(20) NULL,
  address             VARCHAR(500) NULL,
  linkedin_url        VARCHAR(500) NULL,
  github_url          VARCHAR(500) NULL,
  -- Quyền riêng tư cho gợi ý ứng viên (mục 3.4)
  is_open_to_work     TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 = cho phép doanh nghiệp tìm thấy',
  show_gpa            TINYINT(1) NOT NULL DEFAULT 0,
  show_contact        TINYINT(1) NOT NULL DEFAULT 0,
  show_achievements   TINYINT(1) NOT NULL DEFAULT 1,
  updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (student_id),
  CONSTRAINT fk_sprofiles_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE student_skills (
  student_id  BIGINT UNSIGNED NOT NULL,
  skill_id    BIGINT UNSIGNED NOT NULL,
  level       ENUM('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT') NOT NULL DEFAULT 'BEGINNER',
  source      ENUM('SELF','CV_AI','SCHOOL') NOT NULL DEFAULT 'SELF'
              COMMENT 'SELF: tự khai; CV_AI: trích từ CV; SCHOOL: do trường xác nhận',
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (student_id, skill_id),
  KEY idx_sskills_skill (skill_id),
  CONSTRAINT fk_sskills_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_sskills_skill FOREIGN KEY (skill_id) REFERENCES skills(id)
) ENGINE=InnoDB;

CREATE TABLE student_experiences (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id    BIGINT UNSIGNED NOT NULL,
  company_name  VARCHAR(255) NOT NULL,
  position      VARCHAR(255) NOT NULL,
  start_date    DATE NULL,
  end_date      DATE NULL,
  description   TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_sexp_student (student_id),
  CONSTRAINT fk_sexp_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE student_projects (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id    BIGINT UNSIGNED NOT NULL,
  name          VARCHAR(255) NOT NULL,
  role          VARCHAR(255) NULL,
  description   TEXT NULL,
  tech_stack    VARCHAR(500) NULL,
  project_url   VARCHAR(500) NULL,
  start_date    DATE NULL,
  end_date      DATE NULL,
  PRIMARY KEY (id),
  KEY idx_sproj_student (student_id),
  CONSTRAINT fk_sproj_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Chứng chỉ: source phân biệt do trường xác nhận hay sinh viên tự khai
CREATE TABLE student_certificates (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id     BIGINT UNSIGNED NOT NULL,
  name           VARCHAR(255) NOT NULL,
  issuer         VARCHAR(255) NULL,
  issued_at      DATE NULL,
  expires_at     DATE NULL,
  credential_url VARCHAR(500) NULL,
  source         ENUM('SCHOOL','SELF') NOT NULL DEFAULT 'SELF',
  is_verified    TINYINT(1) NOT NULL DEFAULT 0,
  verified_by    BIGINT UNSIGNED NULL,
  verified_at    DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_scert_student (student_id),
  CONSTRAINT fk_scert_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_scert_verifier FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 4.3 CV
CREATE TABLE cvs (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id      BIGINT UNSIGNED NOT NULL,
  title           VARCHAR(255) NOT NULL,
  type            ENUM('UPLOADED','ONLINE') NOT NULL,
  file_url        VARCHAR(500) NULL COMMENT 'Bắt buộc với UPLOADED (PDF/DOCX), hoặc bản export của ONLINE',
  content_json    JSON NULL COMMENT 'Nội dung CV tạo trực tuyến',
  is_default      TINYINT(1) NOT NULL DEFAULT 0,
  -- Kết quả phân tích AI (mục 5.1), cache để không gọi lại API
  extracted_text  MEDIUMTEXT NULL,
  parsed_json     JSON NULL COMMENT 'Kỹ năng, kinh nghiệm, dự án, lĩnh vực đã chuẩn hóa',
  content_hash    CHAR(64) NULL COMMENT 'Hash nội dung, đổi hash => cần phân tích lại',
  parsed_at       DATETIME NULL,
  deleted_at      DATETIME NULL COMMENT 'Xóa mềm: Application vẫn tham chiếu được',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_cvs_student (student_id, is_default),
  CONSTRAINT fk_cvs_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- 5. DOANH NGHIỆP
-- =====================================================================

CREATE TABLE companies (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id              BIGINT UNSIGNED NOT NULL,
  name                 VARCHAR(255) NOT NULL,
  tax_code             VARCHAR(20) NOT NULL,
  industry_id          BIGINT UNSIGNED NULL,
  company_size         ENUM('1-10','11-50','51-200','201-500','501-1000','1000+') NULL,
  address              VARCHAR(500) NULL,
  website              VARCHAR(255) NULL,
  logo_url             VARCHAR(500) NULL,
  description          TEXT NULL,
  tech_stack           VARCHAR(500) NULL,
  benefits             TEXT NULL,
  contact_name         VARCHAR(255) NULL,
  contact_phone        VARCHAR(20) NULL,
  -- Xác thực bởi nhà trường
  verification_status  ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  verified_by          BIGINT UNSIGNED NULL,
  verified_at          DATETIME NULL,
  reject_reason        VARCHAR(500) NULL,
  created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_companies_user (user_id),
  UNIQUE KEY uq_companies_tax_code (tax_code),
  KEY idx_companies_status (verification_status),
  KEY idx_companies_industry (industry_id),
  CONSTRAINT fk_companies_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_companies_industry FOREIGN KEY (industry_id) REFERENCES industries(id),
  CONSTRAINT fk_companies_verifier FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE company_documents (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  company_id   BIGINT UNSIGNED NOT NULL,
  doc_type     ENUM('BUSINESS_LICENSE','TAX_CERTIFICATE','AUTHORIZATION_LETTER','OTHER') NOT NULL,
  file_url     VARCHAR(500) NOT NULL,
  uploaded_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_cdocs_company (company_id),
  CONSTRAINT fk_cdocs_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- 6. THỰC TẬP THEO ĐỢT
-- =====================================================================

CREATE TABLE internship_terms (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name           VARCHAR(255) NOT NULL,
  semester       VARCHAR(20) NOT NULL COMMENT 'Vd: HK1',
  academic_year  VARCHAR(20) NOT NULL COMMENT 'Vd: 2025-2026',
  start_date     DATE NOT NULL,
  end_date       DATE NOT NULL,
  status         ENUM('DRAFT','OPEN','ONGOING','CLOSED') NOT NULL DEFAULT 'DRAFT',
  created_by     BIGINT UNSIGNED NOT NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_terms_year (academic_year, semester),
  CONSTRAINT fk_terms_creator FOREIGN KEY (created_by) REFERENCES users(id),
  CONSTRAINT chk_terms_dates CHECK (start_date <= end_date)
) ENGINE=InnoDB;

-- Danh sách sinh viên thuộc đợt + giảng viên hướng dẫn
CREATE TABLE term_students (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  term_id      BIGINT UNSIGNED NOT NULL,
  student_id   BIGINT UNSIGNED NOT NULL,
  lecturer_id  BIGINT UNSIGNED NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_term_students (term_id, student_id),
  KEY idx_term_students_student (student_id),
  KEY idx_term_students_lecturer (lecturer_id),
  CONSTRAINT fk_ts_term FOREIGN KEY (term_id) REFERENCES internship_terms(id) ON DELETE CASCADE,
  CONSTRAINT fk_ts_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_ts_lecturer FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 7. TIN TUYỂN DỤNG
-- =====================================================================

CREATE TABLE jobs (
  id                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  company_id             BIGINT UNSIGNED NOT NULL,
  term_id                BIGINT UNSIGNED NULL COMMENT 'NULL = ứng tuyển tự do; có giá trị = thuộc đợt thực tập',
  title                  VARCHAR(255) NOT NULL,
  position               VARCHAR(255) NOT NULL,
  job_type_id            BIGINT UNSIGNED NOT NULL,
  industry_id            BIGINT UNSIGNED NULL,
  description            MEDIUMTEXT NOT NULL,
  requirements           MEDIUMTEXT NULL,
  benefits               TEXT NULL,
  quantity               INT UNSIGNED NOT NULL DEFAULT 1,
  salary_min             INT UNSIGNED NULL,
  salary_max             INT UNSIGNED NULL,
  is_salary_negotiable   TINYINT(1) NOT NULL DEFAULT 0,
  location               VARCHAR(255) NULL,
  work_mode              ENUM('ONSITE','REMOTE','HYBRID') NOT NULL DEFAULT 'ONSITE',
  min_gpa                DECIMAL(3,2) NULL,
  min_experience_months  SMALLINT UNSIGNED NULL,
  deadline               DATE NOT NULL,
  status                 ENUM('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','CLOSED','EXPIRED')
                         NOT NULL DEFAULT 'DRAFT'
                         COMMENT 'Chỉ APPROVED mới hiển thị cho sinh viên',
  approved_by            BIGINT UNSIGNED NULL,
  approved_at            DATETIME NULL,
  reject_reason          VARCHAR(500) NULL,
  view_count             INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Denormalize từ job_views để đọc nhanh',
  -- Kết quả phân tích AI (mục 5.2)
  parsed_json            JSON NULL,
  content_hash           CHAR(64) NULL,
  parsed_at              DATETIME NULL,
  created_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_jobs_company (company_id),
  KEY idx_jobs_term (term_id),
  KEY idx_jobs_status_deadline (status, deadline),
  KEY idx_jobs_type (job_type_id),
  KEY idx_jobs_industry (industry_id),
  FULLTEXT KEY ft_jobs_search (title, position, description),
  CONSTRAINT fk_jobs_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  CONSTRAINT fk_jobs_term FOREIGN KEY (term_id) REFERENCES internship_terms(id) ON DELETE SET NULL,
  CONSTRAINT fk_jobs_type FOREIGN KEY (job_type_id) REFERENCES job_types(id),
  CONSTRAINT fk_jobs_industry FOREIGN KEY (industry_id) REFERENCES industries(id),
  CONSTRAINT fk_jobs_approver FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT chk_jobs_salary CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max),
  CONSTRAINT chk_jobs_gpa CHECK (min_gpa IS NULL OR (min_gpa >= 0 AND min_gpa <= 4))
) ENGINE=InnoDB;

-- Ngành học được phép ứng tuyển (điều kiện bắt buộc khi matching). Không có dòng = mọi ngành
CREATE TABLE job_majors (
  job_id    BIGINT UNSIGNED NOT NULL,
  major_id  BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (job_id, major_id),
  KEY idx_job_majors_major (major_id),
  CONSTRAINT fk_job_majors_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_job_majors_major FOREIGN KEY (major_id) REFERENCES majors(id)
) ENGINE=InnoDB;

CREATE TABLE job_skills (
  job_id       BIGINT UNSIGNED NOT NULL,
  skill_id     BIGINT UNSIGNED NOT NULL,
  is_required  TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1 = bắt buộc, 0 = ưu tiên',
  PRIMARY KEY (job_id, skill_id),
  KEY idx_job_skills_skill (skill_id),
  CONSTRAINT fk_job_skills_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_job_skills_skill FOREIGN KEY (skill_id) REFERENCES skills(id)
) ENGINE=InnoDB;

CREATE TABLE job_views (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  job_id     BIGINT UNSIGNED NOT NULL,
  user_id    BIGINT UNSIGNED NULL COMMENT 'NULL nếu chưa đăng nhập',
  viewed_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_job_views_job_time (job_id, viewed_at),
  CONSTRAINT fk_job_views_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_job_views_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE saved_jobs (
  student_id  BIGINT UNSIGNED NOT NULL,
  job_id      BIGINT UNSIGNED NOT NULL,
  saved_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (student_id, job_id),
  KEY idx_saved_jobs_job (job_id),
  CONSTRAINT fk_saved_jobs_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_saved_jobs_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- 8. LỜI MỜI, ỨNG TUYỂN
-- =====================================================================

-- Doanh nghiệp mời sinh viên ứng tuyển (từ gợi ý ứng viên AI)
CREATE TABLE invitations (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  company_id    BIGINT UNSIGNED NOT NULL,
  student_id    BIGINT UNSIGNED NOT NULL,
  job_id        BIGINT UNSIGNED NOT NULL,
  message       TEXT NULL,
  status        ENUM('PENDING','ACCEPTED','DECLINED','EXPIRED') NOT NULL DEFAULT 'PENDING',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  responded_at  DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_invitations_job_student (job_id, student_id),
  KEY idx_invitations_student (student_id, status),
  KEY idx_invitations_company (company_id),
  CONSTRAINT fk_inv_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  CONSTRAINT fk_inv_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_inv_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE applications (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id       BIGINT UNSIGNED NOT NULL,
  job_id           BIGINT UNSIGNED NOT NULL,
  cv_id            BIGINT UNSIGNED NOT NULL,
  cv_snapshot_url  VARCHAR(500) NULL COMMENT 'Bản CV tại thời điểm nộp, doanh nghiệp xem bản này',
  cover_letter     TEXT NULL,
  invitation_id    BIGINT UNSIGNED NULL COMMENT 'Có giá trị nếu ứng tuyển từ lời mời',
  current_status   ENUM('APPLIED','SCREENING','SHORTLISTED','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN')
                   NOT NULL DEFAULT 'APPLIED',
  applied_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_applications_student_job (student_id, job_id),
  KEY idx_applications_job_status (job_id, current_status),
  KEY idx_applications_cv (cv_id),
  CONSTRAINT fk_app_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_cv FOREIGN KEY (cv_id) REFERENCES cvs(id),
  CONSTRAINT fk_app_invitation FOREIGN KEY (invitation_id) REFERENCES invitations(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE application_status_logs (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  application_id  BIGINT UNSIGNED NOT NULL,
  old_status      VARCHAR(20) NULL,
  new_status      VARCHAR(20) NOT NULL,
  changed_by      BIGINT UNSIGNED NULL,
  note            VARCHAR(500) NULL,
  changed_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_asl_application (application_id, changed_at),
  CONSTRAINT fk_asl_application FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
  CONSTRAINT fk_asl_user FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Kết quả thực tập: gắn với (sinh viên, đợt), application chỉ là liên kết tùy chọn
CREATE TABLE internship_results (
  id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  term_student_id       BIGINT UNSIGNED NOT NULL,
  application_id        BIGINT UNSIGNED NULL COMMENT 'Đơn trúng tuyển nơi thực tập (nếu qua nền tảng)',
  company_id            BIGINT UNSIGNED NULL,
  company_evaluation    TEXT NULL,
  company_score         DECIMAL(4,2) NULL,
  evaluated_at          DATETIME NULL,
  lecturer_comment      TEXT NULL,
  lecturer_score        DECIMAL(4,2) NULL,
  result                ENUM('PENDING','PASSED','FAILED') NOT NULL DEFAULT 'PENDING',
  confirmed_by          BIGINT UNSIGNED NULL,
  confirmed_at          DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ir_term_student (term_student_id),
  KEY idx_ir_company (company_id),
  CONSTRAINT fk_ir_term_student FOREIGN KEY (term_student_id) REFERENCES term_students(id) ON DELETE CASCADE,
  CONSTRAINT fk_ir_application FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE SET NULL,
  CONSTRAINT fk_ir_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
  CONSTRAINT fk_ir_confirmer FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 9. AI & JOB MATCHING
-- =====================================================================

-- Mỗi cặp (sinh viên, tin) một dòng; input_hash đổi => kết quả cũ hết hiệu lực, tính lại
CREATE TABLE matching_results (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id      BIGINT UNSIGNED NOT NULL,
  job_id          BIGINT UNSIGNED NOT NULL,
  cv_id           BIGINT UNSIGNED NULL COMMENT 'CV dùng để tính',
  passed_rules    TINYINT(1) NOT NULL COMMENT 'Đạt điều kiện bắt buộc (ngành, GPA, đợt...)',
  score           DECIMAL(5,2) NOT NULL COMMENT 'Điểm tổng 0-100, backend tính',
  skill_score     DECIMAL(5,2) NULL,
  experience_score DECIMAL(5,2) NULL,
  semantic_score  DECIMAL(5,2) NULL COMMENT 'Thành phần ngữ nghĩa (embedding/LLM)',
  matched_skills  JSON NULL,
  missing_skills  JSON NULL,
  explanation     TEXT NULL,
  input_hash      CHAR(64) NOT NULL COMMENT 'Hash(cv.content_hash + job.content_hash + student data + version)',
  model_name      VARCHAR(100) NULL,
  algo_version    VARCHAR(20) NULL,
  computed_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_matching_student_job (student_id, job_id),
  KEY idx_matching_job_score (job_id, score),
  KEY idx_matching_student_score (student_id, score),
  CONSTRAINT fk_matching_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_matching_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_matching_cv FOREIGN KEY (cv_id) REFERENCES cvs(id) ON DELETE SET NULL,
  CONSTRAINT chk_matching_score CHECK (score >= 0 AND score <= 100)
) ENGINE=InnoDB;

-- Theo dõi gọi API NLP: chi phí, lỗi, retry
CREATE TABLE ai_request_logs (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  purpose        ENUM('PARSE_CV','PARSE_JOB','MATCH_EXPLAIN','OTHER') NOT NULL,
  ref_type       VARCHAR(30) NULL,
  ref_id         BIGINT UNSIGNED NULL,
  provider       VARCHAR(50) NULL,
  model_name     VARCHAR(100) NULL,
  input_tokens   INT UNSIGNED NULL,
  output_tokens  INT UNSIGNED NULL,
  status         ENUM('SUCCESS','FAILED') NOT NULL,
  error_message  VARCHAR(500) NULL,
  latency_ms     INT UNSIGNED NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ai_logs_ref (ref_type, ref_id),
  KEY idx_ai_logs_time (created_at)
) ENGINE=InnoDB;

-- =====================================================================
-- 10. THÔNG BÁO, EMAIL, BÁO CÁO VI PHẠM
-- =====================================================================

CREATE TABLE notifications (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  type        VARCHAR(50) NOT NULL COMMENT 'Vd: APPLICATION_STATUS, JOB_APPROVED, INVITATION',
  title       VARCHAR(255) NOT NULL,
  content     TEXT NULL,
  ref_type    VARCHAR(30) NULL,
  ref_id      BIGINT UNSIGNED NULL,
  is_read     TINYINT(1) NOT NULL DEFAULT 0,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_notifications_user (user_id, is_read, created_at),
  CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE email_logs (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id          BIGINT UNSIGNED NULL,
  recipient_email  VARCHAR(255) NOT NULL,
  type             VARCHAR(50) NOT NULL COMMENT 'Vd: APPLY_SUCCESS, STATUS_CHANGED, INTERVIEW_INVITE, JOB_APPROVED, RESET_PASSWORD',
  subject          VARCHAR(255) NOT NULL,
  status           ENUM('PENDING','SENT','FAILED') NOT NULL DEFAULT 'PENDING',
  error_message    VARCHAR(500) NULL,
  retry_count      TINYINT UNSIGNED NOT NULL DEFAULT 0,
  ref_type         VARCHAR(30) NULL COMMENT 'APPLICATION, JOB, INTERNSHIP_RESULT...',
  ref_id           BIGINT UNSIGNED NULL,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sent_at          DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_email_logs_status (status, created_at),
  KEY idx_email_logs_ref (ref_type, ref_id),
  KEY idx_email_logs_user (user_id),
  CONSTRAINT fk_email_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE reports (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  reporter_id      BIGINT UNSIGNED NOT NULL,
  target_type      ENUM('JOB','COMPANY','STUDENT') NOT NULL,
  target_id        BIGINT UNSIGNED NOT NULL,
  reason           VARCHAR(500) NOT NULL,
  status           ENUM('PENDING','RESOLVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  handled_by       BIGINT UNSIGNED NULL,
  handled_at       DATETIME NULL,
  resolution_note  VARCHAR(500) NULL,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_reports_target (target_type, target_id),
  KEY idx_reports_status (status, created_at),
  CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_reports_handler FOREIGN KEY (handled_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 11. DỮ LIỆU KHỞI TẠO
-- =====================================================================

INSERT INTO job_types (code, name) VALUES
  ('INTERN',    'Thực tập'),
  ('FRESHER',   'Fresher'),
  ('PART_TIME', 'Bán thời gian'),
  ('FULL_TIME', 'Toàn thời gian');

-- =====================================================================
-- GHI CHÚ TRIỂN KHAI (ràng buộc nghiệp vụ DB không tự kiểm soát)
-- =====================================================================
-- 1. Job thuộc đợt (term_id NOT NULL): chỉ cho ứng tuyển nếu sinh viên có trong term_students.
-- 2. Chỉ hiển thị jobs.status = 'APPROVED' AND deadline >= CURDATE(); job hết hạn chuyển EXPIRED bằng job định kỳ.
-- 3. Mỗi sinh viên chỉ nên có 1 CV is_default = 1 (xử lý ở service khi set default).
-- 4. Doanh nghiệp chỉ được đăng tin khi companies.verification_status = 'APPROVED'.
-- 5. Khi nộp đơn: copy file CV vào cv_snapshot_url, ghi application_status_logs (old_status NULL).
-- 6. Gợi ý ứng viên: chỉ lấy student_profiles.is_open_to_work = 1 và che các trường show_* = 0.
-- 7. Matching: backend tính score từ passed_rules + skill/experience; LLM chỉ trích xuất và giải thích.
-- 8. users.role = 'STUDENT' <=> có đúng 1 dòng students; 'COMPANY' <=> companies; 'ADMIN' <=> admins.
-- 9. Không có bảng lịch phỏng vấn: doanh nghiệp tự gửi email lịch cho sinh viên khi đơn ở trạng thái INTERVIEW.
-- 10. Dashboard: group theo students.faculty_id/major_id/cohort, jobs.term_id (NULL = tự do), job_skills.
