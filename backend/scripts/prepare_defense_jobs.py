"""Complete recruitment scenarios for thesis defense; preserve existing job IDs.

Run: python -m scripts.prepare_defense_jobs
Company profiles added here are authored scenarios, not verified external vacancies.
"""
from datetime import date, timedelta

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.enums import JobStatus, UserRole, VerificationStatus
from app.models import Application, Company, Industry, Job, JobSkill, JobType, Skill, User
from app.utils.datetime_utils import utcnow
from scripts.seed import get_or_create_user
from scripts.seed_demo_catalog import INDUSTRIES, JOB_TYPES

EMPLOYERS = {
    "tech": ("careers@techcorp.example", "Công ty Cổ phần Công nghệ TechCorp", "SC-TECH-001", "Công nghệ thông tin - Phần mềm", "Cầu Giấy, Hà Nội", "Nguyễn Minh Anh", "Phát triển phần mềm quản trị doanh nghiệp, nền tảng thương mại điện tử và giải pháp dữ liệu. Đội ngũ kỹ thuật tổ chức theo nhóm sản phẩm, có mentor hướng dẫn sinh viên và nhân sự mới."),
    "media": ("careers@lamsang.example", "Công ty TNHH Truyền thông Lam Sáng", "SC-MEDIA-001", "Marketing - Quảng cáo", "Bình Thạnh, TP. Hồ Chí Minh", "Trần Hà Linh", "Cung cấp dịch vụ nội dung, thiết kế nhận diện và truyền thông số. Nhóm nội dung và thiết kế phối hợp theo từng chiến dịch, sử dụng quy trình brief, phản hồi và nghiệm thu rõ ràng."),
    "services": ("careers@ketnoiservices.example", "Công ty TNHH Dịch vụ Kết Nối", "SC-SERVICE-001", "Logistics - Chuỗi cung ứng", "Nam Từ Liêm, Hà Nội", "Lê Hoàng Phúc", "Cung cấp dịch vụ hỗ trợ vận hành cho doanh nghiệp thương mại: quản lý đơn hàng, chăm sóc khách hàng, phối hợp kho vận và dịch vụ hành chính. Có chương trình hướng dẫn nghiệp vụ cho sinh viên năm cuối."),
    "education": ("careers@minhtriedu.example", "Công ty TNHH Giáo dục Minh Tri", "SC-EDU-001", "Giáo dục - Đào tạo", "Thanh Xuân, Hà Nội", "Phạm Thu Hương", "Phát triển chương trình học tiếng Anh giao tiếp và tài liệu học tập song ngữ. Bộ phận học thuật phối hợp cùng trợ giảng để theo dõi tiến độ học viên và chuẩn hóa chất lượng tài liệu."),
}

