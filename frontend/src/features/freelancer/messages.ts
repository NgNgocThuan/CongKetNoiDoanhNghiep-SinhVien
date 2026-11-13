import { toApiError } from "@/lib/api-error";

const codes: Record<string, string> = {
  PROJECT_INCOMPLETE:
    "Chưa đủ thông tin để gửi duyệt. Hãy nhập mô tả, ngân sách, danh mục, hạn nhận ứng tuyển, hạn hoàn thành, sản phẩm bàn giao, tiêu chí nghiệm thu và chọn ít nhất một kỹ năng.",
  FINANCE_NOT_READY:
    "Chức năng tài chính chưa được bật. Vui lòng liên hệ người quản lý nền tảng trước khi thử thanh toán.",
  PAYOS_CONFIGURATION:
    "Kênh thanh toán chưa sẵn sàng. Vui lòng thử lại sau khi nền tảng hoàn tất cấu hình.",
  BANK_DESTINATION_REQUIRED:
    "Người nhận cần có tài khoản ngân hàng đã được xác minh trước khi chuẩn bị giải ngân hoặc hoàn tiền.",
  PAYOUT_BALANCE_REQUIRED:
    "Ví chi PayOS chưa đủ tiền. Admin cần nạp thêm; hệ thống tự kiểm tra lại mỗi phút.",
  CLIENT_NOT_ELIGIBLE:
    "Tài khoản chưa đủ điều kiện. Vui lòng hoàn thiện xác minh liên hệ và hồ sơ Freelancer.",
  FUNDS_ON_HOLD:
    "Khoản ký quỹ đang được giữ để xử lý nghiệp vụ. Hãy xem hồ sơ liên quan trước khi tiếp tục.",
  OTP_NOT_READY:
    "Kênh gửi mã xác minh chưa sẵn sàng. Vui lòng liên hệ người quản lý nền tảng.",
  OTP_INVALID:
    "Mã xác minh không đúng, đã hết hạn hoặc đã được sử dụng. Hãy kiểm tra hoặc yêu cầu mã mới.",
  OTP_DELIVERY_FAILED:
    "Không gửi được mã xác minh. Hãy thử lại sau hoặc liên hệ quản trị viên nếu lỗi tiếp diễn.",
  COOLDOWN: "Chưa đến thời gian gửi lại mã. Vui lòng chờ đồng hồ đếm ngược.",
  RATE_LIMITED: "Bạn đã yêu cầu quá nhiều mã. Vui lòng thử lại sau.",
  SCANNER_NOT_READY:
    "Dịch vụ kiểm tra tệp chưa sẵn sàng. Vui lòng thử lại sau.",
  IDEMPOTENCY_CONFLICT:
    "Yêu cầu đã được sử dụng với nội dung khác. Hãy tải lại trạng thái trước khi thực hiện tiếp.",
  CONTRACT_VERSION_CONFLICT:
    "Điều khoản đã thay đổi. Hãy tải lại và đọc đúng phiên bản trước khi xác nhận.",
  SESSION_CHANGED:
    "Phiên đăng nhập đã thay đổi. Hãy mở lại dữ liệu trong tài khoản hiện tại.",
};
const messages: Record<string, string> = {
  "Recruitment deadline cannot exceed completion deadline":
    "Hạn nhận ứng tuyển không được sau hạn hoàn thành dự án.",
  "Project and recruitment deadlines must be in the future":
    "Hạn nhận ứng tuyển và hạn hoàn thành phải ở tương lai.",
  "Check proposal amounts and milestone deadlines":
    "Kiểm tra lại tổng tiền các mốc và hạn bàn giao. Hạn phải ở tương lai và không vượt quá hạn hoàn thành.",
  "Milestone dates must be within project deadline":
    "Hạn mốc không được vượt quá hạn hoàn thành dự án.",
  "OTP must target the account's current contact":
    "Email hoặc điện thoại phải khớp thông tin hiện tại của tài khoản. Hãy cập nhật liên hệ trước nếu muốn đổi.",
  "Account already exists":
    "Email hoặc thông tin tài khoản đã được sử dụng. Hãy đăng nhập hoặc dùng thông tin khác.",
  "Project policy limit exceeded":
    "Dự án vượt hạn mức số dự án, ngân sách hoặc điều kiện ký quỹ của tài khoản. Hãy kiểm tra hạn mức trước khi gửi duyệt.",
  "A refund transfer already exists":
    "Khoản thu này đã có yêu cầu hoàn. Hãy theo dõi yêu cầu cũ thay vì gửi lại.",
  "Recipient needs a verified bank destination":
    "Người nhận cần hoàn tất xác minh tài khoản ngân hàng.",
  "Only pending destinations can be verified":
    "Tài khoản này đã được xử lý. Hãy tải lại trạng thái mới nhất.",
  "Collect evidence before deciding":
    "Chưa hết thời hạn thu thập bằng chứng. Admin chỉ có thể ra quyết định sau thời hạn hiển thị trên hồ sơ tranh chấp.",
  "An administrator decision has already closed evidence collection":
    "Admin đã ra quyết định cuối cùng nên hồ sơ không còn nhận thêm bằng chứng.",
};
export function errorText(error: unknown) {
  if (
    error instanceof Error &&
    error.name !== "ApiError" &&
    error.name !== "AxiosError"
  )
    return error.message;
  const e = toApiError(error);
  if (e.code === "VALIDATION_ERROR" && Object.keys(e.fields).length) {
    const names: Record<string, string> = {
      email: "Email",
      password: "Mật khẩu",
      phone: "Số điện thoại",
      full_name: "Họ tên",
      amount: "Số tiền",
      code: "Mã OTP",
      identifier: "Thông tin liên hệ",
      deadline: "Hạn dự án",
      due_at: "Hạn bàn giao",
      reason: "Lý do",
      title: "Tiêu đề",
      tax_code: "Mã số thuế",
    };
    return Object.entries(e.fields)
      .map(([field, message]) => `${names[field] ?? field}: ${message}`)
      .join(" · ");
  }
  return codes[e.code] ?? messages[e.message] ?? e.message;
}
