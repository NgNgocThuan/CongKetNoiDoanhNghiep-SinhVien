CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE ai_request_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    purpose ENUM('PARSE_CV','PARSE_JOB','MATCH_EXPLAIN','OTHER') NOT NULL,
    ref_type VARCHAR(30),
    ref_id BIGINT UNSIGNED,
    provider VARCHAR(50),
    model_name VARCHAR(100),
    input_tokens INTEGER UNSIGNED,
    output_tokens INTEGER UNSIGNED,
    status ENUM('SUCCESS','FAILED') NOT NULL,
    error_message VARCHAR(500),
    latency_ms INTEGER UNSIGNED,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_ai_request_logs PRIMARY KEY (id)
);

CREATE INDEX idx_ai_logs_ref ON ai_request_logs (ref_type, ref_id);

CREATE INDEX idx_ai_logs_time ON ai_request_logs (created_at);

CREATE TABLE faculties (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_faculties PRIMARY KEY (id),
    CONSTRAINT uq_faculties_code UNIQUE (code),
    CONSTRAINT uq_faculties_name UNIQUE (name)
);

CREATE TABLE industries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    is_active BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_industries PRIMARY KEY (id),
    CONSTRAINT uq_industries_name UNIQUE (name)
);

CREATE TABLE job_types (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_job_types PRIMARY KEY (id),
    CONSTRAINT uq_job_types_code UNIQUE (code)
);

CREATE TABLE skills (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    is_active BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_skills PRIMARY KEY (id),
    CONSTRAINT uq_skills_name UNIQUE (name)
);

CREATE INDEX idx_skills_category ON skills (category);

CREATE TABLE users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    `role` ENUM('STUDENT','COMPANY','ADMIN') NOT NULL,
    status ENUM('PENDING_ACTIVATION','PENDING_APPROVAL','ACTIVE','LOCKED') NOT NULL DEFAULT 'PENDING_ACTIVATION',
    locked_reason VARCHAR(500),
    last_login_at DATETIME,
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX idx_users_role_status ON users (`role`, status);

CREATE TABLE admins (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    faculty_id BIGINT UNSIGNED,
    position VARCHAR(100),
    phone VARCHAR(20),
    CONSTRAINT pk_admins PRIMARY KEY (id),
    CONSTRAINT fk_admins_faculty_id_faculties FOREIGN KEY(faculty_id) REFERENCES faculties (id),
    CONSTRAINT fk_admins_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_admins_user_id UNIQUE (user_id)
);

CREATE TABLE companies (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    tax_code VARCHAR(20) NOT NULL,
    industry_id BIGINT UNSIGNED,
    company_size ENUM('1-10','11-50','51-200','201-500','501-1000','1000+'),
    address VARCHAR(500),
    website VARCHAR(255),
    logo_url VARCHAR(500),
    description TEXT,
    tech_stack VARCHAR(500),
    benefits TEXT,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(20),
    verification_status ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
    verified_by BIGINT UNSIGNED,
    verified_at DATETIME,
    reject_reason VARCHAR(500),
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_companies PRIMARY KEY (id),
    CONSTRAINT fk_companies_industry_id_industries FOREIGN KEY(industry_id) REFERENCES industries (id),
    CONSTRAINT fk_companies_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_companies_verified_by_users FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT uq_companies_tax_code UNIQUE (tax_code),
    CONSTRAINT uq_companies_user_id UNIQUE (user_id)
);

CREATE INDEX idx_companies_industry ON companies (industry_id);

CREATE INDEX idx_companies_status ON companies (verification_status);

CREATE TABLE email_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED,
    recipient_email VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status ENUM('PENDING','SENT','FAILED') NOT NULL DEFAULT 'PENDING',
    error_message VARCHAR(500),
    retry_count TINYINT UNSIGNED NOT NULL DEFAULT '0',
    ref_type VARCHAR(30),
    ref_id BIGINT UNSIGNED,
    sent_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_email_logs PRIMARY KEY (id),
    CONSTRAINT fk_email_logs_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_email_logs_ref ON email_logs (ref_type, ref_id);

CREATE INDEX idx_email_logs_status ON email_logs (status, created_at);

CREATE INDEX idx_email_logs_user ON email_logs (user_id);

CREATE TABLE import_batches (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    type ENUM('STUDENTS','TERM_STUDENTS','SYNC') NOT NULL,
    file_name VARCHAR(255),
    total_rows INTEGER UNSIGNED NOT NULL DEFAULT '0',
    success_rows INTEGER UNSIGNED NOT NULL DEFAULT '0',
    failed_rows INTEGER UNSIGNED NOT NULL DEFAULT '0',
    error_report JSON,
    imported_by BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_import_batches PRIMARY KEY (id),
    CONSTRAINT fk_import_batches_imported_by_users FOREIGN KEY(imported_by) REFERENCES users (id)
);

CREATE INDEX idx_import_batches_user ON import_batches (imported_by);

CREATE TABLE internship_terms (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('DRAFT','OPEN','ONGOING','CLOSED') NOT NULL DEFAULT 'DRAFT',
    created_by BIGINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_internship_terms PRIMARY KEY (id),
    CONSTRAINT ck_internship_terms_dates CHECK (start_date <= end_date),
    CONSTRAINT fk_internship_terms_created_by_users FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX idx_terms_year ON internship_terms (academic_year, semester);

CREATE TABLE lecturers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(30),
    full_name VARCHAR(255) NOT NULL,
    faculty_id BIGINT UNSIGNED NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOL NOT NULL DEFAULT '1',
    CONSTRAINT pk_lecturers PRIMARY KEY (id),
    CONSTRAINT fk_lecturers_faculty_id_faculties FOREIGN KEY(faculty_id) REFERENCES faculties (id),
    CONSTRAINT uq_lecturers_code UNIQUE (code)
);

CREATE INDEX idx_lecturers_faculty ON lecturers (faculty_id);

CREATE TABLE majors (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    faculty_id BIGINT UNSIGNED NOT NULL,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_majors PRIMARY KEY (id),
    CONSTRAINT fk_majors_faculty_id_faculties FOREIGN KEY(faculty_id) REFERENCES faculties (id),
    CONSTRAINT uq_majors_code UNIQUE (code)
);

CREATE INDEX idx_majors_faculty ON majors (faculty_id);

CREATE TABLE notifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    ref_type VARCHAR(30),
    ref_id BIGINT UNSIGNED,
    is_read BOOL NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_notifications PRIMARY KEY (id),
    CONSTRAINT fk_notifications_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user ON notifications (user_id, is_read, created_at);

CREATE TABLE password_reset_tokens (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_password_reset_tokens PRIMARY KEY (id),
    CONSTRAINT fk_password_reset_tokens_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_password_reset_tokens_token_hash UNIQUE (token_hash)
);

CREATE INDEX idx_prt_user ON password_reset_tokens (user_id);

CREATE TABLE reports (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    reporter_id BIGINT UNSIGNED NOT NULL,
    target_type ENUM('JOB','COMPANY','STUDENT') NOT NULL,
    target_id BIGINT UNSIGNED NOT NULL,
    reason VARCHAR(500) NOT NULL,
    status ENUM('PENDING','RESOLVED','REJECTED') NOT NULL DEFAULT 'PENDING',
    handled_by BIGINT UNSIGNED,
    handled_at DATETIME,
    resolution_note VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_reports PRIMARY KEY (id),
    CONSTRAINT fk_reports_handled_by_users FOREIGN KEY(handled_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_reports_reporter_id_users FOREIGN KEY(reporter_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_reports_status ON reports (status, created_at);

CREATE INDEX idx_reports_target ON reports (target_type, target_id);

CREATE TABLE skill_aliases (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    skill_id BIGINT UNSIGNED NOT NULL,
    alias VARCHAR(100) NOT NULL,
    CONSTRAINT pk_skill_aliases PRIMARY KEY (id),
    CONSTRAINT fk_skill_aliases_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE,
    CONSTRAINT uq_skill_aliases_alias UNIQUE (alias)
);

CREATE INDEX idx_skill_aliases_skill ON skill_aliases (skill_id);

CREATE TABLE company_documents (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    doc_type ENUM('BUSINESS_LICENSE','TAX_CERTIFICATE','AUTHORIZATION_LETTER','OTHER') NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_company_documents PRIMARY KEY (id),
    CONSTRAINT fk_company_documents_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE
);

CREATE INDEX idx_cdocs_company ON company_documents (company_id);

CREATE TABLE jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    term_id BIGINT UNSIGNED,
    title VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    job_type_id BIGINT UNSIGNED NOT NULL,
    industry_id BIGINT UNSIGNED,
    description MEDIUMTEXT NOT NULL,
    requirements MEDIUMTEXT,
    benefits TEXT,
    quantity INTEGER UNSIGNED NOT NULL DEFAULT '1',
    salary_min INTEGER UNSIGNED,
    salary_max INTEGER UNSIGNED,
    is_salary_negotiable BOOL NOT NULL DEFAULT 0,
    location VARCHAR(255),
    work_mode ENUM('ONSITE','REMOTE','HYBRID') NOT NULL DEFAULT 'ONSITE',
    min_gpa NUMERIC(3, 2),
    min_experience_months SMALLINT UNSIGNED,
    deadline DATE NOT NULL,
    status ENUM('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','CLOSED','EXPIRED') NOT NULL DEFAULT 'DRAFT',
    approved_by BIGINT UNSIGNED,
    approved_at DATETIME,
    reject_reason VARCHAR(500),
    view_count INTEGER UNSIGNED NOT NULL DEFAULT '0',
    parsed_json JSON,
    content_hash VARCHAR(64),
    parsed_at DATETIME,
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_jobs PRIMARY KEY (id),
    CONSTRAINT ck_jobs_gpa_range CHECK (min_gpa IS NULL OR (min_gpa >= 0 AND min_gpa <= 4)),
    CONSTRAINT ck_jobs_salary_range CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max),
    CONSTRAINT fk_jobs_approved_by_users FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_jobs_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_jobs_industry_id_industries FOREIGN KEY(industry_id) REFERENCES industries (id),
    CONSTRAINT fk_jobs_job_type_id_job_types FOREIGN KEY(job_type_id) REFERENCES job_types (id),
    CONSTRAINT fk_jobs_term_id_internship_terms FOREIGN KEY(term_id) REFERENCES internship_terms (id) ON DELETE SET NULL
);

CREATE INDEX idx_jobs_company ON jobs (company_id);

CREATE INDEX idx_jobs_industry ON jobs (industry_id);

CREATE INDEX idx_jobs_status_deadline ON jobs (status, deadline);

CREATE INDEX idx_jobs_term ON jobs (term_id);

CREATE INDEX idx_jobs_type ON jobs (job_type_id);

CREATE TABLE students (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    student_code VARCHAR(30) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    class_name VARCHAR(50),
    faculty_id BIGINT UNSIGNED NOT NULL,
    major_id BIGINT UNSIGNED NOT NULL,
    cohort VARCHAR(20) NOT NULL,
    gpa NUMERIC(3, 2),
    academic_result VARCHAR(50),
    phone VARCHAR(20),
    import_batch_id BIGINT UNSIGNED,
    synced_at DATETIME,
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_students PRIMARY KEY (id),
    CONSTRAINT ck_students_gpa_range CHECK (gpa IS NULL OR (gpa >= 0 AND gpa <= 4)),
    CONSTRAINT fk_students_faculty_id_faculties FOREIGN KEY(faculty_id) REFERENCES faculties (id),
    CONSTRAINT fk_students_import_batch_id_import_batches FOREIGN KEY(import_batch_id) REFERENCES import_batches (id) ON DELETE SET NULL,
    CONSTRAINT fk_students_major_id_majors FOREIGN KEY(major_id) REFERENCES majors (id),
    CONSTRAINT fk_students_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_students_student_code UNIQUE (student_code),
    CONSTRAINT uq_students_user_id UNIQUE (user_id)
);

CREATE INDEX idx_students_cohort ON students (cohort);

CREATE INDEX idx_students_faculty_major ON students (faculty_id, major_id);

CREATE TABLE cvs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    type ENUM('UPLOADED','ONLINE') NOT NULL,
    file_url VARCHAR(500),
    content_json JSON,
    is_default BOOL NOT NULL DEFAULT 0,
    extracted_text MEDIUMTEXT,
    parsed_json JSON,
    content_hash VARCHAR(64),
    parsed_at DATETIME,
    deleted_at DATETIME,
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_cvs PRIMARY KEY (id),
    CONSTRAINT fk_cvs_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_cvs_student ON cvs (student_id, is_default);

CREATE TABLE invitations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    message TEXT,
    status ENUM('PENDING','ACCEPTED','DECLINED','EXPIRED') NOT NULL DEFAULT 'PENDING',
    responded_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_invitations PRIMARY KEY (id),
    CONSTRAINT fk_invitations_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_invitations_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_invitations_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE,
    CONSTRAINT uq_invitations_job_student UNIQUE (job_id, student_id)
);