# title, employer, industry, type, salary, headcount, mode, experience,
# required skills, preferred skills, responsibilities, specific requirements
POSITIONS = [
    ("Thực tập sinh lập trình Python", "tech", "Công nghệ thông tin - Phần mềm", "INTERN", (3000000, 5000000), 3, "HYBRID", 0,
     ["Python", "SQL"], ["FastAPI", "Git"],
     ["Phát triển API cho phân hệ quản lý đơn hàng bằng Python và FastAPI.", "Viết truy vấn SQL, kiểm tra dữ liệu đầu vào và xử lý lỗi theo hướng dẫn của mentor.", "Viết kiểm thử cho tính năng được giao, tham gia code review và cập nhật tài liệu API.", "Báo cáo tiến độ hằng tuần và phối hợp với nhóm frontend để tích hợp chức năng."],
     ["Sinh viên năm 3–4 hoặc mới tốt nghiệp ngành CNTT, có thể làm tối thiểu 6 buổi/tuần trong 3 tháng.", "Nắm cấu trúc dữ liệu cơ bản, lập trình hướng đối tượng Python và truy vấn SELECT/JOIN.", "Có bài tập hoặc dự án cá nhân sử dụng Python; gửi liên kết mã nguồn trong CV nếu có."]),
    ("Fresher React / TypeScript", "tech", "Công nghệ thông tin - Phần mềm", "FRESHER", (9000000, 14000000), 2, "HYBRID", 0,
     ["React", "TypeScript", "HTML", "CSS"], ["Git", "REST API"],
     ["Xây dựng giao diện dashboard và các biểu mẫu nghiệp vụ từ thiết kế Figma.", "Tích hợp REST API, xử lý trạng thái tải, lỗi và xác thực dữ liệu trên giao diện.", "Tối ưu bố cục trên desktop/mobile và hỗ trợ kiểm tra khả năng sử dụng bàn phím.", "Viết kiểm thử cho component quan trọng và tham gia rà soát mã nguồn trong nhóm."],
     ["Mới tốt nghiệp hoặc hoàn thành chương trình học, có thể làm toàn thời gian.", "Hiểu React hooks, TypeScript, HTML ngữ nghĩa và CSS responsive.", "Có ít nhất một ứng dụng React hoàn chỉnh để trình bày trong buổi phỏng vấn."]),
    ("Thực tập sinh phân tích dữ liệu", "tech", "Dữ liệu - Trí tuệ nhân tạo", "INTERN", (3000000, 5000000), 2, "ONSITE", 0,
     ["SQL", "Excel"], ["Python", "Power BI"],
     ["Tổng hợp dữ liệu bán hàng, kiểm tra giá trị thiếu và chuẩn hóa các trường dữ liệu.", "Viết truy vấn SQL cho các chỉ số doanh thu, tỷ lệ chuyển đổi và hành vi khách hàng.", "Xây dựng báo cáo Excel/Power BI theo mẫu và giải thích kết quả cho người phụ trách.", "Lưu tài liệu mô tả nguồn dữ liệu, công thức và phạm vi thống kê."],
     ["Sinh viên ngành phân tích dữ liệu, hệ thống thông tin, thống kê hoặc kinh tế định lượng.", "Sử dụng được JOIN, GROUP BY và các hàm tổng hợp SQL; nắm PivotTable và hàm tra cứu Excel.", "Cẩn thận với số liệu, có khả năng trình bày nhận xét dựa trên dữ liệu."]),
    ("Cộng tác viên viết nội dung", "media", "Nội dung - Báo chí - Xuất bản", "COLLABORATOR", (3000000, 5000000), 3, "REMOTE", 0,
     ["Viết nội dung", "Tiếng Việt"], ["SEO", "Canva"],
     ["Nghiên cứu sản phẩm và khách hàng mục tiêu dựa trên brief của quản lý nội dung.", "Viết 8–12 bài/tháng cho website và mạng xã hội, bảo đảm nội dung nguyên bản.", "Biên tập tiêu đề, cấu trúc bài và lời kêu gọi hành động phù hợp từng kênh.", "Tiếp nhận tối đa hai vòng góp ý cho mỗi bài và cập nhật tiến độ trên bảng công việc."],
     ["Diễn đạt tiếng Việt rõ ràng, đúng chính tả và có khả năng tự kiểm chứng thông tin.", "Gửi 2–3 bài viết đã thực hiện hoặc portfolio kèm CV.", "Có thể dành tối thiểu 15 giờ/tuần và tham gia họp trực tuyến một lần mỗi tuần."]),
    ("Thiết kế đồ họa bán thời gian", "media", "Thiết kế đồ họa - Mỹ thuật", "PART_TIME", (4000000, 6000000), 2, "HYBRID", 0,
     ["Thiết kế đồ họa", "Figma"], ["Adobe Photoshop", "Adobe Illustrator"],
     ["Thiết kế banner, ảnh mạng xã hội và tài liệu giới thiệu sản phẩm theo bộ nhận diện.", "Triển khai concept từ brief, trình bày phương án và chỉnh sửa theo phản hồi đã thống nhất.", "Chuẩn bị file xuất đúng kích thước, định dạng và lưu trữ file nguồn có tổ chức.", "Phối hợp với người viết nội dung để bảo đảm thông điệp và thiết kế nhất quán."],
     ["Có portfolio tối thiểu 5 sản phẩm thể hiện bố cục, màu sắc và typography.", "Sử dụng Figma và ít nhất một công cụ xử lý đồ họa; hiểu yêu cầu bản quyền hình ảnh.", "Làm tối thiểu 5 buổi/tuần, trong đó có 2 buổi làm việc tại văn phòng."]),
    ("Thực tập sinh kế toán", "services", "Kế toán - Kiểm toán", "INTERN", (2500000, 4000000), 2, "ONSITE", 0,
     ["Kế toán cơ bản", "Excel"], ["MISA", "Quản lý chứng từ"],
     ["Phân loại và sắp xếp hóa đơn, chứng từ thu chi theo hướng dẫn của kế toán phụ trách.", "Nhập dữ liệu vào bảng theo dõi, đối chiếu số tiền và hỗ trợ rà soát công nợ.", "Chuẩn bị danh sách chứng từ còn thiếu và theo dõi việc bổ sung từ các bộ phận.", "Hỗ trợ lập báo cáo nội bộ; không tự phê duyệt thanh toán hoặc ký chứng từ."],
     ["Sinh viên năm cuối chuyên ngành kế toán, kiểm toán hoặc tài chính.", "Nắm nguyên lý kế toán và sử dụng được SUMIF, tra cứu dữ liệu, PivotTable trong Excel.", "Có thể làm tối thiểu 6 buổi/tuần, bảo mật thông tin tài chính và kiểm tra số liệu cẩn thận."]),
    ("Nhân viên chăm sóc khách hàng", "services", "Dịch vụ khách hàng", "FULL_TIME", (7000000, 10000000), 4, "ONSITE", 0,
     ["Giao tiếp", "Chăm sóc khách hàng"], ["Excel", "CRM"],
     ["Tiếp nhận yêu cầu qua email, chat và điện thoại theo quy trình dịch vụ khách hàng.", "Tra cứu tình trạng đơn hàng, giải thích chính sách và phối hợp xử lý phản ánh.", "Ghi nhận đầy đủ lịch sử trao đổi trong hệ thống CRM và theo dõi đến khi yêu cầu đóng.", "Tổng hợp các vấn đề lặp lại để đề xuất cải thiện trải nghiệm khách hàng."],
     ["Giao tiếp lịch sự, có khả năng lắng nghe và diễn đạt tình huống rõ ràng.", "Sử dụng thành thạo công cụ văn phòng và sẵn sàng học hệ thống CRM.", "Làm toàn thời gian theo lịch ca được thông báo trước; không yêu cầu kinh nghiệm."]),
    ("Trợ giảng tiếng Anh", "education", "Giáo dục - Đào tạo", "PART_TIME", (3500000, 5500000), 3, "ONSITE", 0,
     ["Tiếng Anh", "Giao tiếp"], ["Giảng dạy", "PowerPoint"],
     ["Chuẩn bị học liệu, kiểm tra thiết bị và hỗ trợ giảng viên tổ chức hoạt động lớp.", "Theo dõi điểm danh, thu bài tập và cập nhật tiến độ học viên sau mỗi buổi học.", "Hướng dẫn học viên thực hành theo giáo án, ghi nhận nội dung cần giảng viên hỗ trợ thêm.", "Phối hợp với bộ phận học thuật để tổng hợp phản hồi và cải thiện tài liệu."],
     ["Sử dụng tiếng Anh tương đương B2 trở lên; có thể chứng minh qua bài kiểm tra đầu vào.", "Ưu tiên sinh viên ngôn ngữ Anh hoặc sư phạm, kiên nhẫn và có trách nhiệm với lớp học.", "Đăng ký tối thiểu 4 ca/tuần vào buổi tối hoặc cuối tuần, gắn bó tối thiểu 4 tháng."]),
    ("Thực tập sinh tuyển dụng", "services", "Nhân sự - Tuyển dụng", "INTERN", (2500000, 4000000), 2, "HYBRID", 0,
     ["Giao tiếp", "Excel"], ["Tuyển dụng", "Viết nội dung"],
     ["Biên tập và đăng thông tin tuyển dụng theo yêu cầu đã được duyệt của từng bộ phận.", "Sàng lọc hồ sơ theo checklist, cập nhật trạng thái ứng viên và liên hệ đặt lịch phỏng vấn.", "Chuẩn bị danh sách phỏng vấn, gửi hướng dẫn và theo dõi phản hồi sau phỏng vấn.", "Báo cáo số lượng hồ sơ theo nguồn và bảo vệ dữ liệu cá nhân của ứng viên."],
     ["Sinh viên ngành quản trị nhân lực, quản trị kinh doanh hoặc ngành liên quan.", "Sử dụng được Excel, viết email rõ ràng và chủ động quản lý lịch làm việc.", "Có thể làm tối thiểu 6 buổi/tuần trong 3 tháng; không yêu cầu kinh nghiệm tuyển dụng."]),
    ("Thực tập sinh logistics", "services", "Logistics - Chuỗi cung ứng", "INTERN", (3000000, 4500000), 2, "ONSITE", 0,
     ["Excel", "Logistics cơ bản"], ["Tiếng Anh", "Quản lý chứng từ"],
     ["Cập nhật trạng thái đơn giao nhận và đối chiếu thông tin trên hệ thống vận hành.", "Chuẩn bị danh sách chứng từ, hỗ trợ kiểm tra thông tin hàng hóa và lịch giao hàng.", "Phối hợp với kho, đối tác vận chuyển và bộ phận chăm sóc khách hàng khi có phát sinh.", "Tổng hợp báo cáo tiến độ và ghi nhận nguyên nhân chậm giao theo biểu mẫu."],
     ["Sinh viên năm cuối logistics, kinh doanh quốc tế hoặc quản trị chuỗi cung ứng.", "Nắm kiến thức cơ bản về giao nhận, sử dụng Excel để lọc và tổng hợp dữ liệu.", "Đọc hiểu email tiếng Anh cơ bản, có thể làm ít nhất 6 buổi/tuần."]),
    ("Cộng tác viên biên dịch", "education", "Biên phiên dịch", "COLLABORATOR", (4000000, 6500000), 2, "REMOTE", 0,
     ["Tiếng Anh", "Biên dịch"], ["Microsoft Word", "Hiệu đính"],
     ["Biên dịch tài liệu học tập và hướng dẫn sản phẩm từ tiếng Anh sang tiếng Việt.", "Sử dụng bảng thuật ngữ, giữ cấu trúc tài liệu và đánh dấu nội dung cần xác nhận.", "Tự kiểm tra chính tả, số liệu và tính nhất quán trước khi bàn giao file Word.", "Thực hiện hiệu đính theo phản hồi trong phạm vi công việc đã thống nhất."],
     ["Có năng lực đọc viết tiếng Anh tốt và diễn đạt tiếng Việt tự nhiên.", "Nộp một bản dịch khoảng 500 từ hoặc portfolio; có thể thực hiện bài kiểm tra ngắn.", "Cam kết lịch bàn giao từng tài liệu và bảo mật nội dung; không yêu cầu dịch công chứng."]),
    ("Thực tập sinh kiểm thử phần mềm", "tech", "Công nghệ thông tin - Phần mềm", "INTERN", (3000000, 5000000), 3, "HYBRID", 0,
     ["Kiểm thử phần mềm", "SQL"], ["Postman", "Git"],
     ["Đọc yêu cầu và viết test case cho các luồng tài khoản, đơn hàng và báo cáo.", "Thực hiện kiểm thử chức năng, ghi nhận bước tái hiện và bằng chứng lỗi rõ ràng.", "Kiểm tra API bằng Postman, đối chiếu dữ liệu SQL và phối hợp xác nhận lỗi đã sửa.", "Cập nhật kết quả kiểm thử, tham gia kiểm thử hồi quy trước mỗi lần phát hành."],
     ["Sinh viên CNTT hoặc đã học kiểm thử cơ bản, hiểu test case và quy trình báo lỗi.", "Sử dụng được truy vấn SQL cơ bản; tư duy logic và cẩn thận khi mô tả tình huống.", "Có thể làm tối thiểu 6 buổi/tuần và tham gia chương trình 3 tháng."]),
]


