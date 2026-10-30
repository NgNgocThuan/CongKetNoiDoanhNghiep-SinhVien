# Hai trang gợi ý — bàn giao

## Vị trí và phạm vi

- Sinh viên: /student/recommended, menu **Gợi ý phù hợp**.
- Doanh nghiệp: /company/candidates, menu **Gợi ý ứng viên**.
- Có thể mở thẳng /company/candidates?job_id=<id>. Tin phải thuộc doanh nghiệp đang đăng nhập.
- Bộ chọn tin có phân trang riêng qua jobs_page; danh sách kết quả dùng page.
- Source: src/features/matching/. Route được nối tại app/feature-routes.ts.
- Không sửa backend hoặc thay thế các trang nghiệp vụ của thành viên khác.

Tham khảo hình thức từ bản Stitch do Thuận cung cấp: thẻ trắng, nhãn kỹ năng xanh/cam,
danh sách và bảng giải thích bên phải. Giữ layout/menu, font và tokens của khung hiện có.
Trên màn nhỏ, nút xem mức độ phù hợp mở dialog có hỗ trợ Escape.

## Hợp đồng API sử dụng

| Hành vi | API |
|---|---|
| Gợi ý việc cho sinh viên | GET /matching/jobs/recommended?page=&size=6 |
| Tin của công ty, chọn vị trí | GET /jobs/me?page=&size=20 |
| Tin tuyển dụng chi tiết khi người dùng bấm xem | GET /jobs/{id} |
| Tên doanh nghiệp công khai trên thẻ việc | GET /companies/{id} |
| Ứng viên cho đúng tin | GET /matching/jobs/{id}/candidates?page=&size=6 |
| Tên ngành được chia sẻ | GET /catalog/majors/{id} |
| Trạng thái việc đã lưu | GET /saved-jobs?page=&size=100, đọc các trang |
| Lưu/bỏ lưu | POST /saved-jobs/{job_id}, DELETE /saved-jobs/{job_id} |
| Chọn CV | GET /cvs/me, response là mảng |
| Ứng tuyển | POST /applications: job_id, cv_id, cover_letter tùy chọn |
| Mời ứng tuyển | POST /invitations: job_id, student_id, message tối đa 500 ký tự |

Tất cả đường dẫn trên là tương đối với /api/v1, đi qua HTTP/auth chung.
Request truy vấn có AbortSignal; matching có timeout 120 giây vì backend có thể tính
kết quả khi đọc. Không chạy POST /matching/recompute từ hai trang này vì chỉ ADMIN có quyền.

## Quy tắc dữ liệu

- Không tải gợi ý ứng viên trước khi chọn và đọc được tin tuyển dụng.
- Query key ứng viên bao gồm job_id và page; đổi tin bỏ page cũ, không giữ kết quả tin trước.
- Kết quả xếp hạng/phân trang lấy từ backend, không lọc/sắp lại một trang dữ liệu ở frontend.
- Matching API không trả tên công ty, lương, địa điểm. Thẻ đọc tên công ty qua
  GET /companies/{id}; lương/địa điểm xem trong dialog chi tiết. Không tự tải GET /jobs/{id}
  cho các thẻ vì backend ghi lượt xem sinh viên trên endpoint này.
- GPA null là “Không chia sẻ”; GPA 0 vẫn là 0. Email/số điện thoại không có dữ liệu
  không được suy đoán hoặc lấy từ nguồn khác.
- Chỉ hiển thị thành tích backend trả về; không có chức năng tải CV ứng viên chưa nộp đơn.
- Số dạng Decimal của API có thể là chuỗi; không biến score null thành 0.
- Backend lưu timestamp UTC không kèm timezone; giao diện chuyển sang giờ địa phương.
- Giải thích là nội dung backend trả về, hiển thị bằng text; không render HTML trực tiếp.
- Không hiển thị top %, số điểm tăng dự kiến, trường đại học, khóa, dấu xác minh hoặc
  thời gian thực nếu response không có dữ liệu.
- Không có khu vực “State Previews” trong sản phẩm: loading/rỗng/lỗi chỉ xuất hiện khi phù hợp.
- API lỗi hoặc thiếu cấu hình AI được hiển thị rõ và có thử lại; không thay bằng dữ liệu mẫu.

## Điểm tích hợp với các thành viên

Các thao tác tối thiểu ApplyDialog, InviteDialog, SaveJobButton và MatchPanel được xuất qua
features/matching/index.ts để dùng lại hoặc thống nhất với Việt Anh/Khôi.
Chưa có module tương ứng của các bạn trong main tại thời điểm triển khai, nên hai trang
có thể thao tác độc lập bằng API hiện có. Khi tích hợp, chuyển phần dùng chung về module
sở hữu theo phân công thay vì tạo hai bộ logic.

Các đường dẫn /student/profile, /student/cvs và /company/jobs vẫn dùng trang do thành viên
phụ trách triển khai; bộ khung hiện hiển thị placeholder nếu phần đó chưa được làm.
Xem tin tuyển dụng từ trang matching đã có dialog đọc API thật, không phụ thuộc trang chi tiết tương lai.

Lỗi DUPLICATE_APPLICATION và DUPLICATE_INVITATION hiển thị nội dung backend và ngăn gửi lại
trong dialog. Sau thành công có thông báo xác nhận; lời mời vừa gửi được ghi nhận trên
trang hiện tại. Sau tải lại, backend vẫn kiểm tra trùng (không suy đoán trạng thái lời mời
từ response matching vì API không có trường này).

## Kiểm tra

- npm run lint, npm run build, npm test.
- npm run test:e2e: gồm kiểm tra khung và matching; API fixture chỉ ở e2e.
- Browser matching: chọn đúng tin, đổi tin, phân trang/Back, privacy null,
  lưu/bỏ lưu và tải lại, chọn CV mặc định, ứng tuyển, mời ứng tuyển, lỗi trùng,
  lỗi AI, không có CV, kết quả rỗng, tin không được phép xem và mobile.
- Đã chạy thêm smoke bằng browser với FastAPI và SQLite tạm: đăng nhập thật,
  đọc matching, lưu việc, nộp đơn và gửi lời mời. SMTP/AI bên ngoài được tắt;
  đây không phải kiểm tra MariaDB hay gửi email/AI thật.
