import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog } from '@/components/ui/Dialog';
import { command, rows, text } from './api';
import { useRead } from './hooks';
import { LoadingError, Notice } from './ui';
import { errorText } from './messages';
import { toast } from '@/lib/toast';

export function BankForm() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [bin, setBin] = useState('');
  const [expanded, setExpanded] = useState(true);
  const q = useRead('/finance/banks', open);
  const banks = rows(q.data);
  const selected = banks.find(b => b.bin === bin);
  const client = useQueryClient();
  const save = useMutation({ mutationFn: (body: Record<string, unknown>) => command('/bank-destinations', body),
    onSuccess: () => { setOpen(false); setBin(''); setQuery(''); setExpanded(true); toast.success('Đã lưu tài khoản. Các khoản chi chờ bổ sung ngân hàng sẽ tự động được tiếp tục xử lý.'); void client.invalidateQueries({ queryKey: ['freelancer'] }); void client.invalidateQueries({ queryKey: ['notifications'] }); } });
  return <><button className="fl-button" onClick={() => setOpen(true)}>Thêm tài khoản ngân hàng</button>
    <Dialog open={open} onOpenChange={v => { if (!save.isPending) setOpen(v); }} title="Thêm tài khoản ngân hàng">
      <form className="ux-form" onSubmit={e => { e.preventDefault(); if (!bin || save.isPending) return;
        const data = new FormData(e.currentTarget);
        save.mutate({ bank_bin: bin, account_number: data.get('account_number'), account_name: String(data.get('account_name')).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'D').toUpperCase().trim() }); }}>
        <label>Ngân hàng<button type="button" className="ux-bank-choice" aria-expanded={expanded} onClick={() => setExpanded(v => !v)}>{selected ? text(selected.shortName) : 'Chọn ngân hàng'} ▾</button></label>
        {expanded && <div className="ux-bank-picker">
          <input aria-label="Tìm ngân hàng" placeholder="Tìm tên hoặc viết tắt: VCB, MB, BIDV…" value={query} onChange={e => setQuery(e.target.value)} />
          <LoadingError query={q} />
          <div className="ux-bank-list">{banks.filter(b => `${b.name} ${b.shortName} ${b.code}`.toLowerCase().includes(query.trim().toLowerCase())).map(b =>
            <button type="button" key={text(b.bin)} aria-pressed={bin === b.bin} onClick={() => { setBin(text(b.bin)); setExpanded(false); }}>
              <img src={text(b.logo)} alt="" loading="lazy" onError={e => { e.currentTarget.style.visibility = 'hidden'; }} /><span><strong>{text(b.shortName)}</strong><small>{text(b.name)}</small></span>
            </button>)}{!q.isPending && banks.length > 0 && !banks.some(b => `${b.name} ${b.shortName} ${b.code}`.toLowerCase().includes(query.trim().toLowerCase())) && <p>Không tìm thấy ngân hàng.</p>}</div>
        </div>}
        <label>Số tài khoản<input name="account_number" required inputMode="numeric" pattern="[0-9]{4,30}" minLength={4} maxLength={30} autoComplete="off" /></label>
        <label>Tên chủ tài khoản<input name="account_name" required minLength={2} maxLength={255} placeholder="NGUYEN VAN A" /></label>
        <p className="muted">Tên chủ tài khoản được chuyển thành chữ in hoa không dấu. Sau khi lưu, các khoản chi đang chờ bổ sung ngân hàng sẽ tự động được xử lý lại.</p>
        {save.isError && <Notice danger>{errorText(save.error)}</Notice>}
        <button className="button button--primary" disabled={!bin || save.isPending}>{save.isPending ? 'Đang lưu…' : 'Lưu tài khoản'}</button>
      </form>
    </Dialog></>;
}
