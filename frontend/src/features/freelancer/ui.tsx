import { useRead } from "./hooks";
import { formBody } from "./forms";
import type { Field } from "./forms";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { command, obj, rows, text, upload } from "./api";
import type { Page, Row } from "./api";
import { errorText } from "./messages";
import { toast } from "@/lib/toast";

export function PageHeading({
  title,
  subtitle,
  children,
  back,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  back?: string;
}) {
  return (
    <header className="fl-heading">
      <div>
        {back && (
          <Link className="fl-back" to={back}>
            <ArrowLeft size={15} /> Quay lại
          </Link>
        )}
        <p className="fl-eyebrow">STUDENT CONNECT / FREELANCER</p>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="fl-actions">{children}</div>
    </header>
  );
}
const labels: Record<string, string> = {
  CONTACT_VERIFIED: "Đã xác minh liên hệ",
  UNVERIFIED: "Chưa xác minh",
  OFFICIAL_PARTNER: "Đối tác chính thức",
  SCANNING: "Đang kiểm tra tệp",
  DRAFT: "Bản nháp",
  OFFERED: "Chờ chấp nhận",
  EFFECTIVE: "Đang hiệu lực",
  APPROVED: "Đã duyệt",
  PENDING: "Chờ xử lý",
  ACTIVE: "Đang thực hiện",
  IN_PROGRESS: "Đang thực hiện",
  PENDING_REVIEW: "Chờ kiểm tra",
  PENDING_VERIFICATION: "Chờ xác minh",
  PENDING_APPROVAL: "Chờ duyệt",
  PENDING_ACCEPTANCE: "Chờ thống nhất điều khoản",
  DECLINED: "Đã từ chối đề nghị",
  UNALLOCATED: "Chưa phân bổ",
  ALLOCATED: "Đã phân bổ ký quỹ",
  PARTIALLY_RETURNED: "Đã hoàn một phần",
  RETURNED: "Đã hoàn khoản thu",
  UNMATCHED: "Chưa xác định đơn",
  UNDERPAID: "Thiếu số tiền",
  OVERPAID: "Thừa số tiền",
  LATE: "Đến muộn",
  WRONG_ACCOUNT: "Sai tài khoản",
  DUPLICATE_PAYMENT: "Nhiều khoản cho cùng mốc",
  RELEASE: "Giải ngân cho sinh viên",
  REFUND: "Hoàn tiền người thuê",
  UNALLOCATED_REFUND: "Hoàn khoản thu chưa phân bổ",
  PAYOUT: "Trả cho sinh viên",
  SPLIT: "Phân chia hai bên",
  NON_COOPERATION: "Bên còn lại không hợp tác",
  QUALITY: "Chất lượng sản phẩm",
  DEADLINE: "Thời hạn",
  OTHER: "Vấn đề khác",
  SUBMITTED: "Chờ nghiệm thu",
  REJECTED: "Đã từ chối",
  NEEDS_REVISION: "Cần bổ sung",
  VERIFIED: "Đã xác minh",
  NOT_FUNDED: "Chưa ký quỹ",
  FUNDING_PENDING: "Chờ ký quỹ",
  FUNDED: "Đã ký quỹ",
  WAITING_BANK: "Chờ bổ sung ngân hàng",
  REVISION_REQUESTED: "Yêu cầu chỉnh sửa",
  ACCEPTED: "Đã chấp nhận",
  SETTLEMENT_PENDING: "Đang quyết toán",
  PAID_OUT: "Đã giải ngân",
  REFUNDED: "Đã hoàn tiền",
  PARTIALLY_RELEASED: "Đã phân chia",
  DISPUTED: "Đang tranh chấp",
  OPEN: "Đang mở",
  CLOSED: "Đã đóng",
  CANCELLED: "Đã hủy",
  EXPIRED: "Đã hết hạn",
  CREATING: "Đang tạo yêu cầu",
  PROCESSING: "Đang xử lý",
  UNKNOWN: "Đang xác minh giao dịch",
  SUCCEEDED: "Thành công",
  FAILED: "Cần kiểm tra lỗi",
  PAID: "Đã nhận ký quỹ",
  NEEDS_REVIEW: "Cần kiểm tra",
  PROPOSED: "Đã đề xuất",
  EXECUTING: "Đang thực hiện quyết định",
  EXECUTED: "Đã thực hiện",
  RESOLVED: "Đã giải quyết",
  UNDER_REVIEW: "Đang kiểm tra",
  EVIDENCE_COLLECTION: "Đang thu thập bằng chứng",
  DISABLED: "Ngừng sử dụng",
  WITHDRAWN: "Đã rút",
  SELECTED: "Đã được chọn",
  SHORTLISTED: "Đang cân nhắc",
  PARTIALLY_SUCCEEDED: "Hoàn tất một phần",
  POSTED: "Đã ghi nhận",
  RETRY: "Đang chờ thử lại",
  DEAD: "Cần xử lý",
  CLEAN: "Tệp hợp lệ",
  REVOKED: "Đã thu hồi",
  SUPERSEDED: "Đã thay thế",
  COMPLETED: "Đã hoàn thành",
  TERMINATED: "Đã kết thúc",
  MATCHED: "Khớp",
  MISMATCH: "Lệch dữ liệu",
  NOT_IN_SYSTEM: "Không có trong hệ thống",
  PROVIDER_UNAVAILABLE: "Không tra được PayOS",
  BALANCED: "Cân bằng",
  UNBALANCED: "Lệch sổ",
};
export function Badge({ value }: { value: unknown }) {
  const v = text(value);
  return (
    <span
      className={`fl-badge ${["SUCCEEDED", "VERIFIED", "FUNDED", "PAID", "PAID_OUT", "POSTED", "APPROVED", "COMPLETED", "CLEAN", "MATCHED", "BALANCED"].includes(v) ? "good" : ["FAILED", "REJECTED", "DEAD", "DISPUTED", "NEEDS_REVIEW", "MISMATCH", "NOT_IN_SYSTEM", "UNBALANCED"].includes(v) ? "bad" : ""}`}
    >
      {labels[v] ?? v}
    </span>
  );
}
export function Notice({
  children,
  danger = false,
}: {
  children: ReactNode;
  danger?: boolean;
}) {
  return (
    <div
      className={`fl-notice ${danger ? "danger" : ""}`}
      role={danger ? "alert" : "status"}
    >
      <AlertCircle size={18} />
      <div>{children}</div>
    </div>
  );
}
export function LoadingError({
  query,
}: {
  query: {
    isPending: boolean;
    isError: boolean;
    error: unknown;
    refetch: () => unknown;
  };
}) {
  if (query.isPending)
    return (
      <div className="fl-loading" role="status">
        Đang tải dữ liệu…
      </div>
    );
  if (query.isError)
    return (
      <Notice danger>
        {errorText(query.error)}{" "}
        <button className="fl-link" onClick={() => void query.refetch()}>
          Thử tải lại
        </button>
      </Notice>
    );
  return null;
}
export function Panel({
  title,
  children,
  aside,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  aside?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`fl-panel ${className}`.trim()}>
      {title && (
        <div className="fl-panel-title">
          <h2>{title}</h2>
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}
export function Facts({ data }: { data: [string, ReactNode][] }) {
  return (
    <dl className="fl-facts">
      {data.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}
export function Stats({ data }: { data: [string, ReactNode][] }) {
  return (
    <div className="fl-stats">
      {data.map(([k, v]) => (
        <div key={k}>
          <span>{k}</span>
          <strong>{v}</strong>
        </div>
      ))}
    </div>
  );
}
export function Fields({ fields }: { fields: Field[] }) {
  return (
    <div className="fl-form-grid">
      {fields.map((f) => (
        <label key={f.name} className={f.type === "textarea" ? "wide" : ""}>
          <span>
            {f.label}
            {f.required !== false && f.type !== "checkbox" ? " *" : ""}
          </span>
          {f.type === "textarea" ? (
            <textarea
              aria-label={f.label}
              name={f.name}
              required={f.required !== false}
              defaultValue={text(f.initial, "")}
              rows={4}
              onChange={(event) => f.onChange?.(event.target.value)}
            />
          ) : f.type === "select" ? (
            <select
              aria-label={f.label}
              name={f.name}
              defaultValue={text(f.initial, "")}
              required={f.required !== false}
              onChange={(event) => f.onChange?.(event.target.value)}
            >
              {f.options?.map(([v, label]) => (
                <option value={v} key={v}>
                  {label}
                </option>
              ))}
            </select>
          ) : (
            <input
              aria-label={f.label}
              name={f.name}
              type={f.type === "money" ? "text" : (f.type ?? "text")}
              inputMode={f.type === "money" ? "numeric" : undefined}
              pattern={f.type === "money" ? "[0-9]+" : f.pattern}
              minLength={f.minLength}
              maxLength={f.maxLength}
              min={f.min}
              max={f.max}
              onChange={(event) => f.onChange?.(event.target.value)}
              required={
                f.type === "checkbox"
                  ? f.required === true
                  : f.required !== false
              }
              defaultChecked={
                f.type === "checkbox" ? Boolean(f.initial) : undefined
              }
              defaultValue={
                f.type === "checkbox" ? undefined : text(f.initial, "")
              }
            />
          )}
          {f.hint && <small className="fl-muted">{f.hint}</small>}
        </label>
      ))}
    </div>
  );
}
export function Action({
  label,
  path,
  body = {},
  fields = [],
  method = "POST",
  onDone,
  danger = false,
  disabled = false,
  children,
  transform,
}: {
  label: string;
  path: string;
  body?: Row;
  fields?: Field[];
  method?: string;
  onDone?: (row: Row) => void;
  danger?: boolean;
  disabled?: boolean;
  children?: ReactNode;
  transform?: (row: Row) => Row;
}) {
  const [open, setOpen] = useState(false);
  const [success, setSuccess] = useState(false);
  const [inputError, setInputError] = useState("");
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: (b: Row) => command(path, b, method),
    onSuccess: async (row) => {
      await client.invalidateQueries({ queryKey: ["freelancer"] });
      setOpen(false);
      setSuccess(true);
      toast.success("Thao tác thành công.");
      onDone?.(row);
    },
    onError: (err) => {
      const msg = errorText(err);
      toast.error(msg, "Lỗi xử lý yêu cầu");
    },
  });
  return (
    <>
      {success && (
        <span className="fl-badge good" role="status">
          <Check size={16} /> Đã cập nhật
        </span>
      )}
      <Dialog.Root
        open={open}
        onOpenChange={(v) => {
          if (!mutation.isPending) {
            setOpen(v);
            mutation.reset();
            setInputError("");
            if (v) setSuccess(false);
          }
        }}
      >
        <Dialog.Trigger asChild>
          <button
            disabled={disabled}
            className={`fl-button ${danger ? "danger" : "secondary"}`}
          >
            {label}
          </button>
        </Dialog.Trigger>
        <Dialog.Portal>
          <Dialog.Overlay className="fl-overlay" />
          <Dialog.Content className="fl-modal" aria-describedby={undefined}>
            <Dialog.Title>{label}</Dialog.Title>
            <Dialog.Close
              className="fl-close"
              disabled={mutation.isPending}
              aria-label="Đóng"
            >
              <X size={20} />
            </Dialog.Close>
            <form
              onSubmit={(e: FormEvent<HTMLFormElement>) => {
                e.preventDefault();
                if (!mutation.isPending) {
                  setInputError("");
                  try {
                    const b = { ...body, ...formBody(e.currentTarget, fields) };
                    mutation.mutate(transform ? transform(b) : b);
                  } catch (err) {
                    setInputError(errorText(err));
                  }
                }
              }}
            >
              {children}
              <Fields fields={fields} />
              {!fields.length && !children && (
                <p>
                  Bạn xác nhận thực hiện thao tác này? Kết quả sẽ được kiểm tra
                  và cập nhật từ hệ thống.
                </p>
              )}
              {mutation.isError && (
                <Notice danger>{errorText(mutation.error)}</Notice>
              )}
              {inputError && <Notice danger>{inputError}</Notice>}
              <div className="fl-actions">
                <button
                  className={`fl-button ${danger ? "danger" : ""}`}
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? "Đang gửi…" : "Xác nhận"}
                </button>
              </div>
            </form>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
export interface Column {
  key: string;
  label: string;
  render?: (r: Row) => ReactNode;
}
export function Table({
  data,
  columns,
  actions,
}: {
  data: Row[];
  columns: Column[];
  actions?: (r: Row) => ReactNode;
}) {
  return data.length ? (
    <div className="fl-table-wrap">
      <table className="fl-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
            {actions && <th>Thao tác</th>}
          </tr>
        </thead>
        <tbody>
          {data.map((r, i) => (
            <tr key={text(r.id, String(i))}>
              {columns.map((c) => (
                <td key={c.key}>{c.render ? c.render(r) : text(r[c.key])}</td>
              ))}
              {actions && (
                <td>
                  <div className="fl-actions">{actions(r)}</div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <div className="fl-empty">
      <ShieldCheck size={32} />
      <h3>Chưa có dữ liệu</h3>
      <p>Các nội dung phù hợp sẽ xuất hiện tại đây.</p>
    </div>
  );
}
export function List({
  path,
  columns,
  actions,
  children,
  onRows,
}: {
  path: string;
  columns: Column[];
  actions?: (r: Row) => ReactNode;
  children?: ReactNode;
  onRows?: (data: Row[]) => void;
}) {
  return (
    <PagedList
      key={path}
      path={path}
      columns={columns}
      actions={actions}
      onRows={onRows}
    >
      {children}
    </PagedList>
  );
}
function PagedList({
  path,
  columns,
  actions,
  children,
  onRows,
}: {
  path: string;
  columns: Column[];
  actions?: (r: Row) => ReactNode;
  children?: ReactNode;
  onRows?: (data: Row[]) => void;
}) {
  const [p, setP] = useState(1);
  const [pathname, search = ""] = path.split("?");
  const params = new URLSearchParams(search);
  params.set("page", String(p));
  params.set("number", String(p));
  if (!params.has("size")) params.set("size", "20");
  const q = useRead(
    `${pathname}?${params}`,
    true,
    /payment-orders|transactions|settlements|money-transfers|bank-destinations|verifications|mou-agreements/.test(
      pathname,
    ),
  );
  const listener = useRef(onRows);
  listener.current = onRows;
  useEffect(() => {
    if (q.data) listener.current?.(rows(obj(q.data).items));
  }, [q.data]);
  const value = obj(q.data) as unknown as Page;
  useEffect(() => {
    if (q.data && p > Math.max(1, value.pages ?? 1))
      setP(Math.max(1, value.pages ?? 1));
  }, [q.data, p, value.pages]);
  return (
    <>
      <LoadingError query={q} />
      {children}
      {!q.isPending && !q.isError && (
        <>
          <Table data={rows(value.items)} columns={columns} actions={actions} />
          <div className="fl-pagination">
            <span>
              {value.total ?? 0} kết quả · Trang {p}/
              {Math.max(1, value.pages ?? 1)}
            </span>
            <button
              className="fl-button secondary"
              disabled={p <= 1}
              onClick={() => setP(p - 1)}
              aria-label="Trang trước"
            >
              <ChevronLeft size={17} />
            </button>
            <button
              className="fl-button secondary"
              disabled={p >= (value.pages ?? 1)}
              onClick={() => setP(p + 1)}
              aria-label="Trang sau"
            >
              <ChevronRight size={17} />
            </button>
            <button
              className="fl-button secondary"
              onClick={() => void q.refetch()}
            >
              <RefreshCw size={15} /> Cập nhật
            </button>
          </div>
        </>
      )}
    </>
  );
}
export function FileUpload({
  category,
  onReady,
}: {
  category: string;
  onReady: (r: Row) => void;
}) {
  const [file, setFile] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Row | null>(null);
  const seen = useRef("");
  const q = useRead(
    `/files/${text(file?.id, "")}`,
    Boolean(file?.id),
    (data) =>
      Boolean(file?.id) &&
      !["CLEAN", "REJECTED"].includes(
        text(obj(obj(data).data ?? data ?? file).scan_status),
      ),
  );
  const state = q.data ? obj(obj(q.data).data ?? q.data) : file;
  // Explicit confirmation avoids accepting a file before the server's scan completes.
  return (
    <div className="fl-upload">
      <label>
        <strong>Tải tài liệu lên</strong>
        <input
          type="file"
          accept={
            ["DELIVERABLE", "CV", "PROJECT_REFERENCE"].includes(category)
              ? ".pdf,.png,.jpg,.jpeg,.zip,.docx,.xlsx"
              : ".pdf,.png,.jpg,.jpeg"
          }
          disabled={busy}
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            e.target.value = "";
            setBusy(true);
            setError("");
            try {
              const r = await upload(f, category);
              setFile(r);
              seen.current = "";
            } catch (err) {
              setError(errorText(err));
            } finally {
              setBusy(false);
            }
          }}
        />
      </label>
      <p>
        PDF, ảnh, ZIP, DOCX hoặc XLSX · Tệp được kiểm tra định dạng và dung lượng trước khi sử dụng.
      </p>
      {busy && <p role="status">Đang tải tệp…</p>}
      {selected && <p role="status">Đã chọn: {text(selected.original_name)}</p>}
      {file && q.isError && <LoadingError query={q} />}
      {state && (
        <div className="fl-actions">
          <span>{text(state.original_name)}</span>
          <Badge value={state.scan_status} />
          <button
            type="button"
            className="fl-button secondary"
            disabled={
              state.scan_status !== "CLEAN" ||
              state.availability_status !== "AVAILABLE" ||
              seen.current === text(state.id)
            }
            onClick={() => {
              seen.current = text(state.id);
              onReady(state);
              setSelected(state);
              setFile(null);
            }}
          >
            <Check size={16} /> Sử dụng tài liệu này
          </button>
        </div>
      )}
      {state && state.scan_status === "PENDING" && (
        <p role="status">
          Tệp đang chờ kiểm tra an toàn. Trạng thái sẽ tự cập nhật; nếu chờ lâu,
          hãy liên hệ quản trị viên.
        </p>
      )}
      {state && state.scan_status === "REJECTED" && (
        <Notice danger>
          Tệp không đạt kiểm tra an toàn. Hãy chọn một tệp khác.
        </Notice>
      )}
      {error && <Notice danger>{error}</Notice>}
    </div>
  );
}
