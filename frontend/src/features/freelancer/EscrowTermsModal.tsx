import { useState, type ReactNode } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Dialog } from '@/components/ui/Dialog';
import { useRead, useBase } from './hooks';
import { command, unwrap } from './api';
import { LoadingError, Notice } from './ui';
import { errorText } from './messages';
import { useNavigate } from 'react-router-dom';
import { TERMS_VERSION } from './RegisterTermsModal';

export function EscrowTermsGate({ children }: { children: ReactNode }) {
  const q = useRead('/auth/escrow-terms');
  const data = unwrap(q.data);
  const [reachedEnd, setReachedEnd] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const navigate = useNavigate();
  const base = useBase();
  const save = useMutation({ mutationFn: () => command('/auth/escrow-terms', { accepted: true, version: TERMS_VERSION }),
    onSuccess: () => { setAccepted(true); void q.refetch(); } });
  if (q.isPending || q.isError) return <LoadingError query={q} />;
  if (accepted || data.has_accepted_escrow_terms === true) return <>{children}</>;
  const days = Number(data.review_period_seconds ?? 604800) / 86400;
  return <Dialog open onOpenChange={open => { if (!open && !save.isPending) navigate(base + '/projects'); }} title="Ký quỹ, nghiệm thu & tranh chấp" wide>
    <p>Vui lòng đọc đến cuối trước khi tạo dự án đầu tiên.</p>
    <article className="ux-reading ux-escrow-reading" tabIndex={0} aria-label="Điều khoản ký quỹ" onScroll={e => {
      const el = e.currentTarget;
      if (el.scrollHeight - el.scrollTop <= el.clientHeight + 5) setReachedEnd(true);
    }}>
      <h3>1. Tiền ký quỹ được quản lý thế nào?</h3>
      <p>Người thuê nạp tiền qua PayOS vào tài khoản thu của nền tảng. Hệ thống ghi nhận và quản lý khoản tiền theo từng hợp đồng, từng mốc. Sinh viên chưa nhận tiền ngay khi bắt đầu. Ngân sách dự án và số dư ký quỹ là hai thông tin khác nhau.</p>
      <h3>2. Ký quỹ toàn bộ hoặc theo từng mốc</h3>
      <p>Với ký quỹ toàn bộ (Full), người thuê nạp đủ 100% giá trị hợp đồng trước khi triển khai. Hình thức này phù hợp công việc ngắn hoặc đơn giản.</p>
      <p>Với ký quỹ theo từng mốc (Milestone), công việc được chia thành các giai đoạn có sản phẩm và tiêu chí riêng. Hình thức này áp dụng khi hạng tài khoản và chính sách cho phép; doanh nghiệp thông thường có thể phải ký quỹ toàn bộ. Người thuê nạp tiền cho mốc theo kế hoạch. Sinh viên chỉ bắt đầu công việc tương ứng khi hệ thống xác nhận mốc ở trạng thái FUNDED (Đã ký quỹ), không dựa vào ảnh chụp chuyển khoản.</p>
      <h3>3. Nghiệm thu và giải ngân</h3>
      <p>Khi nhận sản phẩm, người thuê kiểm tra theo tiêu chí đã thống nhất và chọn “Nghiệm thu đạt yêu cầu”, hoặc phản hồi yêu cầu sửa theo hợp đồng. Khi nghiệm thu hợp lệ, hệ thống lập nghĩa vụ chi trả cho sinh viên.</p>
      <p>Thời gian phản hồi hiện tại là {days} ngày. Khi hết hạn mà không có phản hồi và không có tranh chấp hay lệnh giữ tiền, hệ thống có thể tự động nghiệm thu và lập lệnh giải ngân. Mặc định là 7 ngày; thời hạn cụ thể được ghi trong hợp đồng. Tiền đến ngân hàng còn phụ thuộc xử lý lệnh chi và tài khoản nhận hợp lệ.</p>
      <h3>4. Khi có tranh chấp</h3>
      <p>Nếu sản phẩm sai cam kết hoặc công việc bị bỏ dở, người thuê có thể chọn “Mở tranh chấp” khi đủ điều kiện. Khoản ký quỹ của mốc bị giữ lại để chờ giải quyết, không tiếp tục tự động giải ngân.</p>
      <p>Ban quản trị Nhà trường xem xét hợp đồng, sản phẩm và bằng chứng của các bên để quyết định giải ngân, hoàn tiền hoặc phân chia theo tỷ lệ. Hai bên cần gửi bằng chứng đúng thời hạn và theo dõi thông báo trên hệ thống.</p>
      <p>Không yêu cầu sinh viên làm việc ngoài nền tảng nhằm né tránh nghĩa vụ thanh toán. Hãy thống nhất rõ phạm vi, mốc công việc và tiêu chí trước khi ký hợp đồng.</p>
      <p><strong>Bạn đã đến cuối điều khoản.</strong> Phiên bản {TERMS_VERSION}.</p>
    </article>
    {save.isError && <Notice danger>{errorText(save.error)}</Notice>}
    <p className="muted" aria-live="polite">{reachedEnd ? 'Bạn có thể xác nhận để tiếp tục.' : 'Cuộn xuống cuối nội dung để mở nút xác nhận.'}</p>
    <button className="button button--primary" disabled={!reachedEnd || save.isPending} onClick={() => save.mutate()}>Tôi đã đọc, hiểu rõ và đồng ý với điều khoản</button>
  </Dialog>;
}