CREATE INDEX idx_invitations_company ON invitations (company_id);

CREATE INDEX idx_invitations_student ON invitations (student_id, status);

CREATE TABLE job_majors (
    job_id BIGINT UNSIGNED NOT NULL,
    major_id BIGINT UNSIGNED NOT NULL,
    CONSTRAINT pk_job_majors PRIMARY KEY (job_id, major_id),
    CONSTRAINT fk_job_majors_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_job_majors_major_id_majors FOREIGN KEY(major_id) REFERENCES majors (id)
);

CREATE INDEX idx_job_majors_major ON job_majors (major_id);

CREATE TABLE job_skills (
    job_id BIGINT UNSIGNED NOT NULL,
    skill_id BIGINT UNSIGNED NOT NULL,
    is_required BOOL NOT NULL DEFAULT 1,
    CONSTRAINT pk_job_skills PRIMARY KEY (job_id, skill_id),
    CONSTRAINT fk_job_skills_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_job_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE INDEX idx_job_skills_skill ON job_skills (skill_id);

CREATE TABLE job_views (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED,
    viewed_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_job_views PRIMARY KEY (id),
    CONSTRAINT fk_job_views_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_job_views_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_job_views_job_time ON job_views (job_id, viewed_at);

CREATE TABLE saved_jobs (
    student_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    saved_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_saved_jobs PRIMARY KEY (student_id, job_id),
    CONSTRAINT fk_saved_jobs_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_saved_jobs_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_saved_jobs_job ON saved_jobs (job_id);

CREATE TABLE student_achievements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    type ENUM('RESEARCH','ACHIEVEMENT','OTHER') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    achieved_at DATE,
    import_batch_id BIGINT UNSIGNED,
    CONSTRAINT pk_student_achievements PRIMARY KEY (id),
    CONSTRAINT fk_student_achievements_import_batch_id_import_batches FOREIGN KEY(import_batch_id) REFERENCES import_batches (id) ON DELETE SET NULL,
    CONSTRAINT fk_student_achievements_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_sach_student ON student_achievements (student_id);

CREATE TABLE student_certificates (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    issued_at DATE,
    expires_at DATE,
    credential_url VARCHAR(500),
    source ENUM('SCHOOL','SELF') NOT NULL DEFAULT 'SELF',
    is_verified BOOL NOT NULL DEFAULT 0,
    verified_by BIGINT UNSIGNED,
    verified_at DATETIME,
    CONSTRAINT pk_student_certificates PRIMARY KEY (id),
    CONSTRAINT fk_student_certificates_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE,
    CONSTRAINT fk_student_certificates_verified_by_users FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_scert_student ON student_certificates (student_id);

CREATE TABLE student_experiences (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    description TEXT,
    CONSTRAINT pk_student_experiences PRIMARY KEY (id),
    CONSTRAINT fk_student_experiences_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_sexp_student ON student_experiences (student_id);

CREATE TABLE student_profiles (
    student_id BIGINT UNSIGNED NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    career_goal TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    address VARCHAR(500),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    is_open_to_work BOOL NOT NULL DEFAULT 0,
    show_gpa BOOL NOT NULL DEFAULT 0,
    show_contact BOOL NOT NULL DEFAULT 0,
    show_achievements BOOL NOT NULL DEFAULT 1,
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_student_profiles PRIMARY KEY (student_id),
    CONSTRAINT fk_student_profiles_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE TABLE student_projects (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    `role` VARCHAR(255),
    description TEXT,
    tech_stack VARCHAR(500),
    project_url VARCHAR(500),
    start_date DATE,
    end_date DATE,
    CONSTRAINT pk_student_projects PRIMARY KEY (id),
    CONSTRAINT fk_student_projects_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_sproj_student ON student_projects (student_id);

CREATE TABLE student_skills (
    student_id BIGINT UNSIGNED NOT NULL,
    skill_id BIGINT UNSIGNED NOT NULL,
    level ENUM('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT') NOT NULL DEFAULT 'BEGINNER',
    source ENUM('SELF','CV_AI','SCHOOL') NOT NULL DEFAULT 'SELF',
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_student_skills PRIMARY KEY (student_id, skill_id),
    CONSTRAINT fk_student_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id),
    CONSTRAINT fk_student_skills_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE
);

CREATE INDEX idx_sskills_skill ON student_skills (skill_id);

CREATE TABLE term_students (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    term_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    lecturer_id BIGINT UNSIGNED,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_term_students PRIMARY KEY (id),
    CONSTRAINT fk_term_students_lecturer_id_lecturers FOREIGN KEY(lecturer_id) REFERENCES lecturers (id) ON DELETE SET NULL,
    CONSTRAINT fk_term_students_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE,
    CONSTRAINT fk_term_students_term_id_internship_terms FOREIGN KEY(term_id) REFERENCES internship_terms (id) ON DELETE CASCADE,
    CONSTRAINT uq_term_students UNIQUE (term_id, student_id)
);

CREATE INDEX idx_term_students_lecturer ON term_students (lecturer_id);

CREATE INDEX idx_term_students_student ON term_students (student_id);

CREATE TABLE applications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    cv_id BIGINT UNSIGNED NOT NULL,
    cv_snapshot_url VARCHAR(500),
    cover_letter TEXT,
    invitation_id BIGINT UNSIGNED,
    current_status ENUM('APPLIED','SCREENING','SHORTLISTED','INTERVIEW','OFFER','HIRED','REJECTED','WITHDRAWN') NOT NULL DEFAULT 'APPLIED',
    applied_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_applications PRIMARY KEY (id),
    CONSTRAINT fk_applications_cv_id_cvs FOREIGN KEY(cv_id) REFERENCES cvs (id),
    CONSTRAINT fk_applications_invitation_id_invitations FOREIGN KEY(invitation_id) REFERENCES invitations (id) ON DELETE SET NULL,
    CONSTRAINT fk_applications_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_applications_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE,
    CONSTRAINT uq_applications_student_job UNIQUE (student_id, job_id)
);

CREATE INDEX idx_applications_cv ON applications (cv_id);

CREATE INDEX idx_applications_job_status ON applications (job_id, current_status);

CREATE TABLE matching_results (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id BIGINT UNSIGNED NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    cv_id BIGINT UNSIGNED,
    passed_rules BOOL NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    skill_score NUMERIC(5, 2),
    experience_score NUMERIC(5, 2),
    semantic_score NUMERIC(5, 2),
    matched_skills JSON,
    missing_skills JSON,
    explanation TEXT,
    input_hash VARCHAR(64) NOT NULL,
    model_name VARCHAR(100),
    algo_version VARCHAR(20),
    computed_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_matching_results PRIMARY KEY (id),
    CONSTRAINT ck_matching_results_score_range CHECK (score >= 0 AND score <= 100),
    CONSTRAINT fk_matching_results_cv_id_cvs FOREIGN KEY(cv_id) REFERENCES cvs (id) ON DELETE SET NULL,
    CONSTRAINT fk_matching_results_job_id_jobs FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_matching_results_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE CASCADE,
    CONSTRAINT uq_matching_student_job UNIQUE (student_id, job_id)
);

CREATE INDEX idx_matching_job_score ON matching_results (job_id, score);

CREATE INDEX idx_matching_student_score ON matching_results (student_id, score);

CREATE TABLE application_status_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    application_id BIGINT UNSIGNED NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by BIGINT UNSIGNED,
    note VARCHAR(500),
    changed_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_application_status_logs PRIMARY KEY (id),
    CONSTRAINT fk_application_status_logs_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE,
    CONSTRAINT fk_application_status_logs_changed_by_users FOREIGN KEY(changed_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_asl_application ON application_status_logs (application_id, changed_at);

CREATE TABLE internship_results (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    term_student_id BIGINT UNSIGNED NOT NULL,
    application_id BIGINT UNSIGNED,
    company_id BIGINT UNSIGNED,
    company_evaluation TEXT,
    company_score NUMERIC(4, 2),
    evaluated_at DATETIME,
    lecturer_comment TEXT,
    lecturer_score NUMERIC(4, 2),
    result ENUM('PENDING','PASSED','FAILED') NOT NULL DEFAULT 'PENDING',
    confirmed_by BIGINT UNSIGNED,
    confirmed_at DATETIME,
    CONSTRAINT pk_internship_results PRIMARY KEY (id),
    CONSTRAINT fk_internship_results_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE SET NULL,
    CONSTRAINT fk_internship_results_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE SET NULL,
    CONSTRAINT fk_internship_results_confirmed_by_users FOREIGN KEY(confirmed_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_internship_results_term_student_id_term_students FOREIGN KEY(term_student_id) REFERENCES term_students (id) ON DELETE CASCADE,
    CONSTRAINT uq_internship_results_term_student_id UNIQUE (term_student_id)
);

CREATE INDEX idx_ir_company ON internship_results (company_id);

ALTER TABLE jobs ADD FULLTEXT INDEX ft_jobs_search (title, position, description);

INSERT INTO alembic_version (version_num) VALUES ('0001');

-- Running upgrade 0001 -> 0002

CREATE TABLE daily_limit_buckets (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scope_key VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
    local_date DATE NOT NULL,
    limit_amount BIGINT NOT NULL,
    reserved_amount BIGINT NOT NULL DEFAULT '0',
    consumed_amount BIGINT NOT NULL DEFAULT '0',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_daily_limit_buckets PRIMARY KEY (id),
    CONSTRAINT ck_daily_limit_buckets_consumed_amount_amount CHECK (consumed_amount >= 0),
    CONSTRAINT ck_daily_limit_buckets_limit_amount_amount CHECK (limit_amount > 0),
    CONSTRAINT ck_daily_limit_buckets_limit_conservation CHECK (reserved_amount + consumed_amount <= limit_amount),
    CONSTRAINT ck_daily_limit_buckets_reserved_amount_amount CHECK (reserved_amount >= 0),
    CONSTRAINT uq_daily_limit_buckets_scope_key_local_date UNIQUE (scope_key, local_date)
);

CREATE TABLE outbox_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    event_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    event_type VARCHAR(60) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    payload_json JSON NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT '0',
    available_at DATETIME(6) NOT NULL,
    lease_until DATETIME(6),
    locked_by VARCHAR(100) COLLATE utf8mb4_bin,
    last_error TEXT,
    completed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_outbox_events PRIMARY KEY (id),
    CONSTRAINT ck_outbox_events_attempts_nonnegative CHECK (attempts >= 0),
    CONSTRAINT uq_outbox_events_event_key UNIQUE (event_key),
    CONSTRAINT ck_outbox_events_outbox_events_status CHECK (status IN ('PENDING', 'PROCESSING', 'SUCCEEDED', 'RETRY', 'DEAD'))
);

CREATE INDEX ix_outbox_events_status_available_at_lease_until ON outbox_events (status, available_at, lease_until);

CREATE TABLE provider_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    channel_key VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
    event_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    payload_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    payload_json JSON NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'RECEIVED',
    attempts INTEGER NOT NULL DEFAULT '0',
    available_at DATETIME(6) NOT NULL,
    lease_until DATETIME(6),
    last_error TEXT,
    processed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_provider_events PRIMARY KEY (id),
    CONSTRAINT ck_provider_events_attempts_nonnegative CHECK (attempts >= 0),
    CONSTRAINT uq_provider_events_channel_key_event_key UNIQUE (channel_key, event_key),
    CONSTRAINT ck_provider_events_provider_events_event_type CHECK (event_type IN ('PAYMENT', 'PAYOUT')),
    CONSTRAINT ck_provider_events_provider_events_status CHECK (status IN ('RECEIVED', 'PROCESSING', 'PROCESSED', 'UNMATCHED', 'RETRY', 'DEAD', 'PROBE'))
);

CREATE INDEX ix_provider_events_status_available_at_lease_until ON provider_events (status, available_at, lease_until);

CREATE TABLE reconciliation_runs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    period_from DATETIME(6) NOT NULL,
    period_until DATETIME(6) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'RUNNING',
    summary_json JSON,
    started_at DATETIME(6) NOT NULL,
    finished_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_reconciliation_runs PRIMARY KEY (id),
    CONSTRAINT ck_reconciliation_runs_period_dates CHECK (period_until > period_from),
    CONSTRAINT ck_reconciliation_runs_reconciliation_runs_status CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED'))
);

CREATE TABLE scheduled_jobs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    job_type VARCHAR(60) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    payload_json JSON NOT NULL,
    run_at DATETIME(6) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT '0',
    lease_until DATETIME(6),
    locked_by VARCHAR(100) COLLATE utf8mb4_bin,
    last_error TEXT,
    finished_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_scheduled_jobs PRIMARY KEY (id),
    CONSTRAINT ck_scheduled_jobs_attempts_nonnegative CHECK (attempts >= 0),
    CONSTRAINT uq_scheduled_jobs_job_key UNIQUE (job_key),
    CONSTRAINT ck_scheduled_jobs_scheduled_jobs_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'RETRY', 'CANCELLED', 'DEAD'))
);

CREATE INDEX ix_scheduled_jobs_status_run_at_lease_until ON scheduled_jobs (status, run_at, lease_until);

CREATE TABLE audit_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_user_id BIGINT UNSIGNED,
    actor_type VARCHAR(40) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED,
    request_id VARCHAR(100) COLLATE utf8mb4_bin,
    job_key VARCHAR(191) COLLATE utf8mb4_bin,
    reason TEXT,
    before_json JSON,
    after_json JSON,
    ip_hash VARCHAR(64) COLLATE utf8mb4_bin,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_audit_logs PRIMARY KEY (id),
    CONSTRAINT fk_audit_logs_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_audit_logs_audit_logs_actor_type CHECK (actor_type IN ('USER', 'SYSTEM', 'PROVIDER'))
);