def prepare(db):
    for code, name in JOB_TYPES:
        if not db.scalar(select(JobType.id).where(JobType.code == code)):
            db.add(JobType(code=code, name=name))
    for name in INDUSTRIES:
        if not db.scalar(select(Industry.id).where(Industry.name == name)):
            db.add(Industry(name=name))
    db.flush()
    employers = {}
    for key, (email, name, tax_code, industry, address, contact, description) in EMPLOYERS.items():
        # Prefer the existing TechCorp account; do not modify its identity/profile.
        existing = db.scalar(select(Company).where(Company.name == name))
        if existing:
            employers[key] = existing
            continue
        legacy_company = db.scalar(select(Company).where(Company.tax_code == "DEMO-SC-001")) if key == "services" else None
        owner = db.get(User, legacy_company.user_id) if legacy_company else get_or_create_user(db, email, UserRole.COMPANY)
        if owner.role != UserRole.COMPANY:
            raise ValueError(f"Account role conflict: {email}")
        owner.email_verified_at = utcnow()
        if legacy_company:
            owner.email = email
        company = legacy_company or db.scalar(select(Company).where(Company.user_id == owner.id))
        if company is None:
            company = Company(user_id=owner.id, name=name, tax_code=tax_code)
            db.add(company)
        company.name = name
        company.industry_id = db.scalar(select(Industry.id).where(Industry.name == industry))
        company.address, company.contact_name = address, contact
        company.company_size = "51-200"
        company.description = description
        company.tech_stack = "Python, FastAPI, React, TypeScript, PostgreSQL" if key == "tech" else None
        company.benefits = "Đào tạo hội nhập, người hướng dẫn trực tiếp, phản hồi định kỳ và cơ hội phát triển theo năng lực."
        company.verification_status = VerificationStatus.APPROVED
        company.business_status, company.operation_status = "VERIFIED", "ENABLED"
        company.business_verified_at = utcnow()
        db.flush()
        employers[key] = company

    admin_id = db.scalar(select(User.id).where(User.role == UserRole.ADMIN).order_by(User.id))
    updated = 0
    for title, key, industry, job_type, salary, quantity, mode, months, required, preferred, duties, requirements in POSITIONS:
        company = employers[key]
        legacy = db.scalar(select(Job).join(Company).where(Job.title == "[DEMO] " + title, Company.tax_code == "DEMO-SC-001"))
        job = legacy or db.scalar(select(Job).where(Job.title == title, Job.company_id == company.id))
        if legacy and db.scalar(select(func.count(Application.id)).where(Application.job_id == legacy.id)):
            raise ValueError(f"Job {legacy.id} has applications: preserve its employer and review manually")
        new = job is None
        if new:
            job = Job(company_id=company.id, title=title, position=title, description="", job_type_id=1, deadline=date.today())
            db.add(job)
        schedule = (
            "Lịch làm việc: thỏa thuận lịch bàn giao và khối lượng hằng tháng; họp cập nhật trực tuyến mỗi tuần."
            if job_type == "COLLABORATOR" else
            "Lịch làm việc: đăng ký ca/buổi theo yêu cầu vị trí; thống nhất lịch với quản lý trước khi nhận việc."
            if job_type in ("PART_TIME", "INTERN") else
            "Lịch làm việc: thứ Hai đến thứ Sáu, 08:30–17:30, nghỉ trưa 12:00–13:00."
        )
        description = "\n".join([f"Đơn vị tuyển dụng: {company.name}", "", "Công việc chính:"] + [f"• {line}" for line in duties] + ["", schedule, "Nơi làm việc: " + ("Làm việc trực tuyến, phối hợp với văn phòng " if mode == "REMOTE" else "") + EMPLOYERS[key][4]])
        benefits = "\n".join([
            f"• {'Thu nhập theo khối lượng thỏa thuận' if job_type == 'COLLABORATOR' else 'Lương/phụ cấp theo tháng'}: {salary[0]:,}–{salary[1]:,} VND, thống nhất theo năng lực và lịch làm việc.",
            "• Có người hướng dẫn trực tiếp, mục tiêu công việc rõ ràng và đánh giá định kỳ.",
            "• Được cung cấp tài liệu, quyền truy cập công cụ và đào tạo cần thiết cho công việc.",
            "• Hỗ trợ xác nhận thực tập sau khi hoàn thành chương trình." if job_type == "INTERN" else "• Có cơ hội tiếp tục hợp tác hoặc phát triển vị trí sau khi đánh giá kết quả.",
            "• Không thu phí ứng tuyển; trao đổi điều kiện làm việc và chế độ trong buổi phỏng vấn.",
        ])
        changed = new or legacy is not None or job.description != description or job.requirements != "\n".join(f"• {r}" for r in requirements) or job.benefits != benefits
        job.company_id, job.title, job.position = company.id, title, title
        job.job_type_id = db.scalar(select(JobType.id).where(JobType.code == job_type))
        job.industry_id = db.scalar(select(Industry.id).where(Industry.name == industry))
        job.description, job.requirements, job.benefits = description, "\n".join(f"• {r}" for r in requirements), benefits
        job.salary_min, job.salary_max = salary
        job.is_salary_negotiable, job.quantity, job.work_mode = False, quantity, mode
        job.location = EMPLOYERS[key][4]
        job.min_gpa, job.min_experience_months = None, months
        if new or legacy:
            job.status = JobStatus.APPROVED
            job.deadline = date.today() + timedelta(days=45)
            job.approved_by, job.approved_at = admin_id, utcnow()
        if changed:
            job.parsed_json = job.parsed_at = job.content_hash = None
        db.flush()
        skill_ids = set()
        for name in required + preferred:
            skill = db.scalar(select(Skill).where(Skill.name == name))
            if skill is None:
                skill = Skill(name=name, category="Chuyên môn" if name in required else "Bổ trợ")
                db.add(skill)
                db.flush()
            skill_ids.add(skill.id)
            link = db.get(JobSkill, (job.id, skill.id))
            if link is None:
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, is_required=name in required))
            else:
                link.is_required = name in required
        for link in db.scalars(select(JobSkill).where(JobSkill.job_id == job.id)):
            if link.skill_id not in skill_ids:
                db.delete(link)
        updated += 1
    # Legacy marker is retained until all twelve original titles have been located.
    if employers["services"].tax_code == "DEMO-SC-001":
        employers["services"].tax_code = EMPLOYERS["services"][2]
    db.commit()
    return updated


if __name__ == "__main__":
    with SessionLocal() as session:
        count = prepare(session)
    print(f"Prepared {count} complete recruitment postings with employer accounts and skill requirements.")
