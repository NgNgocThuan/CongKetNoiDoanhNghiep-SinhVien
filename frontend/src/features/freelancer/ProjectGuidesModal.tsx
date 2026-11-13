import { useState } from 'react';
import { Dialog } from '@/components/ui/Dialog';
import { projectGuides } from './projectGuides';

export function ProjectGuidesModal() {
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const guide = projectGuides[index];
  return <><button type="button" className="fl-button secondary" onClick={() => setOpen(true)}>💡 Xem hướng dẫn & dự án mẫu tham khảo</button>
    <Dialog open={open} onOpenChange={setOpen} title="Hướng dẫn & dự án mẫu tham khảo" wide>
      <p>Đọc mẫu rồi viết theo nhu cầu thực tế của bạn. Nội dung đang nhập trong form được giữ nguyên.</p>
      <div className="ux-tabs" aria-label="Ngành nghề tham khảo">{projectGuides.map((g, i) => <button type="button" key={g.category} aria-pressed={i === index} onClick={() => setIndex(i)}>{g.category}</button>)}</div>
      <article className="ux-reading"><h3>{guide.title}</h3><h4>Mô tả & phạm vi công việc</h4><p>{guide.scope}</p>
        <h4>Sản phẩm bàn giao & tiêu chí kiểm tra</h4><ul>{guide.deliverables.map(d => <li key={d}>{d}</li>)}</ul>
        <h4>Gợi ý phân chia mốc nghiệm thu</h4><ol>{guide.milestones.map(m => <li key={m}>{m}</li>)}</ol>
        <p>Tỷ lệ trên là phần ngân sách của từng mốc, tổng cộng 100%. Điều chỉnh phạm vi, thời hạn và số tiền theo hợp đồng thực tế.</p>
      </article><div className="dialog__actions"><button type="button" className="button button--primary" onClick={() => setOpen(false)}>Đã hiểu & Đóng</button></div>
    </Dialog></>;
}