CREATE INDEX ix_audit_logs_actor_user_id ON audit_logs (actor_user_id);

CREATE INDEX ix_audit_logs_actor_user_id_created_at ON audit_logs (actor_user_id, created_at);

CREATE INDEX ix_audit_logs_entity_type_entity_id_created_at ON audit_logs (entity_type, entity_id, created_at);

CREATE TABLE bank_destinations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    bank_bin VARCHAR(20) NOT NULL,
    account_number_ciphertext TEXT NOT NULL,
    account_fingerprint VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    account_last4 VARCHAR(4) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    verification_status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    verification_source VARCHAR(40),
    verified_by BIGINT UNSIGNED,
    verified_at DATETIME(6),
    verification_note TEXT,
    encryption_key_version VARCHAR(30) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_bank_destinations PRIMARY KEY (id),
    CONSTRAINT fk_bank_destinations_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_bank_destinations_verified_by_users FOREIGN KEY(verified_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_bank_destinations_user_id_bank_bin_account_fingerprint UNIQUE (user_id, bank_bin, account_fingerprint),
    CONSTRAINT ck_bank_destinations_bank_destinations_verification_status CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED', 'DISABLED'))
);

CREATE INDEX ix_bank_destinations_verified_by ON bank_destinations (verified_by);

CREATE TABLE client_profiles (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    address VARCHAR(500),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_client_profiles PRIMARY KEY (id),
    CONSTRAINT fk_client_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_client_profiles_user_id UNIQUE (user_id)
);

CREATE INDEX ix_client_profiles_user_id ON client_profiles (user_id);

CREATE TABLE command_requests (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    actor_user_id BIGINT UNSIGNED NOT NULL,
    operation VARCHAR(80) NOT NULL,
    idempotency_key VARCHAR(128) COLLATE utf8mb4_bin NOT NULL,
    request_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    result_entity_type VARCHAR(50),
    result_entity_id BIGINT UNSIGNED,
    response_json JSON,
    completed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_command_requests PRIMARY KEY (id),
    CONSTRAINT fk_command_requests_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_command_requests_actor_user_id_operation_idempotency_key UNIQUE (actor_user_id, operation, idempotency_key)
);

