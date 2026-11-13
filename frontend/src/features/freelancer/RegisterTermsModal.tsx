import { useState } from 'react';
import { Dialog } from '@/components/ui/Dialog';

export const TERMS_VERSION = '2026-11-12';
export function RegisterTermsModal({ open, tab, onTab, onClose, onAccept }: {
  open: boolean; tab: 'terms' | 'privacy'; onTab: (tab: 'terms' | 'privacy') => void;
  onClose: () => void; onAccept: () => void;
}) {
  return <Dialog open={open} onOpenChange={v => { if (!v) onClose(); }} title="Điều khoản Student Connect" wide>
    <div className="ux-tabs" role="tablist" aria-label="Nội dung điều khoản">
      <button type="button" role="tab" aria-selected={tab === 'terms'} aria-controls="registration-policy" onClick={() => onTab('terms')}>Điều khoản Dịch vụ & Tuyển dụng</button>
      <button type="button" role="tab" aria-selected={tab === 'privacy'} aria-controls="registration-policy" onClick={() => onTab('privacy')}>Chính sách Bảo mật Dữ liệu Cá nhân</button>
    </div>
    <article className="ux-reading" id="registration-policy" role="tabpanel" tabIndex={0}>
      <p className="muted">Phiên bản {TERMS_VERSION}</p>
      {tab === 'terms' ? <>
        <h3>1. Danh tính và quyền đại diện</h3>
        <p>Người đăng ký cam kết thông tin cá nhân, mã số thuế, tên doanh nghiệp và người đại diện là chính xác. Người đăng ký thay mặt doanh nghiệp phải là người đại diện hợp pháp hoặc được ủy quyền. Người thuê cá nhân chịu trách nhiệm với thông tin và giao dịch của mình.</p>
        <p>Mạo danh, sử dụng giấy tờ giả hoặc pháp nhân không hợp pháp có thể dẫn đến khóa tài khoản vĩnh viễn và chuyển thông tin cho cơ quan có thẩm quyền theo pháp luật.</p>
        <h3>2. Tuyển dụng minh bạch, không thu phí sinh viên</h3>
        <p>Nghiêm cấm thu phí xét hồ sơ, giữ chỗ, đặt cọc tài liệu hoặc thiết bị, đào tạo đầu vào và các khoản thu khác từ sinh viên để được tuyển dụng. Tin đăng phải mô tả rõ công việc, thù lao, thời gian và quyền lợi; không đăng thông tin gian dối hoặc phân biệt đối xử.</p>
        <h3>3. Thù lao và thanh toán Freelancer</h3>
        <p>Người thuê phải ký quỹ qua cổng thanh toán PayOS theo hợp đồng trước khi sinh viên bắt đầu công việc tương ứng. Ngân sách trên tin đăng không đồng nghĩa với tiền đã ký quỹ. Hai bên thống nhất phạm vi, sản phẩm bàn giao và tiêu chí nghiệm thu trước khi làm việc.</p>
        <p>Nghiêm cấm ép sinh viên làm ngoài nền tảng để né tránh nghĩa vụ nghiệm thu hoặc thanh toán. Người thuê có trách nhiệm phản hồi sản phẩm đúng thời hạn trong hợp đồng và cung cấp bằng chứng khi có tranh chấp.</p>
        <h3>4. Xử lý vi phạm và phản ánh</h3>
        <p>Ban quản trị Nhà trường có quyền đình chỉ, từ chối duyệt hoặc xử lý tài khoản khi có bằng chứng về lừa đảo, nợ thù lao, thu phí trái phép hoặc xúc phạm sinh viên. Người dùng có thể gửi phản ánh và bằng chứng qua chức năng báo cáo hoặc tranh chấp trên nền tảng để được xem xét.</p>
        <p>Việc xác minh hồ sơ không phải bảo đảm mọi giao dịch đều thành công. Các bên chịu trách nhiệm thực hiện cam kết trong hợp đồng; nghĩa vụ lưu trữ chứng từ và giải quyết tranh chấp có thể tiếp tục sau khi ngừng tài khoản.</p>
      </> : <>
        <h3>1. Dữ liệu và mục đích sử dụng</h3>
        <p>Thông tin tài khoản, họ tên, mã số sinh viên, email, điện thoại, GPA, CV và hồ sơ công việc được xử lý để xác thực, kết nối tuyển dụng, liên hệ phỏng vấn, thực hiện hợp đồng và giải quyết phản ánh. Doanh nghiệp chỉ sử dụng thông tin ứng viên được phép truy cập cho những mục đích này.</p>
        <h3>2. Giới hạn chia sẻ</h3>
        <p>Nghiêm cấm mua bán, chuyển giao hoặc sao chép dữ liệu sinh viên cho quảng cáo, telesale hay mục đích ngoài tuyển dụng và hợp đồng. Việc chấp nhận điều khoản này không thay thế lựa chọn riêng của sinh viên về công khai hồ sơ hoặc nhận tiếp thị.</p>
        <p>Thông tin cần thiết cho thanh toán được xử lý bởi đơn vị cung cấp dịch vụ thanh toán; việc cung cấp cho cơ quan có thẩm quyền phải theo quy định pháp luật. Không được tự ý chuyển dữ liệu cho bên thứ ba.</p>
        <h3>3. Bảo vệ, lưu trữ và xóa dữ liệu</h3>
        <p>Người dùng phải bảo mật tài khoản và chỉ cho người có nhiệm vụ truy cập dữ liệu ứng viên. Doanh nghiệp phải xóa bản sao CV khi kết thúc tuyển dụng nếu không tiếp nhận ứng viên, trừ khi có căn cứ hợp pháp cho việc lưu giữ tiếp.</p>
        <p>Dữ liệu cần cho hợp đồng, đối soát, giải quyết tranh chấp hoặc nghĩa vụ pháp luật được lưu trong thời gian cần thiết cho mục đích đó. Không dùng việc xóa tài khoản để né tránh nghĩa vụ đang tồn tại.</p>
        <h3>4. Quyền của chủ thể dữ liệu</h3>
        <p>Bạn có thể kiểm tra, yêu cầu sửa hoặc xóa thông tin, rút lại sự đồng ý và phản ánh việc xử lý dữ liệu qua Ban quản trị Nhà trường. Một số yêu cầu có thể ảnh hưởng tính năng cần dữ liệu đó hoặc bị giới hạn bởi nghĩa vụ lưu giữ theo pháp luật.</p>
        <p>Việc xử lý dữ liệu phải tuân thủ pháp luật bảo vệ dữ liệu cá nhân hiện hành, bao gồm Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 và các quy định hướng dẫn có hiệu lực.</p>
      </>}
    </article>
    <div className="dialog__actions"><button type="button" className="button button--primary" onClick={onAccept}>Tôi đã đọc và Đồng ý</button></div>
  </Dialog>;
}

export function RegistrationConsent({ checked, onChange }: { checked: boolean; onChange: (value: boolean) => void }) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<'terms' | 'privacy'>('terms');
  return <div className="ux-consent">
    <label><input type="checkbox" required checked={checked} onChange={e => onChange(e.target.checked)} /> Tôi đã đọc, hiểu rõ và đồng ý với điều khoản và chính sách của Student Connect.</label>
    <div className="ux-policy-links"><button type="button" onClick={() => { setTab('terms'); setOpen(true); }}>Điều khoản Dịch vụ & Tuyển dụng</button><button type="button" onClick={() => { setTab('privacy'); setOpen(true); }}>Chính sách Bảo mật Dữ liệu Cá nhân</button></div>
    <RegisterTermsModal open={open} tab={tab} onTab={setTab} onClose={() => setOpen(false)} onAccept={() => { onChange(true); setOpen(false); }} />
  </div>;
}
