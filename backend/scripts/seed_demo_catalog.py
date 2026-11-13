"""Compatibility entry point for the complete thesis recruitment dataset.

Run from backend: python -m scripts.seed_demo_catalog
"""
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Job

JOB_TYPES = [
    ("INTERN", "Thực tập sinh"), ("FRESHER", "Fresher / Mới tốt nghiệp"),
    ("PART_TIME", "Bán thời gian"), ("FULL_TIME", "Toàn thời gian"),
    ("CONTRACT", "Hợp đồng có thời hạn"), ("SEASONAL", "Thời vụ"),
    ("COLLABORATOR", "Cộng tác viên"), ("APPRENTICE", "Học việc"),
]

# Practical recruitment taxonomy; administrators can add emerging specialties.
INDUSTRIES = [
    "Công nghệ thông tin - Phần mềm", "Phần cứng - Mạng - Viễn thông",
    "Dữ liệu - Trí tuệ nhân tạo", "An toàn thông tin", "Game - Giải trí số",
    "Tài chính - Ngân hàng", "Kế toán - Kiểm toán", "Bảo hiểm", "Chứng khoán - Đầu tư",
    "Marketing - Quảng cáo", "Truyền thông - Quan hệ công chúng", "Nội dung - Báo chí - Xuất bản",
    "Thiết kế đồ họa - Mỹ thuật", "Thiết kế sản phẩm - UI/UX", "Kinh doanh - Bán hàng",
    "Thương mại điện tử", "Bán lẻ - Phân phối", "Dịch vụ khách hàng", "Hành chính - Văn phòng",
    "Nhân sự - Tuyển dụng", "Pháp lý - Tuân thủ", "Biên phiên dịch", "Giáo dục - Đào tạo",
    "Nghiên cứu - Khoa học", "Y tế - Chăm sóc sức khỏe", "Dược phẩm - Công nghệ sinh học",
    "Nha khoa", "Tâm lý - Công tác xã hội", "Xây dựng - Hạ tầng", "Kiến trúc - Nội thất",
    "Bất động sản", "Cơ khí - Chế tạo", "Điện - Điện tử - Tự động hóa", "Ô tô - Xe máy",
    "Sản xuất - Vận hành", "Quản lý chất lượng", "An toàn lao động", "Dầu khí - Hóa chất",
    "Năng lượng - Năng lượng tái tạo", "Môi trường - Xử lý chất thải", "Khai khoáng - Địa chất",
    "Nông nghiệp - Lâm nghiệp", "Thủy sản - Chăn nuôi - Thú y", "Công nghệ thực phẩm",
    "Dệt may - Da giày", "Thời trang - Trang sức", "Mỹ phẩm - Làm đẹp", "In ấn - Bao bì",
    "Logistics - Chuỗi cung ứng", "Vận tải - Giao nhận", "Xuất nhập khẩu", "Thu mua",
    "Du lịch - Lữ hành", "Khách sạn - Khu nghỉ dưỡng", "Nhà hàng - Dịch vụ ăn uống",
    "Hàng không", "Hàng hải", "Sự kiện - Giải trí", "Điện ảnh - Âm nhạc - Nhiếp ảnh",
    "Thể thao - Thể hình", "An ninh - Bảo vệ", "Dịch vụ gia đình - Chăm sóc cá nhân",
    "Tư vấn - Chiến lược", "Quản lý dự án", "Tổ chức phi lợi nhuận", "Hành chính công",
    "Thống kê - Khảo sát thị trường", "Bảo trì - Sửa chữa", "Lao động phổ thông", "Ngành nghề khác",
]

VACANCIES = [
    ("Thực tập sinh lập trình Python", "Công nghệ thông tin - Phần mềm", "INTERN", "Phát triển API và kiểm thử tính năng dưới sự hướng dẫn của mentor."),
    ("Fresher React / TypeScript", "Công nghệ thông tin - Phần mềm", "FRESHER", "Xây dựng giao diện web responsive, phối hợp cùng nhóm thiết kế và backend."),
    ("Thực tập sinh phân tích dữ liệu", "Dữ liệu - Trí tuệ nhân tạo", "INTERN", "Làm sạch dữ liệu, xây dựng báo cáo và phân tích chỉ số vận hành."),
    ("Cộng tác viên viết nội dung", "Nội dung - Báo chí - Xuất bản", "COLLABORATOR", "Nghiên cứu chủ đề, viết bài và biên tập nội dung theo kế hoạch truyền thông."),
    ("Thiết kế đồ họa bán thời gian", "Thiết kế đồ họa - Mỹ thuật", "PART_TIME", "Thiết kế ấn phẩm truyền thông số và bộ nhận diện cho các chiến dịch."),
    ("Thực tập sinh kế toán", "Kế toán - Kiểm toán", "INTERN", "Hỗ trợ sắp xếp chứng từ, đối chiếu dữ liệu và lập báo cáo theo hướng dẫn."),
    ("Nhân viên chăm sóc khách hàng", "Dịch vụ khách hàng", "FULL_TIME", "Tiếp nhận yêu cầu và hỗ trợ khách hàng qua các kênh dịch vụ."),
    ("Trợ giảng tiếng Anh", "Giáo dục - Đào tạo", "PART_TIME", "Hỗ trợ giảng viên chuẩn bị tài liệu và theo dõi tiến độ học viên."),
    ("Thực tập sinh tuyển dụng", "Nhân sự - Tuyển dụng", "INTERN", "Hỗ trợ đăng tin, sàng lọc hồ sơ và sắp xếp lịch phỏng vấn."),
    ("Thực tập sinh logistics", "Logistics - Chuỗi cung ứng", "INTERN", "Theo dõi đơn hàng, chuẩn bị chứng từ và cập nhật tiến độ giao nhận."),
    ("Cộng tác viên biên dịch", "Biên phiên dịch", "COLLABORATOR", "Dịch và hiệu đính tài liệu tiếng Anh theo bộ thuật ngữ được cung cấp."),
    ("Thực tập sinh kiểm thử phần mềm", "Công nghệ thông tin - Phần mềm", "INTERN", "Viết test case, thực hiện kiểm thử và báo cáo lỗi cho nhóm phát triển."),
]


def seed(db):
    # Keep the old command compatible without reintroducing incomplete DEMO rows.
    from scripts.prepare_defense_jobs import prepare
    before = db.scalar(select(func.count(Job.id)))
    prepare(db)
    return db.scalar(select(func.count(Job.id))) - before


if __name__ == "__main__":
    with SessionLocal() as db:
        count = seed(db)
    print(f"Recruitment data prepared: {len(JOB_TYPES)} job types, {len(INDUSTRIES)} industries, {count} new jobs.")