CREATE TABLE ledger_journals (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    reference_type VARCHAR(40) NOT NULL,
    reference_id BIGINT UNSIGNED NOT NULL,
    idempotency_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    description VARCHAR(500) NOT NULL,
    reversal_of_id BIGINT UNSIGNED,
    posted_at DATETIME(6) NOT NULL,
    actor_user_id BIGINT UNSIGNED,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_ledger_journals PRIMARY KEY (id),
    CONSTRAINT fk_ledger_journals_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ledger_journals_reversal_of_id_ledger_journals FOREIGN KEY(reversal_of_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT uq_ledger_journals_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT uq_ledger_journals_reversal_of_id UNIQUE (reversal_of_id)
);

CREATE INDEX ix_ledger_journals_actor_user_id ON ledger_journals (actor_user_id);

CREATE INDEX ix_ledger_journals_posted_at ON ledger_journals (posted_at);

CREATE INDEX ix_ledger_journals_reference_type_reference_id ON ledger_journals (reference_type, reference_id);

CREATE INDEX ix_ledger_journals_reversal_of_id ON ledger_journals (reversal_of_id);

CREATE TABLE reconciliation_items (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_id BIGINT UNSIGNED NOT NULL,
    issue_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED,
    issue_type VARCHAR(50) NOT NULL,
    expected_amount BIGINT,
    actual_amount BIGINT,
    details_json JSON NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'OPEN',
    resolved_by BIGINT UNSIGNED,
    resolved_at DATETIME(6),
    resolution_note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_reconciliation_items PRIMARY KEY (id),
    CONSTRAINT ck_reconciliation_items_actual_amount_amount CHECK (actual_amount >= 0),
    CONSTRAINT ck_reconciliation_items_expected_amount_amount CHECK (expected_amount >= 0),
    CONSTRAINT fk_reconciliation_items_resolved_by_users FOREIGN KEY(resolved_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_reconciliation_items_run_id_reconciliation_runs FOREIGN KEY(run_id) REFERENCES reconciliation_runs (id) ON DELETE RESTRICT,
    CONSTRAINT uq_reconciliation_items_run_id_issue_key UNIQUE (run_id, issue_key),
    CONSTRAINT ck_reconciliation_items_reconciliation_items_status CHECK (status IN ('OPEN', 'RESOLVED', 'ACKNOWLEDGED'))
);

CREATE INDEX ix_reconciliation_items_resolved_by ON reconciliation_items (resolved_by);

CREATE INDEX ix_reconciliation_items_status_created_at ON reconciliation_items (status, created_at);

CREATE TABLE stored_files (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    uploaded_by BIGINT UNSIGNED NOT NULL,
    storage_key VARCHAR(500) COLLATE utf8mb4_bin NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(150) NOT NULL,
    size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    category VARCHAR(40) NOT NULL,
    scan_status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    availability_status VARCHAR(40) NOT NULL DEFAULT 'AVAILABLE',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_stored_files PRIMARY KEY (id),
    CONSTRAINT ck_stored_files_size_bytes_nonnegative CHECK (size_bytes > 0),
    CONSTRAINT fk_stored_files_uploaded_by_users FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_stored_files_storage_key UNIQUE (storage_key),
    CONSTRAINT ck_stored_files_stored_files_scan_status CHECK (scan_status IN ('PENDING', 'CLEAN', 'REJECTED')),
    CONSTRAINT ck_stored_files_stored_files_availability_status CHECK (availability_status IN ('AVAILABLE', 'QUARANTINED', 'REMOVED'))
);

CREATE INDEX ix_stored_files_checksum_sha256 ON stored_files (checksum_sha256);

CREATE INDEX ix_stored_files_uploaded_by ON stored_files (uploaded_by);

CREATE INDEX ix_stored_files_uploaded_by_created_at ON stored_files (uploaded_by, created_at);

CREATE TABLE user_verifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    channel VARCHAR(40) NOT NULL,
    purpose VARCHAR(40) NOT NULL,
    target VARCHAR(255) NOT NULL,
    otp_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    key_version VARCHAR(30) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT '0',
    max_attempts INTEGER NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    resend_after DATETIME(6) NOT NULL,
    verified_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_user_verifications PRIMARY KEY (id),
    CONSTRAINT ck_user_verifications_attempt_limit CHECK (attempts <= max_attempts),
    CONSTRAINT ck_user_verifications_attempts_nonnegative CHECK (attempts >= 0),
    CONSTRAINT ck_user_verifications_max_attempts_nonnegative CHECK (max_attempts > 0),
    CONSTRAINT fk_user_verifications_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_user_verifications_user_verifications_channel CHECK (channel IN ('EMAIL', 'PHONE')),
    CONSTRAINT ck_user_verifications_user_verifications_purpose CHECK (purpose IN ('VERIFY_CONTACT', 'CHANGE_CONTACT')),
    CONSTRAINT ck_user_verifications_user_verifications_status CHECK (status IN ('PENDING', 'VERIFIED', 'EXPIRED', 'LOCKED', 'SUPERSEDED'))
);

CREATE INDEX ix_user_verifications_status_expires_at ON user_verifications (status, expires_at);

CREATE INDEX ix_user_verifications_user_id ON user_verifications (user_id);

CREATE INDEX ix_user_verifications_user_id_channel_created_at ON user_verifications (user_id, channel, created_at);

CREATE TABLE business_verifications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    submission_no INTEGER NOT NULL,
    submitted_by BIGINT UNSIGNED NOT NULL,
    submitted_snapshot JSON NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING',
    decided_by BIGINT UNSIGNED,
    decided_at DATETIME(6),
    reason TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_business_verifications PRIMARY KEY (id),
    CONSTRAINT ck_business_verifications_submission_no_nonnegative CHECK (submission_no > 0),
    CONSTRAINT fk_business_verifications_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_business_verifications_decided_by_users FOREIGN KEY(decided_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_business_verifications_submitted_by_users FOREIGN KEY(submitted_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_business_verifications_company_id_submission_no UNIQUE (company_id, submission_no),
    CONSTRAINT ck_business_verifications_business_verifications_status CHECK (status IN ('PENDING', 'NEEDS_REVISION', 'APPROVED', 'REJECTED'))
);

CREATE INDEX ix_business_verifications_decided_by ON business_verifications (decided_by);

CREATE INDEX ix_business_verifications_status_created_at ON business_verifications (status, created_at);

CREATE INDEX ix_business_verifications_submitted_by ON business_verifications (submitted_by);

CREATE TABLE company_limits (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    max_open_projects INTEGER NOT NULL,
    max_project_amount BIGINT NOT NULL,
    max_daily_funding BIGINT NOT NULL,
    full_prefunding_required BOOL NOT NULL,
    source VARCHAR(40) NOT NULL,
    set_by BIGINT UNSIGNED,
    reason TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_company_limits PRIMARY KEY (id),
    CONSTRAINT ck_company_limits_max_daily_funding_amount CHECK (max_daily_funding > 0),
    CONSTRAINT ck_company_limits_max_open_projects_nonnegative CHECK (max_open_projects > 0),
    CONSTRAINT ck_company_limits_max_project_amount_amount CHECK (max_project_amount > 0),
    CONSTRAINT fk_company_limits_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_company_limits_set_by_users FOREIGN KEY(set_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_company_limits_company_id UNIQUE (company_id),
    CONSTRAINT ck_company_limits_company_limits_source CHECK (source IN ('VERIFIED', 'PARTNER', 'OVERRIDE'))
);

CREATE INDEX ix_company_limits_company_id ON company_limits (company_id);

CREATE INDEX ix_company_limits_set_by ON company_limits (set_by);

CREATE TABLE freelance_projects (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    client_user_id BIGINT UNSIGNED NOT NULL,
    company_id BIGINT UNSIGNED,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    budget_amount BIGINT NOT NULL,
    max_students INTEGER NOT NULL,
    recruitment_status VARCHAR(40) NOT NULL DEFAULT 'NOT_OPEN',
    recruitment_closed_at DATETIME(6),
    deadline DATETIME(6) NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    deliverables_description TEXT NOT NULL,
    funding_policy VARCHAR(40) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'DRAFT',
    submitted_at DATETIME(6),
    reviewed_by BIGINT UNSIGNED,
    reviewed_at DATETIME(6),
    review_reason TEXT,
    closed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_freelance_projects PRIMARY KEY (id),
    CONSTRAINT ck_freelance_projects_budget_amount_amount CHECK (budget_amount > 0),
    CONSTRAINT ck_freelance_projects_max_students_nonnegative CHECK (max_students > 0),
    CONSTRAINT fk_freelance_projects_client_user_id_users FOREIGN KEY(client_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_projects_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_projects_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_freelance_projects_freelance_projects_recruitment_status CHECK (recruitment_status IN ('NOT_OPEN', 'OPEN', 'CLOSED')),
    CONSTRAINT ck_freelance_projects_freelance_projects_funding_policy CHECK (funding_policy IN ('FULL', 'PER_MILESTONE')),
    CONSTRAINT ck_freelance_projects_freelance_projects_status CHECK (status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'NEEDS_REVISION', 'REJECTED', 'CANCELLED', 'CLOSED'))
);

CREATE INDEX ix_freelance_projects_client_user_id ON freelance_projects (client_user_id);

CREATE INDEX ix_freelance_projects_client_user_id_status ON freelance_projects (client_user_id, status);

CREATE INDEX ix_freelance_projects_company_id ON freelance_projects (company_id);

CREATE INDEX ix_freelance_projects_company_id_status ON freelance_projects (company_id, status);

CREATE INDEX ix_freelance_projects_reviewed_by ON freelance_projects (reviewed_by);

CREATE INDEX ix_freelance_projects_status_recruitment_status_created_at ON freelance_projects (status, recruitment_status, created_at);

CREATE TABLE mou_agreements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id BIGINT UNSIGNED NOT NULL,
    agreement_code VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
    document_file_id BIGINT UNSIGNED NOT NULL,
    school_name VARCHAR(255) NOT NULL,
    school_signer_name VARCHAR(255) NOT NULL,
    company_signer_name VARCHAR(255) NOT NULL,
    school_signer_position VARCHAR(100) NOT NULL,
    company_signer_position VARCHAR(100) NOT NULL,
    company_authority_file_id BIGINT UNSIGNED,
    school_authority_file_id BIGINT UNSIGNED,
    signature_method VARCHAR(40) NOT NULL,
    signature_verification_status VARCHAR(40) NOT NULL DEFAULT 'NOT_CHECKED',
    signed_at DATETIME(6) NOT NULL,
    effective_from DATETIME(6) NOT NULL,
    effective_until DATETIME(6) NOT NULL,
    scope_json JSON NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PENDING_REVIEW',
    reviewed_by BIGINT UNSIGNED,
    reviewed_at DATETIME(6),
    review_note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_mou_agreements PRIMARY KEY (id),
    CONSTRAINT ck_mou_agreements_effective_dates CHECK (effective_until > effective_from),
    CONSTRAINT fk_mou_agreements_company_authority_file_id_stored_files FOREIGN KEY(company_authority_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_mou_agreements_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_mou_agreements_document_file_id_stored_files FOREIGN KEY(document_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_mou_agreements_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_mou_agreements_school_authority_file_id_stored_files FOREIGN KEY(school_authority_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT uq_mou_agreements_agreement_code UNIQUE (agreement_code),
    CONSTRAINT ck_mou_agreements_mou_agreements_signature_method CHECK (signature_method IN ('SCANNED_SIGNED_DOCUMENT', 'EXTERNALLY_DIGITALLY_SIGNED')),
    CONSTRAINT ck_mou_agreements_mou_agreements_signature_verification_status CHECK (signature_verification_status IN ('NOT_CHECKED', 'MANUALLY_REVIEWED', 'CRYPTOGRAPHICALLY_VERIFIED', 'FAILED')),
    CONSTRAINT ck_mou_agreements_mou_agreements_status CHECK (status IN ('PENDING_REVIEW', 'ACTIVE', 'REJECTED', 'EXPIRED', 'REVOKED', 'SUPERSEDED'))
);

CREATE INDEX ix_mou_agreements_company_authority_file_id ON mou_agreements (company_authority_file_id);

CREATE INDEX ix_mou_agreements_company_id ON mou_agreements (company_id);

CREATE INDEX ix_mou_agreements_company_id_status_effective_until ON mou_agreements (company_id, status, effective_until);

CREATE INDEX ix_mou_agreements_document_file_id ON mou_agreements (document_file_id);

CREATE INDEX ix_mou_agreements_reviewed_by ON mou_agreements (reviewed_by);

CREATE INDEX ix_mou_agreements_school_authority_file_id ON mou_agreements (school_authority_file_id);

CREATE INDEX ix_mou_agreements_status_effective_until ON mou_agreements (status, effective_until);

CREATE TABLE business_verification_files (
    verification_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED NOT NULL,
    document_type VARCHAR(40) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_business_verification_files PRIMARY KEY (verification_id, file_id),
    CONSTRAINT fk_business_verification_files_file_id_stored_files FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_business_verification_files_verification_id_business__622b FOREIGN KEY(verification_id) REFERENCES business_verifications (id) ON DELETE RESTRICT,
    CONSTRAINT ck_business_verification_files_business_verification_fil_7f2f CHECK (document_type IN ('BUSINESS_LICENSE', 'TAX_CERTIFICATE', 'AUTHORIZATION', 'OTHER'))
);

CREATE INDEX ix_business_verification_files_file_id ON business_verification_files (file_id);

CREATE INDEX ix_business_verification_files_verification_id ON business_verification_files (verification_id);

CREATE TABLE freelance_applications (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    proposal TEXT NOT NULL,
    quoted_amount BIGINT NOT NULL,
    estimated_days INTEGER NOT NULL,
    cv_id BIGINT UNSIGNED,
    cv_snapshot_file_id BIGINT UNSIGNED,
    status VARCHAR(40) NOT NULL DEFAULT 'SUBMITTED',
    selected_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_freelance_applications PRIMARY KEY (id),
    CONSTRAINT ck_freelance_applications_estimated_days_nonnegative CHECK (estimated_days > 0),
    CONSTRAINT ck_freelance_applications_quoted_amount_amount CHECK (quoted_amount > 0),
    CONSTRAINT fk_freelance_applications_cv_id_cvs FOREIGN KEY(cv_id) REFERENCES cvs (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_applications_cv_snapshot_file_id_stored_files FOREIGN KEY(cv_snapshot_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_applications_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_applications_student_id_students FOREIGN KEY(student_id) REFERENCES students (id) ON DELETE RESTRICT,
    CONSTRAINT uq_freelance_applications_project_id_student_id UNIQUE (project_id, student_id),
    CONSTRAINT ck_freelance_applications_freelance_applications_status CHECK (status IN ('SUBMITTED', 'SHORTLISTED', 'SELECTED', 'REJECTED', 'WITHDRAWN'))
);

CREATE INDEX ix_freelance_applications_cv_id ON freelance_applications (cv_id);

CREATE INDEX ix_freelance_applications_cv_snapshot_file_id ON freelance_applications (cv_snapshot_file_id);

CREATE INDEX ix_freelance_applications_project_id_status ON freelance_applications (project_id, status);

CREATE INDEX ix_freelance_applications_student_id ON freelance_applications (student_id);

CREATE INDEX ix_freelance_applications_student_id_status_created_at ON freelance_applications (student_id, status, created_at);

CREATE TABLE freelance_project_reviews (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    reviewed_by BIGINT UNSIGNED NOT NULL,
    decision VARCHAR(40) NOT NULL,
    reason TEXT NOT NULL,
    project_snapshot JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_freelance_project_reviews PRIMARY KEY (id),
    CONSTRAINT fk_freelance_project_reviews_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_project_reviews_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_freelance_project_reviews_freelance_project_reviews_decision CHECK (decision IN ('APPROVED', 'NEEDS_REVISION', 'REJECTED'))
);

CREATE INDEX ix_freelance_project_reviews_project_id ON freelance_project_reviews (project_id);

CREATE INDEX ix_freelance_project_reviews_project_id_created_at ON freelance_project_reviews (project_id, created_at);

CREATE INDEX ix_freelance_project_reviews_reviewed_by ON freelance_project_reviews (reviewed_by);

CREATE TABLE freelance_project_skills (
    project_id BIGINT UNSIGNED NOT NULL,
    skill_id BIGINT UNSIGNED NOT NULL,
    is_required BOOL NOT NULL DEFAULT '1',
    CONSTRAINT pk_freelance_project_skills PRIMARY KEY (project_id, skill_id),
    CONSTRAINT fk_freelance_project_skills_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_project_skills_skill_id_skills FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE RESTRICT
);

CREATE INDEX ix_freelance_project_skills_project_id ON freelance_project_skills (project_id);

CREATE INDEX ix_freelance_project_skills_skill_id ON freelance_project_skills (skill_id);

CREATE TABLE project_milestone_proposals (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    sequence_no INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    amount BIGINT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    due_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_project_milestone_proposals PRIMARY KEY (id),
    CONSTRAINT ck_project_milestone_proposals_amount_amount CHECK (amount > 0),
    CONSTRAINT ck_project_milestone_proposals_sequence_no_nonnegative CHECK (sequence_no > 0),
    CONSTRAINT fk_project_milestone_proposals_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT uq_project_milestone_proposals_project_id_sequence_no UNIQUE (project_id, sequence_no)
);

CREATE TABLE freelance_contracts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    application_id BIGINT UNSIGNED NOT NULL,
    client_user_id BIGINT UNSIGNED NOT NULL,
    company_id BIGINT UNSIGNED,
    freelancer_student_id BIGINT UNSIGNED NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'DRAFT',
    effective_version_id BIGINT UNSIGNED,
    activated_at DATETIME(6),
    closed_at DATETIME(6),
    closure_reason TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_freelance_contracts PRIMARY KEY (id),
    CONSTRAINT fk_freelance_contracts_application_id_freelance_applications FOREIGN KEY(application_id) REFERENCES freelance_applications (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_contracts_client_user_id_users FOREIGN KEY(client_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_contracts_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_contracts_freelancer_student_id_students FOREIGN KEY(freelancer_student_id) REFERENCES students (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_contracts_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT uq_freelance_contracts_application_id UNIQUE (application_id),
    CONSTRAINT uq_freelance_contracts_project_id_freelancer_student_id UNIQUE (project_id, freelancer_student_id),
    CONSTRAINT uq_freelance_contracts_project_id_id UNIQUE (project_id, id),
    CONSTRAINT ck_freelance_contracts_freelance_contracts_status CHECK (status IN ('DRAFT', 'PENDING_ACCEPTANCE', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'TERMINATED'))
);

CREATE INDEX ix_freelance_contracts_application_id ON freelance_contracts (application_id);

CREATE INDEX ix_freelance_contracts_client_user_id ON freelance_contracts (client_user_id);

CREATE INDEX ix_freelance_contracts_client_user_id_status ON freelance_contracts (client_user_id, status);

CREATE INDEX ix_freelance_contracts_company_id ON freelance_contracts (company_id);

CREATE INDEX ix_freelance_contracts_freelancer_student_id ON freelance_contracts (freelancer_student_id);

CREATE INDEX ix_freelance_contracts_freelancer_student_id_status ON freelance_contracts (freelancer_student_id, status);

CREATE INDEX ix_freelance_contracts_project_id_status ON freelance_contracts (project_id, status);

CREATE TABLE contract_versions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    version_no INTEGER NOT NULL,
    created_by BIGINT UNSIGNED NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'DRAFT',
    total_amount BIGINT NOT NULL,
    fee_rate_bp SMALLINT UNSIGNED NOT NULL,
    review_period_seconds INTEGER NOT NULL,
    max_revision_count INTEGER NOT NULL,
    grace_period_seconds INTEGER NOT NULL,
    funding_policy VARCHAR(40) NOT NULL,
    terms_json JSON NOT NULL,
    content_hash VARCHAR(64) COLLATE utf8mb4_bin,
    offered_at DATETIME(6),
    acceptance_deadline DATETIME(6),
    client_accepted_at DATETIME(6),
    freelancer_accepted_at DATETIME(6),
    effective_at DATETIME(6),
    response_note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_contract_versions PRIMARY KEY (id),
    CONSTRAINT ck_contract_versions_fee_below_gross CHECK (fee_rate_bp < 10000),
    CONSTRAINT ck_contract_versions_fee_rate_bp_range CHECK (fee_rate_bp <= 10000),
    CONSTRAINT ck_contract_versions_fee_rate_bp_nonnegative CHECK (fee_rate_bp >= 0),
    CONSTRAINT ck_contract_versions_grace_period_seconds_nonnegative CHECK (grace_period_seconds >= 0),
    CONSTRAINT ck_contract_versions_max_revision_count_nonnegative CHECK (max_revision_count >= 0),
    CONSTRAINT ck_contract_versions_review_period_seconds_nonnegative CHECK (review_period_seconds > 0),
    CONSTRAINT ck_contract_versions_total_amount_amount CHECK (total_amount > 0),
    CONSTRAINT ck_contract_versions_version_no_nonnegative CHECK (version_no > 0),
    CONSTRAINT fk_contract_versions_contract_id_freelance_contracts FOREIGN KEY(contract_id) REFERENCES freelance_contracts (id) ON DELETE RESTRICT,
    CONSTRAINT fk_contract_versions_created_by_users FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_contract_versions_contract_id_id UNIQUE (contract_id, id),
    CONSTRAINT uq_contract_versions_contract_id_version_no UNIQUE (contract_id, version_no),
    CONSTRAINT ck_contract_versions_contract_versions_status CHECK (status IN ('DRAFT', 'OFFERED', 'EFFECTIVE', 'DECLINED', 'WITHDRAWN', 'SUPERSEDED', 'EXPIRED')),
    CONSTRAINT ck_contract_versions_contract_versions_funding_policy CHECK (funding_policy IN ('FULL', 'PER_MILESTONE'))
);

CREATE INDEX ix_contract_versions_created_by ON contract_versions (created_by);

CREATE TABLE freelance_reviews (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    reviewer_user_id BIGINT UNSIGNED NOT NULL,
    reviewee_user_id BIGINT UNSIGNED NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    visibility VARCHAR(40) NOT NULL DEFAULT 'VISIBLE',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_freelance_reviews PRIMARY KEY (id),
    CONSTRAINT ck_freelance_reviews_rating_range CHECK (rating <= 5),
    CONSTRAINT ck_freelance_reviews_rating_nonnegative CHECK (rating > 0),
    CONSTRAINT ck_freelance_reviews_distinct_reviewers CHECK (reviewer_user_id <> reviewee_user_id),
    CONSTRAINT fk_freelance_reviews_contract_id_freelance_contracts FOREIGN KEY(contract_id) REFERENCES freelance_contracts (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_reviews_reviewee_user_id_users FOREIGN KEY(reviewee_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_freelance_reviews_reviewer_user_id_users FOREIGN KEY(reviewer_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_freelance_reviews_contract_id_reviewer_user_id UNIQUE (contract_id, reviewer_user_id),
    CONSTRAINT ck_freelance_reviews_freelance_reviews_visibility CHECK (visibility IN ('VISIBLE', 'HIDDEN'))
);

CREATE INDEX ix_freelance_reviews_reviewee_user_id ON freelance_reviews (reviewee_user_id);

CREATE INDEX ix_freelance_reviews_reviewer_user_id ON freelance_reviews (reviewer_user_id);

CREATE TABLE milestones (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    sequence_no INTEGER NOT NULL,
    effective_terms_id BIGINT UNSIGNED,
    status VARCHAR(40) NOT NULL DEFAULT 'NOT_FUNDED',
    started_at DATETIME(6),
    submitted_at DATETIME(6),
    review_deadline DATETIME(6),
    revision_count INTEGER NOT NULL DEFAULT '0',
    accepted_at DATETIME(6),
    acceptance_source VARCHAR(40),
    settled_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_milestones PRIMARY KEY (id),
    CONSTRAINT ck_milestones_revision_count_nonnegative CHECK (revision_count >= 0),
    CONSTRAINT ck_milestones_sequence_no_nonnegative CHECK (sequence_no > 0),
    CONSTRAINT fk_milestones_contract_id_freelance_contracts FOREIGN KEY(contract_id) REFERENCES freelance_contracts (id) ON DELETE RESTRICT,
    CONSTRAINT uq_milestones_contract_id_id UNIQUE (contract_id, id),
    CONSTRAINT uq_milestones_contract_id_sequence_no UNIQUE (contract_id, sequence_no),
    CONSTRAINT ck_milestones_milestones_status CHECK (status IN ('NOT_FUNDED', 'FUNDING_PENDING', 'FUNDED', 'IN_PROGRESS', 'SUBMITTED', 'REVISION_REQUESTED', 'ACCEPTED', 'SETTLEMENT_PENDING', 'PAID_OUT', 'DISPUTED', 'REFUNDED', 'PARTIALLY_RELEASED', 'CANCELLED')),
    CONSTRAINT ck_milestones_milestones_acceptance_source CHECK (acceptance_source IN ('MANUAL', 'AUTO', 'DISPUTE'))
);

CREATE INDEX ix_milestones_status_review_deadline ON milestones (status, review_deadline);

CREATE TABLE project_contract_budgets (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    contract_id BIGINT UNSIGNED NOT NULL,
    allocated_amount BIGINT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'RESERVED',
    committed_at DATETIME(6),
    released_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_project_contract_budgets PRIMARY KEY (id),
    CONSTRAINT ck_project_contract_budgets_allocated_amount_amount CHECK (allocated_amount > 0),
    CONSTRAINT fk_pcb_contract FOREIGN KEY(project_id, contract_id) REFERENCES freelance_contracts (project_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_pcb_project FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT uq_project_contract_budgets_contract_id UNIQUE (contract_id),
    CONSTRAINT ck_project_contract_budgets_project_contract_budgets_status CHECK (status IN ('RESERVED', 'COMMITTED', 'RELEASED'))
);

CREATE INDEX ix_project_contract_budgets_project_id_status ON project_contract_budgets (project_id, status);

CREATE TABLE cancellation_agreements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    requested_by BIGINT UNSIGNED NOT NULL,
    basis VARCHAR(40) NOT NULL,
    reason TEXT NOT NULL,
    freelancer_gross BIGINT NOT NULL,
    refund_amount BIGINT NOT NULL,
    terms_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PROPOSED',
    client_accepted_at DATETIME(6),
    freelancer_accepted_at DATETIME(6),
    policy_snapshot JSON NOT NULL,
    executed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_cancellation_agreements PRIMARY KEY (id),
    CONSTRAINT ck_cancellation_agreements_freelancer_gross_amount CHECK (freelancer_gross >= 0),
    CONSTRAINT ck_cancellation_agreements_refund_amount_amount CHECK (refund_amount >= 0),
    CONSTRAINT fk_cancellation_agreements_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_cancellation_agreements_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_cancellation_agreements_cancellation_agreements_basis CHECK (basis IN ('MUTUAL', 'BEFORE_START', 'OVERDUE')),
    CONSTRAINT ck_cancellation_agreements_cancellation_agreements_status CHECK (status IN ('PROPOSED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXECUTED'))
);

CREATE INDEX ix_cancellation_agreements_milestone_id ON cancellation_agreements (milestone_id);

CREATE INDEX ix_cancellation_agreements_milestone_id_status ON cancellation_agreements (milestone_id, status);

CREATE INDEX ix_cancellation_agreements_requested_by ON cancellation_agreements (requested_by);

CREATE TABLE contract_milestone_terms (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    contract_version_id BIGINT UNSIGNED NOT NULL,
    milestone_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    amount BIGINT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    due_at DATETIME(6) NOT NULL,
    included BOOL NOT NULL DEFAULT '1',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_contract_milestone_terms PRIMARY KEY (id),
    CONSTRAINT ck_contract_milestone_terms_amount_amount CHECK (amount > 0),
    CONSTRAINT fk_cmt_version FOREIGN KEY(contract_id, contract_version_id) REFERENCES contract_versions (contract_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_cmt_milestone FOREIGN KEY(contract_id, milestone_id) REFERENCES milestones (contract_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_contract_milestone_terms_contract_version_id_milestone_id UNIQUE (contract_version_id, milestone_id),
    CONSTRAINT uq_contract_milestone_terms_milestone_id_id UNIQUE (milestone_id, id)
);

CREATE TABLE deliverables (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    submission_no INTEGER NOT NULL,
    submitted_by BIGINT UNSIGNED NOT NULL,
    note TEXT,
    submitted_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_deliverables PRIMARY KEY (id),
    CONSTRAINT ck_deliverables_submission_no_nonnegative CHECK (submission_no > 0),
    CONSTRAINT fk_deliverables_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_deliverables_submitted_by_users FOREIGN KEY(submitted_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_deliverables_milestone_id_id UNIQUE (milestone_id, id),
    CONSTRAINT uq_deliverables_milestone_id_submission_no UNIQUE (milestone_id, submission_no)
);

CREATE INDEX ix_deliverables_submitted_by ON deliverables (submitted_by);

CREATE TABLE disputes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    opened_by BIGINT UNSIGNED NOT NULL,
    reason_code VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'OPEN',
    previous_milestone_status VARCHAR(40) NOT NULL,
    remaining_review_seconds INTEGER,
    evidence_deadline DATETIME(6) NOT NULL,
    assigned_admin_id BIGINT UNSIGNED,
    resolved_at DATETIME(6),
    withdrawal_note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_disputes PRIMARY KEY (id),
    CONSTRAINT ck_disputes_remaining_review_seconds_nonnegative CHECK (remaining_review_seconds >= 0),
    CONSTRAINT fk_disputes_assigned_admin_id_users FOREIGN KEY(assigned_admin_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_disputes_opened_by_users FOREIGN KEY(opened_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_disputes_disputes_status CHECK (status IN ('OPEN', 'EVIDENCE_COLLECTION', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED', 'WITHDRAWN')),
    CONSTRAINT ck_disputes_disputes_previous_milestone_status CHECK (previous_milestone_status IN ('NOT_FUNDED', 'FUNDING_PENDING', 'FUNDED', 'IN_PROGRESS', 'SUBMITTED', 'REVISION_REQUESTED', 'ACCEPTED', 'SETTLEMENT_PENDING', 'PAID_OUT', 'DISPUTED', 'REFUNDED', 'PARTIALLY_RELEASED', 'CANCELLED'))
);

CREATE INDEX ix_disputes_assigned_admin_id ON disputes (assigned_admin_id);

CREATE INDEX ix_disputes_milestone_id ON disputes (milestone_id);

CREATE INDEX ix_disputes_milestone_id_created_at ON disputes (milestone_id, created_at);

CREATE INDEX ix_disputes_opened_by ON disputes (opened_by);

CREATE INDEX ix_disputes_status_evidence_deadline ON disputes (status, evidence_deadline);

CREATE TABLE ledger_accounts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(150) COLLATE utf8mb4_bin NOT NULL,
    kind VARCHAR(40) NOT NULL,
    normal_side VARCHAR(40) NOT NULL,
    owner_user_id BIGINT UNSIGNED,
    milestone_id BIGINT UNSIGNED,
    currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    is_active BOOL NOT NULL DEFAULT '1',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_ledger_accounts PRIMARY KEY (id),
    CONSTRAINT ck_ledger_accounts_vnd_only CHECK (currency = 'VND'),
    CONSTRAINT fk_ledger_accounts_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ledger_accounts_owner_user_id_users FOREIGN KEY(owner_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_ledger_accounts_code UNIQUE (code),
    CONSTRAINT ck_ledger_accounts_ledger_accounts_kind CHECK (kind IN ('PLATFORM_BANK', 'PAYOUT_ACCOUNT', 'UNALLOCATED_RECEIPTS', 'ESCROW_HELD', 'FREELANCER_PAYABLE', 'CLIENT_REFUND_PAYABLE', 'PLATFORM_FEE_REVENUE', 'PROVIDER_FEE_EXPENSE', 'PLATFORM_EQUITY')),
    CONSTRAINT ck_ledger_accounts_ledger_accounts_normal_side CHECK (normal_side IN ('D', 'C'))
);

CREATE INDEX ix_ledger_accounts_milestone_id ON ledger_accounts (milestone_id);

CREATE INDEX ix_ledger_accounts_owner_user_id ON ledger_accounts (owner_user_id);

CREATE TABLE payment_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    payer_user_id BIGINT UNSIGNED NOT NULL,
    expected_amount BIGINT NOT NULL,
    order_code BIGINT NOT NULL,
    payment_link_id VARCHAR(191) COLLATE utf8mb4_bin,
    status VARCHAR(40) NOT NULL DEFAULT 'CREATING',
    request_key VARCHAR(128) COLLATE utf8mb4_bin NOT NULL,
    request_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    checkout_url VARCHAR(1000),
    qr_payload TEXT,
    receiving_account_snapshot JSON NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    paid_at DATETIME(6),
    provider_response_json JSON,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_payment_orders PRIMARY KEY (id),
    CONSTRAINT ck_payment_orders_expected_amount_amount CHECK (expected_amount > 0),
    CONSTRAINT ck_payment_orders_safe_order_code CHECK (order_code > 0 AND order_code <= 9007199254740991),
    CONSTRAINT fk_payment_orders_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_orders_payer_user_id_users FOREIGN KEY(payer_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_payment_orders_order_code UNIQUE (order_code),
    CONSTRAINT uq_payment_orders_payer_user_id_request_key UNIQUE (payer_user_id, request_key),
    CONSTRAINT uq_payment_orders_payment_link_id UNIQUE (payment_link_id),
    CONSTRAINT ck_payment_orders_payment_orders_status CHECK (status IN ('CREATING', 'PENDING', 'PROCESSING', 'PAID', 'EXPIRED', 'CANCELLED', 'FAILED', 'NEEDS_REVIEW', 'UNKNOWN'))
);

CREATE INDEX ix_payment_orders_milestone_id ON payment_orders (milestone_id);

CREATE INDEX ix_payment_orders_milestone_id_created_at ON payment_orders (milestone_id, created_at);

CREATE INDEX ix_payment_orders_status_expires_at ON payment_orders (status, expires_at);

CREATE TABLE active_milestone_disputes (
    milestone_id BIGINT UNSIGNED NOT NULL,
    dispute_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_active_milestone_disputes PRIMARY KEY (milestone_id),
    CONSTRAINT fk_active_milestone_disputes_dispute_id_disputes FOREIGN KEY(dispute_id) REFERENCES disputes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_active_milestone_disputes_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT uq_active_milestone_disputes_dispute_id UNIQUE (dispute_id)
);

CREATE INDEX ix_active_milestone_disputes_dispute_id ON active_milestone_disputes (dispute_id);

CREATE INDEX ix_active_milestone_disputes_milestone_id ON active_milestone_disputes (milestone_id);

CREATE TABLE deliverable_files (
    deliverable_id BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_deliverable_files PRIMARY KEY (deliverable_id, file_id),
    CONSTRAINT fk_deliverable_files_deliverable_id_deliverables FOREIGN KEY(deliverable_id) REFERENCES deliverables (id) ON DELETE RESTRICT,
    CONSTRAINT fk_deliverable_files_file_id_stored_files FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE RESTRICT
);

CREATE INDEX ix_deliverable_files_deliverable_id ON deliverable_files (deliverable_id);

CREATE INDEX ix_deliverable_files_file_id ON deliverable_files (file_id);

CREATE TABLE dispute_decisions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dispute_id BIGINT UNSIGNED NOT NULL,
    revision_no INTEGER NOT NULL,
    outcome VARCHAR(40) NOT NULL,
    freelancer_gross BIGINT NOT NULL,
    refund_amount BIGINT NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PROPOSED',
    requires_second_approval BOOL NOT NULL,
    approval_threshold_snapshot BIGINT NOT NULL,
    proposed_by BIGINT UNSIGNED NOT NULL,
    approved_by BIGINT UNSIGNED,
    approved_at DATETIME(6),
    executed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_dispute_decisions PRIMARY KEY (id),
    CONSTRAINT ck_dispute_decisions_decision_amounts CHECK ((outcome = 'PAYOUT' AND freelancer_gross > 0 AND refund_amount = 0) OR (outcome = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (outcome = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)),
    CONSTRAINT ck_dispute_decisions_approval_threshold_snapshot_amount CHECK (approval_threshold_snapshot >= 0),
    CONSTRAINT ck_dispute_decisions_distinct_approvers CHECK (approved_by IS NULL OR approved_by <> proposed_by),
    CONSTRAINT ck_dispute_decisions_freelancer_gross_amount CHECK (freelancer_gross >= 0),
    CONSTRAINT ck_dispute_decisions_refund_amount_amount CHECK (refund_amount >= 0),
    CONSTRAINT ck_dispute_decisions_revision_no_nonnegative CHECK (revision_no > 0),
    CONSTRAINT fk_dispute_decisions_approved_by_users FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_decisions_dispute_id_disputes FOREIGN KEY(dispute_id) REFERENCES disputes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_decisions_proposed_by_users FOREIGN KEY(proposed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_dispute_decisions_dispute_id_revision_no UNIQUE (dispute_id, revision_no),
    CONSTRAINT ck_dispute_decisions_dispute_decisions_outcome CHECK (outcome IN ('PAYOUT', 'REFUND', 'SPLIT')),
    CONSTRAINT ck_dispute_decisions_dispute_decisions_status CHECK (status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTING', 'EXECUTED', 'SUPERSEDED'))
);

CREATE INDEX ix_dispute_decisions_approved_by ON dispute_decisions (approved_by);

CREATE INDEX ix_dispute_decisions_proposed_by ON dispute_decisions (proposed_by);

CREATE TABLE dispute_evidence (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dispute_id BIGINT UNSIGNED NOT NULL,
    submitted_by BIGINT UNSIGNED NOT NULL,
    file_id BIGINT UNSIGNED,
    deliverable_id BIGINT UNSIGNED,
    note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_dispute_evidence PRIMARY KEY (id),
    CONSTRAINT ck_dispute_evidence_has_evidence CHECK (file_id IS NOT NULL OR deliverable_id IS NOT NULL OR note IS NOT NULL),
    CONSTRAINT fk_dispute_evidence_deliverable_id_deliverables FOREIGN KEY(deliverable_id) REFERENCES deliverables (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_evidence_dispute_id_disputes FOREIGN KEY(dispute_id) REFERENCES disputes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_evidence_file_id_stored_files FOREIGN KEY(file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_evidence_submitted_by_users FOREIGN KEY(submitted_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_dispute_evidence_deliverable_id ON dispute_evidence (deliverable_id);

CREATE INDEX ix_dispute_evidence_dispute_id ON dispute_evidence (dispute_id);

CREATE INDEX ix_dispute_evidence_dispute_id_created_at ON dispute_evidence (dispute_id, created_at);

CREATE INDEX ix_dispute_evidence_file_id ON dispute_evidence (file_id);

CREATE INDEX ix_dispute_evidence_submitted_by ON dispute_evidence (submitted_by);

CREATE TABLE escrow_accounts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    ledger_account_id BIGINT UNSIGNED NOT NULL,
    funded_amount BIGINT NOT NULL,
    reserved_amount BIGINT NOT NULL DEFAULT '0',
    released_gross BIGINT NOT NULL DEFAULT '0',
    refunded_amount BIGINT NOT NULL DEFAULT '0',
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_escrow_accounts PRIMARY KEY (id),
    CONSTRAINT ck_escrow_accounts_funded_amount_amount CHECK (funded_amount > 0),
    CONSTRAINT ck_escrow_accounts_refunded_amount_amount CHECK (refunded_amount >= 0),
    CONSTRAINT ck_escrow_accounts_escrow_conservation CHECK (released_gross + refunded_amount + reserved_amount <= funded_amount),
    CONSTRAINT ck_escrow_accounts_released_gross_amount CHECK (released_gross >= 0),
    CONSTRAINT ck_escrow_accounts_reserved_amount_amount CHECK (reserved_amount >= 0),
    CONSTRAINT fk_escrow_accounts_ledger_account_id_ledger_accounts FOREIGN KEY(ledger_account_id) REFERENCES ledger_accounts (id) ON DELETE RESTRICT,
    CONSTRAINT fk_escrow_accounts_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT uq_escrow_accounts_ledger_account_id UNIQUE (ledger_account_id),
    CONSTRAINT uq_escrow_accounts_milestone_id UNIQUE (milestone_id)
);

CREATE INDEX ix_escrow_accounts_ledger_account_id ON escrow_accounts (ledger_account_id);

CREATE INDEX ix_escrow_accounts_milestone_id ON escrow_accounts (milestone_id);

CREATE TABLE ledger_postings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    journal_id BIGINT UNSIGNED NOT NULL,
    line_no INTEGER NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    side VARCHAR(40) NOT NULL,
    amount BIGINT NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_ledger_postings PRIMARY KEY (id),
    CONSTRAINT ck_ledger_postings_amount_amount CHECK (amount > 0),
    CONSTRAINT ck_ledger_postings_line_no_nonnegative CHECK (line_no > 0),
    CONSTRAINT fk_ledger_postings_account_id_ledger_accounts FOREIGN KEY(account_id) REFERENCES ledger_accounts (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ledger_postings_journal_id_ledger_journals FOREIGN KEY(journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT uq_ledger_postings_journal_id_line_no UNIQUE (journal_id, line_no),
    CONSTRAINT ck_ledger_postings_ledger_postings_side CHECK (side IN ('D', 'C'))
);

CREATE INDEX ix_ledger_postings_account_id ON ledger_postings (account_id);

CREATE INDEX ix_ledger_postings_account_id_journal_id ON ledger_postings (account_id, journal_id);

CREATE TABLE milestone_funding_guards (
    milestone_id BIGINT UNSIGNED NOT NULL,
    payment_order_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_milestone_funding_guards PRIMARY KEY (milestone_id),
    CONSTRAINT fk_milestone_funding_guards_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_funding_guards_payment_order_id_payment_orders FOREIGN KEY(payment_order_id) REFERENCES payment_orders (id) ON DELETE RESTRICT,
    CONSTRAINT uq_milestone_funding_guards_payment_order_id UNIQUE (payment_order_id)
);

CREATE INDEX ix_milestone_funding_guards_milestone_id ON milestone_funding_guards (milestone_id);

CREATE INDEX ix_milestone_funding_guards_payment_order_id ON milestone_funding_guards (payment_order_id);

CREATE TABLE milestone_holds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    reason_type VARCHAR(40) NOT NULL,
    reason_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    dispute_id BIGINT UNSIGNED,
    placed_by BIGINT UNSIGNED,
    note TEXT NOT NULL,
    placed_at DATETIME(6) NOT NULL,
    released_at DATETIME(6),
    released_by BIGINT UNSIGNED,
    release_note TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_milestone_holds PRIMARY KEY (id),
    CONSTRAINT fk_milestone_holds_dispute_id_disputes FOREIGN KEY(dispute_id) REFERENCES disputes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_holds_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_holds_placed_by_users FOREIGN KEY(placed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_holds_released_by_users FOREIGN KEY(released_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_milestone_holds_reason_key UNIQUE (reason_key),
    CONSTRAINT ck_milestone_holds_milestone_holds_reason_type CHECK (reason_type IN ('DISPUTE', 'COMPANY_SUSPENSION', 'ADMIN_REVIEW'))
);

CREATE INDEX ix_milestone_holds_dispute_id ON milestone_holds (dispute_id);

CREATE INDEX ix_milestone_holds_milestone_id ON milestone_holds (milestone_id);

CREATE INDEX ix_milestone_holds_milestone_id_released_at ON milestone_holds (milestone_id, released_at);

CREATE INDEX ix_milestone_holds_placed_by ON milestone_holds (placed_by);

CREATE INDEX ix_milestone_holds_released_by ON milestone_holds (released_by);

CREATE TABLE milestone_reviews (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    deliverable_id BIGINT UNSIGNED NOT NULL,
    reviewed_by BIGINT UNSIGNED,
    action VARCHAR(40) NOT NULL,
    reason TEXT,
    reviewed_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_milestone_reviews PRIMARY KEY (id),
    CONSTRAINT fk_mr_deliverable FOREIGN KEY(milestone_id, deliverable_id) REFERENCES deliverables (milestone_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_reviews_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_milestone_reviews_milestone_reviews_action CHECK (action IN ('ACCEPT', 'REQUEST_REVISION', 'AUTO_ACCEPT'))
);

CREATE INDEX ix_milestone_reviews_milestone_id_created_at ON milestone_reviews (milestone_id, created_at);

CREATE INDEX ix_milestone_reviews_reviewed_by ON milestone_reviews (reviewed_by);

CREATE TABLE payment_transactions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    payment_order_id BIGINT UNSIGNED,
    provider_event_id BIGINT UNSIGNED,
    channel_key VARCHAR(100) COLLATE utf8mb4_bin NOT NULL,
    external_ref VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    receiving_account_ref VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    received_at DATETIME(6) NOT NULL,
    received_time_raw VARCHAR(100),
    allocation_status VARCHAR(40) NOT NULL DEFAULT 'UNALLOCATED',
    receipt_journal_id BIGINT UNSIGNED NOT NULL,
    raw_payload_json JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_payment_transactions PRIMARY KEY (id),
    CONSTRAINT ck_payment_transactions_vnd_only CHECK (currency = 'VND'),
    CONSTRAINT ck_payment_transactions_amount_amount CHECK (amount > 0),
    CONSTRAINT fk_payment_transactions_payment_order_id_payment_orders FOREIGN KEY(payment_order_id) REFERENCES payment_orders (id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_transactions_provider_event_id_provider_events FOREIGN KEY(provider_event_id) REFERENCES provider_events (id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_transactions_receipt_journal_id_ledger_journals FOREIGN KEY(receipt_journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT uq_payment_transactions_channel_key_external_ref UNIQUE (channel_key, external_ref),
    CONSTRAINT uq_payment_transactions_receipt_journal_id UNIQUE (receipt_journal_id),
    CONSTRAINT ck_payment_transactions_payment_transactions_allocation_status CHECK (allocation_status IN ('UNALLOCATED', 'ALLOCATED', 'PARTIALLY_RETURNED', 'RETURNED'))
);

CREATE INDEX ix_payment_transactions_allocation_status_created_at ON payment_transactions (allocation_status, created_at);

CREATE INDEX ix_payment_transactions_payment_order_id ON payment_transactions (payment_order_id);

CREATE INDEX ix_payment_transactions_provider_event_id ON payment_transactions (provider_event_id);

CREATE INDEX ix_payment_transactions_receipt_journal_id ON payment_transactions (receipt_journal_id);

CREATE TABLE milestone_fundings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    payment_transaction_id BIGINT UNSIGNED NOT NULL,
    amount BIGINT NOT NULL,
    funding_journal_id BIGINT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_milestone_fundings PRIMARY KEY (id),
    CONSTRAINT ck_milestone_fundings_amount_amount CHECK (amount > 0),
    CONSTRAINT fk_milestone_fundings_funding_journal_id_ledger_journals FOREIGN KEY(funding_journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_fundings_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_milestone_fundings_payment_transaction_id_payment_tra_13da FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id) ON DELETE RESTRICT,
    CONSTRAINT uq_milestone_fundings_funding_journal_id UNIQUE (funding_journal_id),
    CONSTRAINT uq_milestone_fundings_milestone_id UNIQUE (milestone_id),
    CONSTRAINT uq_milestone_fundings_payment_transaction_id UNIQUE (payment_transaction_id)
);

CREATE INDEX ix_milestone_fundings_funding_journal_id ON milestone_fundings (funding_journal_id);

CREATE INDEX ix_milestone_fundings_milestone_id ON milestone_fundings (milestone_id);

CREATE INDEX ix_milestone_fundings_payment_transaction_id ON milestone_fundings (payment_transaction_id);

CREATE TABLE payment_review_cases (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    payment_transaction_id BIGINT UNSIGNED NOT NULL,
    reason VARCHAR(40) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'OPEN',
    assigned_to BIGINT UNSIGNED,
    resolution VARCHAR(40),
    note TEXT,
    resolved_by BIGINT UNSIGNED,
    resolved_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_payment_review_cases PRIMARY KEY (id),
    CONSTRAINT fk_payment_review_cases_assigned_to_users FOREIGN KEY(assigned_to) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_review_cases_payment_transaction_id_payment_t_b457 FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_review_cases_resolved_by_users FOREIGN KEY(resolved_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_payment_review_cases_payment_transaction_id UNIQUE (payment_transaction_id),
    CONSTRAINT ck_payment_review_cases_payment_review_cases_reason CHECK (reason IN ('UNMATCHED', 'UNDERPAID', 'OVERPAID', 'LATE', 'WRONG_ACCOUNT', 'DUPLICATE_PAYMENT')),
    CONSTRAINT ck_payment_review_cases_payment_review_cases_status CHECK (status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED')),
    CONSTRAINT ck_payment_review_cases_payment_review_cases_resolution CHECK (resolution IN ('ALLOCATE', 'RETURN', 'PARTIAL_RETURN'))
);

CREATE INDEX ix_payment_review_cases_assigned_to ON payment_review_cases (assigned_to);

CREATE INDEX ix_payment_review_cases_payment_transaction_id ON payment_review_cases (payment_transaction_id);

CREATE INDEX ix_payment_review_cases_resolved_by ON payment_review_cases (resolved_by);

CREATE INDEX ix_payment_review_cases_status_created_at ON payment_review_cases (status, created_at);

CREATE TABLE settlements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    milestone_id BIGINT UNSIGNED NOT NULL,
    sequence_no INTEGER NOT NULL,
    kind VARCHAR(40) NOT NULL,
    source VARCHAR(40) NOT NULL,
    source_review_id BIGINT UNSIGNED,
    source_cancellation_id BIGINT UNSIGNED,
    source_decision_id BIGINT UNSIGNED,
    amount BIGINT NOT NULL,
    freelancer_gross BIGINT NOT NULL,
    refund_amount BIGINT NOT NULL,
    fee_rate_bp SMALLINT UNSIGNED NOT NULL,
    fee_amount BIGINT NOT NULL,
    net_amount BIGINT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'PREPARED',
    request_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    requested_by BIGINT UNSIGNED,
    completed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_settlements PRIMARY KEY (id),
    CONSTRAINT ck_settlements_settlement_kind_amounts CHECK ((kind = 'RELEASE' AND refund_amount = 0 AND freelancer_gross > 0) OR (kind = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (kind = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)),
    CONSTRAINT ck_settlements_settlement_source CHECK ((source IN ('ACCEPTANCE','AUTO_ACCEPT') AND source_review_id IS NOT NULL AND source_cancellation_id IS NULL AND source_decision_id IS NULL) OR (source = 'CANCELLATION' AND source_review_id IS NULL AND source_cancellation_id IS NOT NULL AND source_decision_id IS NULL) OR (source = 'DISPUTE' AND source_review_id IS NULL AND source_cancellation_id IS NULL AND source_decision_id IS NOT NULL)),
    CONSTRAINT ck_settlements_amount_amount CHECK (amount > 0),
    CONSTRAINT ck_settlements_settlement_fee CHECK (fee_amount + net_amount = freelancer_gross),
    CONSTRAINT ck_settlements_fee_amount_amount CHECK (fee_amount >= 0),
    CONSTRAINT ck_settlements_fee_rate_bp_range CHECK (fee_rate_bp <= 10000),
    CONSTRAINT ck_settlements_fee_rate_bp_nonnegative CHECK (fee_rate_bp >= 0),
    CONSTRAINT ck_settlements_settlement_total CHECK (freelancer_gross + refund_amount = amount),
    CONSTRAINT ck_settlements_freelancer_gross_amount CHECK (freelancer_gross >= 0),
    CONSTRAINT ck_settlements_net_amount_amount CHECK (net_amount >= 0),
    CONSTRAINT ck_settlements_refund_amount_amount CHECK (refund_amount >= 0),
    CONSTRAINT ck_settlements_sequence_no_nonnegative CHECK (sequence_no > 0),
    CONSTRAINT fk_settlements_milestone_id_milestones FOREIGN KEY(milestone_id) REFERENCES milestones (id) ON DELETE RESTRICT,
    CONSTRAINT fk_settlements_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_settlements_source_cancellation_id_cancellation_agreements FOREIGN KEY(source_cancellation_id) REFERENCES cancellation_agreements (id) ON DELETE RESTRICT,
    CONSTRAINT fk_settlements_source_decision_id_dispute_decisions FOREIGN KEY(source_decision_id) REFERENCES dispute_decisions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_settlements_source_review_id_milestone_reviews FOREIGN KEY(source_review_id) REFERENCES milestone_reviews (id) ON DELETE RESTRICT,
    CONSTRAINT uq_settlements_milestone_id_sequence_no UNIQUE (milestone_id, sequence_no),
    CONSTRAINT uq_settlements_request_key UNIQUE (request_key),
    CONSTRAINT uq_settlements_source_cancellation_id UNIQUE (source_cancellation_id),
    CONSTRAINT uq_settlements_source_decision_id UNIQUE (source_decision_id),
    CONSTRAINT uq_settlements_source_review_id UNIQUE (source_review_id),
    CONSTRAINT ck_settlements_settlements_kind CHECK (kind IN ('RELEASE', 'REFUND', 'SPLIT')),
    CONSTRAINT ck_settlements_settlements_source CHECK (source IN ('ACCEPTANCE', 'AUTO_ACCEPT', 'CANCELLATION', 'DISPUTE')),
    CONSTRAINT ck_settlements_settlements_status CHECK (status IN ('PREPARED', 'PROCESSING', 'PARTIALLY_SUCCEEDED', 'SUCCEEDED', 'FAILED', 'CANCELLED'))
);

CREATE INDEX ix_settlements_requested_by ON settlements (requested_by);

CREATE INDEX ix_settlements_source_cancellation_id ON settlements (source_cancellation_id);

CREATE INDEX ix_settlements_source_decision_id ON settlements (source_decision_id);

CREATE INDEX ix_settlements_source_review_id ON settlements (source_review_id);

CREATE TABLE money_transfers (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    settlement_id BIGINT UNSIGNED,
    payment_transaction_id BIGINT UNSIGNED,
    purpose VARCHAR(40) NOT NULL,
    recipient_user_id BIGINT UNSIGNED NOT NULL,
    destination_id BIGINT UNSIGNED NOT NULL,
    destination_snapshot JSON NOT NULL,
    amount BIGINT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'READY',
    idempotency_key VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    provider_reference_id VARCHAR(191) COLLATE utf8mb4_bin NOT NULL,
    payos_payout_id VARCHAR(191) COLLATE utf8mb4_bin,
    payos_transaction_id VARCHAR(191) COLLATE utf8mb4_bin,
    provider_approval_state VARCHAR(40),
    provider_transaction_state VARCHAR(40),
    obligation_journal_id BIGINT UNSIGNED,
    disbursement_journal_id BIGINT UNSIGNED,
    provider_fee_amount BIGINT,
    fee_journal_id BIGINT UNSIGNED,
    succeeded_at DATETIME(6),
    reserved_at DATETIME(6) NOT NULL,
    reservation_released_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_money_transfers PRIMARY KEY (id),
    CONSTRAINT ck_money_transfers_transfer_source CHECK ((purpose IN ('RELEASE','REFUND') AND settlement_id IS NOT NULL AND payment_transaction_id IS NULL) OR (purpose = 'UNALLOCATED_REFUND' AND settlement_id IS NULL AND payment_transaction_id IS NOT NULL)),
    CONSTRAINT ck_money_transfers_amount_amount CHECK (amount > 0),
    CONSTRAINT ck_money_transfers_provider_fee_amount_amount CHECK (provider_fee_amount >= 0),
    CONSTRAINT fk_money_transfers_destination_id_bank_destinations FOREIGN KEY(destination_id) REFERENCES bank_destinations (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_disbursement_journal_id_ledger_journals FOREIGN KEY(disbursement_journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_fee_journal_id_ledger_journals FOREIGN KEY(fee_journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_obligation_journal_id_ledger_journals FOREIGN KEY(obligation_journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_payment_transaction_id_payment_transactions FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_recipient_user_id_users FOREIGN KEY(recipient_user_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_money_transfers_settlement_id_settlements FOREIGN KEY(settlement_id) REFERENCES settlements (id) ON DELETE RESTRICT,
    CONSTRAINT uq_money_transfers_disbursement_journal_id UNIQUE (disbursement_journal_id),
    CONSTRAINT uq_money_transfers_fee_journal_id UNIQUE (fee_journal_id),
    CONSTRAINT uq_money_transfers_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT uq_money_transfers_obligation_journal_id UNIQUE (obligation_journal_id),
    CONSTRAINT uq_money_transfers_payos_payout_id UNIQUE (payos_payout_id),
    CONSTRAINT uq_money_transfers_payos_transaction_id UNIQUE (payos_transaction_id),
    CONSTRAINT uq_money_transfers_provider_reference_id UNIQUE (provider_reference_id),
    CONSTRAINT uq_money_transfers_settlement_id_purpose UNIQUE (settlement_id, purpose),
    CONSTRAINT ck_money_transfers_money_transfers_purpose CHECK (purpose IN ('RELEASE', 'REFUND', 'UNALLOCATED_REFUND')),
    CONSTRAINT ck_money_transfers_money_transfers_status CHECK (status IN ('READY', 'PROCESSING', 'UNKNOWN', 'SUCCEEDED', 'FAILED', 'CANCELLED'))
);

CREATE INDEX ix_money_transfers_destination_id ON money_transfers (destination_id);

CREATE INDEX ix_money_transfers_disbursement_journal_id ON money_transfers (disbursement_journal_id);

CREATE INDEX ix_money_transfers_fee_journal_id ON money_transfers (fee_journal_id);

CREATE INDEX ix_money_transfers_obligation_journal_id ON money_transfers (obligation_journal_id);

CREATE INDEX ix_money_transfers_payment_transaction_id ON money_transfers (payment_transaction_id);

CREATE INDEX ix_money_transfers_recipient_user_id ON money_transfers (recipient_user_id);

CREATE TABLE daily_limit_reservations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    bucket_id BIGINT UNSIGNED NOT NULL,
    payment_order_id BIGINT UNSIGNED,
    money_transfer_id BIGINT UNSIGNED,
    amount BIGINT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'RESERVED',
    consumed_at DATETIME(6),
    released_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_daily_limit_reservations PRIMARY KEY (id),
    CONSTRAINT ck_daily_limit_reservations_limit_source CHECK ((payment_order_id IS NOT NULL AND money_transfer_id IS NULL) OR (payment_order_id IS NULL AND money_transfer_id IS NOT NULL)),
    CONSTRAINT ck_daily_limit_reservations_amount_amount CHECK (amount > 0),
    CONSTRAINT fk_daily_limit_reservations_bucket_id_daily_limit_buckets FOREIGN KEY(bucket_id) REFERENCES daily_limit_buckets (id) ON DELETE RESTRICT,
    CONSTRAINT fk_daily_limit_reservations_money_transfer_id_money_transfers FOREIGN KEY(money_transfer_id) REFERENCES money_transfers (id) ON DELETE RESTRICT,
    CONSTRAINT fk_daily_limit_reservations_payment_order_id_payment_orders FOREIGN KEY(payment_order_id) REFERENCES payment_orders (id) ON DELETE RESTRICT,
    CONSTRAINT uq_daily_limit_reservations_bucket_id_money_transfer_id UNIQUE (bucket_id, money_transfer_id),
    CONSTRAINT uq_daily_limit_reservations_bucket_id_payment_order_id UNIQUE (bucket_id, payment_order_id),
    CONSTRAINT ck_daily_limit_reservations_daily_limit_reservations_status CHECK (status IN ('RESERVED', 'CONSUMED', 'RELEASED'))
);

CREATE INDEX ix_daily_limit_reservations_money_transfer_id ON daily_limit_reservations (money_transfer_id);

CREATE INDEX ix_daily_limit_reservations_payment_order_id ON daily_limit_reservations (payment_order_id);

CREATE TABLE transfer_attempts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    transfer_id BIGINT UNSIGNED NOT NULL,
    attempt_no INTEGER NOT NULL,
    operation VARCHAR(40) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'STARTED',
    request_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    provider_response_json JSON,
    error_code VARCHAR(100),
    started_at DATETIME(6) NOT NULL,
    finished_at DATETIME(6),
    next_check_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT pk_transfer_attempts PRIMARY KEY (id),
    CONSTRAINT ck_transfer_attempts_attempt_no_nonnegative CHECK (attempt_no > 0),
    CONSTRAINT fk_transfer_attempts_transfer_id_money_transfers FOREIGN KEY(transfer_id) REFERENCES money_transfers (id) ON DELETE RESTRICT,
    CONSTRAINT uq_transfer_attempts_transfer_id_attempt_no UNIQUE (transfer_id, attempt_no),
    CONSTRAINT ck_transfer_attempts_transfer_attempts_operation CHECK (operation IN ('CREATE', 'QUERY')),
    CONSTRAINT ck_transfer_attempts_transfer_attempts_status CHECK (status IN ('STARTED', 'CONFIRMED_SUCCESS', 'CONFIRMED_FAILURE', 'UNKNOWN'))
);

ALTER TABLE companies ADD COLUMN legal_name VARCHAR(255);

ALTER TABLE companies ADD COLUMN representative_name VARCHAR(255);

ALTER TABLE companies ADD COLUMN representative_position VARCHAR(100);

ALTER TABLE companies ADD COLUMN is_legal_representative BOOL;

ALTER TABLE companies ADD COLUMN authorization_file_id BIGINT UNSIGNED;

ALTER TABLE companies ADD COLUMN business_status VARCHAR(40) NOT NULL DEFAULT 'UNVERIFIED';

ALTER TABLE companies ADD CONSTRAINT ck_companies_companies_business_status CHECK (business_status IN ('UNVERIFIED', 'PENDING_VERIFICATION', 'NEEDS_REVISION', 'VERIFIED', 'REJECTED', 'REVOKED'));

ALTER TABLE companies ADD COLUMN business_verified_at DATETIME(6);

ALTER TABLE companies ADD COLUMN business_verified_by BIGINT UNSIGNED;

ALTER TABLE companies ADD COLUMN operation_status VARCHAR(40) NOT NULL DEFAULT 'ENABLED';

ALTER TABLE companies ADD CONSTRAINT ck_companies_companies_operation_status CHECK (operation_status IN ('ENABLED', 'SUSPENDED'));

ALTER TABLE companies ADD COLUMN suspension_reason TEXT;

ALTER TABLE companies ADD COLUMN suspended_at DATETIME(6);

ALTER TABLE companies ADD COLUMN suspended_by BIGINT UNSIGNED;

CREATE INDEX ix_companies_business_status_created_at ON companies (business_status, created_at);

ALTER TABLE companies ADD CONSTRAINT fk_companies_suspended_by_users FOREIGN KEY(suspended_by) REFERENCES users (id) ON DELETE RESTRICT;

ALTER TABLE companies ADD CONSTRAINT fk_companies_authorization_file_id_stored_files FOREIGN KEY(authorization_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT;

ALTER TABLE companies ADD CONSTRAINT fk_companies_business_verified_by_users FOREIGN KEY(business_verified_by) REFERENCES users (id) ON DELETE RESTRICT;

ALTER TABLE company_documents ADD COLUMN stored_file_id BIGINT UNSIGNED;

ALTER TABLE company_documents ADD COLUMN uploaded_by BIGINT UNSIGNED;

ALTER TABLE company_documents ADD CONSTRAINT fk_company_documents_uploaded_by_users FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE RESTRICT;

ALTER TABLE company_documents ADD CONSTRAINT fk_company_documents_stored_file_id_stored_files FOREIGN KEY(stored_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT;

ALTER TABLE users ADD COLUMN phone VARCHAR(20);

ALTER TABLE users ADD COLUMN email_verified_at DATETIME(6);

ALTER TABLE users ADD COLUMN phone_verified_at DATETIME(6);

ALTER TABLE users MODIFY `role` ENUM('STUDENT','COMPANY','ADMIN','CLIENT') NOT NULL;

ALTER TABLE freelance_contracts ADD CONSTRAINT fk_fc_effective_version FOREIGN KEY(id, effective_version_id) REFERENCES contract_versions (contract_id, id) ON DELETE RESTRICT;

ALTER TABLE milestones ADD CONSTRAINT fk_ms_effective_terms FOREIGN KEY(id, effective_terms_id) REFERENCES contract_milestone_terms (milestone_id, id) ON DELETE RESTRICT;

UPDATE companies SET legal_name = name WHERE legal_name IS NULL;

CREATE TRIGGER trg_ledger_journals_update_blocked BEFORE UPDATE ON ledger_journals FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

CREATE TRIGGER trg_ledger_journals_delete_blocked BEFORE DELETE ON ledger_journals FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

CREATE TRIGGER trg_ledger_postings_update_blocked BEFORE UPDATE ON ledger_postings FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

CREATE TRIGGER trg_ledger_postings_delete_blocked BEFORE DELETE ON ledger_postings FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

CREATE TRIGGER trg_audit_logs_update_blocked BEFORE UPDATE ON audit_logs FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

CREATE TRIGGER trg_audit_logs_delete_blocked BEFORE DELETE ON audit_logs FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table';

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

-- Running upgrade 0002 -> 0003

CREATE TABLE freelancer_policies (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    policy_key VARCHAR(50) COLLATE utf8mb4_bin NOT NULL,
    revision INTEGER NOT NULL,
    values_json JSON NOT NULL,
    updated_by BIGINT UNSIGNED,
    updated_at DATETIME(6) NOT NULL DEFAULT (now()),
    CONSTRAINT pk_freelancer_policies PRIMARY KEY (id),
    CONSTRAINT ck_freelancer_policies_revision_positive CHECK (revision > 0),
    CONSTRAINT uq_freelancer_policies_policy_key UNIQUE (policy_key),
    CONSTRAINT fk_freelancer_policies_updated_by_users FOREIGN KEY(updated_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE otp_rate_buckets (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scope_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    window_started_at DATETIME(6) NOT NULL,
    count INTEGER NOT NULL,
    CONSTRAINT pk_otp_rate_buckets PRIMARY KEY (id),
    CONSTRAINT ck_otp_rate_buckets_count_nonnegative CHECK (count >= 0),
    CONSTRAINT uq_otp_rate_buckets_scope_hash UNIQUE (scope_hash)
);

CREATE TABLE dispute_withdrawals (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dispute_id BIGINT UNSIGNED NOT NULL,
    requested_by BIGINT UNSIGNED NOT NULL,
    reason TEXT NOT NULL,
    terms_hash VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
    confirmed_by BIGINT UNSIGNED,
    created_at DATETIME(6) NOT NULL,
    confirmed_at DATETIME(6),
    CONSTRAINT pk_dispute_withdrawals PRIMARY KEY (id),
    CONSTRAINT ck_dispute_withdrawals_distinct_confirmers CHECK (confirmed_by IS NULL OR confirmed_by <> requested_by),
    CONSTRAINT uq_dispute_withdrawals_dispute_id UNIQUE (dispute_id),
    CONSTRAINT fk_dispute_withdrawals_dispute_id_disputes FOREIGN KEY(dispute_id) REFERENCES disputes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_withdrawals_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_dispute_withdrawals_confirmed_by_users FOREIGN KEY(confirmed_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE project_expansions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    requested_by BIGINT UNSIGNED NOT NULL,
    request_key VARCHAR(128) COLLATE utf8mb4_bin NOT NULL,
    budget_amount BIGINT NOT NULL,
    max_students INTEGER NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    reviewed_by BIGINT UNSIGNED,
    review_reason TEXT,
    reviewed_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT (now()),
    CONSTRAINT pk_project_expansions PRIMARY KEY (id),
    CONSTRAINT uq_project_expansions_project_id_request_key UNIQUE (project_id, request_key),
    CONSTRAINT ck_project_expansions_positive_ceilings CHECK (budget_amount > 0 AND max_students > 0),
    CONSTRAINT ck_project_expansions_status_values CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    CONSTRAINT fk_project_expansions_project_id_freelance_projects FOREIGN KEY(project_id) REFERENCES freelance_projects (id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_expansions_requested_by_users FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_expansions_reviewed_by_users FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_project_expansions_project_id ON project_expansions (project_id);

CREATE INDEX ix_project_expansions_requested_by ON project_expansions (requested_by);

CREATE INDEX ix_project_expansions_reviewed_by ON project_expansions (reviewed_by);

CREATE INDEX ix_freelancer_policies_updated_by ON freelancer_policies (updated_by);

CREATE INDEX ix_dispute_withdrawals_requested_by ON dispute_withdrawals (requested_by);

CREATE INDEX ix_dispute_withdrawals_confirmed_by ON dispute_withdrawals (confirmed_by);

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

-- Running upgrade 0003 -> 0004

CREATE TABLE finance_counters (
    name VARCHAR(50) NOT NULL,
    next_value BIGINT NOT NULL,
    CONSTRAINT pk_finance_counters PRIMARY KEY (name)
);

INSERT INTO finance_counters (name, next_value) VALUES ('writer', 1000000000);

UPDATE finance_counters SET next_value = (SELECT CASE WHEN MAX(order_code) >= 1000000000 THEN MAX(order_code) + 1 ELSE 1000000000 END FROM payment_orders) WHERE name='writer';

CREATE TABLE treasury_entries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    external_reference VARCHAR(150) COLLATE utf8mb4_bin NOT NULL,
    kind VARCHAR(30) NOT NULL,
    amount BIGINT NOT NULL,
    evidence_file_id BIGINT UNSIGNED NOT NULL,
    proposed_by BIGINT UNSIGNED NOT NULL,
    approved_by BIGINT UNSIGNED,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PROPOSED',
    journal_id BIGINT UNSIGNED,
    created_at DATETIME(6) NOT NULL DEFAULT (now()),
    posted_at DATETIME(6),
    CONSTRAINT pk_treasury_entries PRIMARY KEY (id),
    CONSTRAINT ck_treasury_entries_positive_amount CHECK (amount > 0),
    CONSTRAINT ck_treasury_entries_valid_kind CHECK (kind IN ('TRANSFER_TO_PAYOUT','EQUITY_BANK','EQUITY_PAYOUT','FEE_BANK','FEE_PAYOUT')),
    CONSTRAINT ck_treasury_entries_valid_status CHECK (status IN ('PROPOSED','POSTED','REJECTED')),
    CONSTRAINT ck_treasury_entries_distinct_approvers CHECK (approved_by IS NULL OR approved_by <> proposed_by),
    CONSTRAINT uq_treasury_entries_external_reference UNIQUE (external_reference),
    CONSTRAINT fk_treasury_entries_evidence_file_id_stored_files FOREIGN KEY(evidence_file_id) REFERENCES stored_files (id) ON DELETE RESTRICT,
    CONSTRAINT fk_treasury_entries_proposed_by_users FOREIGN KEY(proposed_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_treasury_entries_approved_by_users FOREIGN KEY(approved_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT uq_treasury_entries_journal_id UNIQUE (journal_id),
    CONSTRAINT fk_treasury_entries_journal_id_ledger_journals FOREIGN KEY(journal_id) REFERENCES ledger_journals (id) ON DELETE RESTRICT
);

CREATE INDEX ix_treasury_entries_evidence_file_id ON treasury_entries (evidence_file_id);

CREATE INDEX ix_treasury_entries_proposed_by ON treasury_entries (proposed_by);

CREATE INDEX ix_treasury_entries_approved_by ON treasury_entries (approved_by);

UPDATE alembic_version SET version_num='0004' WHERE alembic_version.version_num = '0003';
