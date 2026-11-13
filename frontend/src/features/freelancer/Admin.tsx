import { useRead } from "./hooks";
import { reason } from "./forms";
import { amountColumn, statusColumn } from "./columns";
import { useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { errorText } from "./messages";
import { date, download, money, obj, rows, text, unwrap } from "./api";
import type { Row } from "./api";
import {
  Action,
  Badge,
  Facts,
  List,
  LoadingError,
  Notice,
  PageHeading,
  Panel,
  Table,
} from "./ui";
import type { Column } from "./ui";
import { useBase } from "./hooks";
import BankInspection from "./BankInspection";
import CompanyReviewQueue from "./CompanyReviewQueue";
import {
  projectCategories,
  projectExperience,
  projectOptionLabel,
} from "./projectOptions";

const idColumn: Column = {
  key: "id",
  label: "Mã hồ sơ",
  render: (r) => "#" + text(r.id),
};
const titles: Record<string, [string, string]> = {
  business: [
    "Thẩm định pháp nhân & MOU",
    "Đối chiếu hồ sơ, quyền đại diện và thời hạn hợp tác.",
  ],
  projects: [
    "Thẩm định dự án & mở rộng ngân sách",
    "Duyệt phạm vi tuyển sinh viên và trần ngân sách dự án.",
  ],
  banks: [
    "Tài khoản ngân hàng nhận tiền",
    "Tra cứu người dùng và tài khoản nhận giải ngân, hoàn tiền. Không cần duyệt thủ công.",
  ],
  receipts: [
    "Khoản thu cần kiểm tra",
    "Kiểm tra tiền thực nhận, sai lệch và yêu cầu hoàn.",
  ],
  transfers: [
    "Giải ngân & hoàn tiền",
    "Theo dõi riêng từng giao dịch chi và từng nhánh của quyết toán.",
  ],
  disputes: [
    "Hàng đợi tranh chấp",
    "Tiếp nhận chứng cứ và theo dõi quá trình giải quyết.",
  ],
  reconciliation: [
    "Đối soát Freelancer",
    "Đối chiếu giao dịch PayOS và theo dõi các tác vụ tài chính cần xử lý.",
  ],
};

export function AdminPage({ section }: { section: string }) {
  if (section === "business") return <CompanyReviewQueue />;
  return <AdminOperationsPage key={section} section={section} />;
}

function AdminOperationsPage({ section }: { section: string }) {
  const base = useBase();
  const [tab, setTab] = useState(section === "reconciliation" ? "payos-collections" : "main");
  const [selected, setSelected] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [title, subtitle] = titles[section];
  let path = "";
  let columns: Column[] = [];
  const toolbar: ReactNode = null;
  let tabs: [string, string][] = [["main", "Danh sách"]];
  if (section === "projects") {
    tabs = [
      ["main", "Dự án"],
      ["expansions", "Yêu cầu mở rộng"],
    ];
    path =
      tab === "expansions"
        ? "/admin/freelance-expansions"
        : "/freelance-projects";
    columns =
      tab === "expansions"
        ? [
            idColumn,
            { key: "project_id", label: "Dự án" },
            amountColumn("budget_amount", "Ngân sách mới"),
            { key: "max_students", label: "Trần sinh viên" },
            statusColumn,
          ]
        : [
            idColumn,
            { key: "title", label: "Tên dự án" },
            amountColumn("budget_amount", "Ngân sách"),
            statusColumn,
          ];
  }
  if (section === "banks") {
    path = "/admin/bank-destinations";
    columns = [
      idColumn,
      { key: "user_name", label: "Người dùng", render: r => <div><strong>{text(r.user_name)}</strong><div className="fl-muted">{text(r.user_role_label)} · {text(r.user_email)}</div></div> },
      { key: "account_name", label: "Chủ tài khoản" },
      { key: "bank_bin", label: "Ngân hàng" },
      {
        key: "account_last4",
        label: "Số tài khoản",
        render: (r) => `•••• ${text(r.account_last4)}`,
      },
      {
        key: "status_label",
        label: "Trạng thái",
        render: (r) => <span className={`fl-badge ${["ACTIVE", "VERIFIED"].includes(text(r.verification_status)) ? "good" : ""}`}>{text(r.status_label)}</span>,
      },
    ];
  }
  if (section === "receipts") {
    tabs = [
      ["main", "Cần kiểm tra"],
      ["transactions", "Tiền thực nhận"],
    ];
    path =
      tab === "transactions"
        ? "/admin/payment-transactions"
        : "/admin/payment-reviews";
    columns =
      tab === "transactions"
        ? [
            idColumn,
            { key: "external_ref", label: "Tham chiếu" },
            { key: "payment_order_id", label: "Đơn" },
            amountColumn(),
            {
              key: "allocation_status",
              label: "Phân bổ",
              render: (r) => <Badge value={r.allocation_status} />,
            },
          ]
        : [
            idColumn,
            { key: "payment_transaction_id", label: "Giao dịch" },
            { key: "reason", label: "Sai lệch" },
            statusColumn,
          ];
  }
  if (section === "transfers") {
    path = "/admin/money-transfers";
    columns = [
      idColumn,
      { key: "settlement_id", label: "Quyết toán" },
      {
        key: "purpose",
        label: "Mục đích",
        render: (r) => <Badge value={r.purpose} />,
      },
      amountColumn(),
      statusColumn,
      { key: "provider_transaction_state", label: "Kết quả chi" },
    ];
  }
  if (section === "disputes") {
    path = "/admin/disputes";
    columns = [
      idColumn,
      { key: "milestone_id", label: "Mốc" },
      { key: "reason_code", label: "Vấn đề" },
      statusColumn,
      {
        key: "evidence_deadline",
        label: "Hạn bằng chứng",
        render: (r) => date(r.evidence_deadline),
      },
    ];
  }
  if (section === "reconciliation") {
    tabs = [
      ["payos-collections", "PayOS thu"],
      ["payos-payouts", "PayOS chi"],
      ["jobs", "Tác vụ lịch đang chạy"],
      ["outbox", "Tác vụ cần xử lý"],
    ];
    path =
      tab === "payos-collections"
          ? "/admin/finance/payos-history?direction=COLLECTION"
        : tab === "payos-payouts"
          ? "/admin/finance/payos-history?direction=PAYOUT"
        : tab === "jobs" || tab === "outbox"
          ? `/admin/freelancer/${tab}?important_only=true`
          : "/admin/finance/payos-history?direction=COLLECTION";
    columns =
      ["payos-collections", "payos-payouts"].includes(tab)
          ? [
              { key: "reference", label: "Mã PayOS" },
              { key: "project_title", label: "Dự án" },
              amountColumn(),
              { key: "provider_status", label: "PayOS", render: (r) => <Badge value={r.provider_status} /> },
              { key: "local_status", label: "Hệ thống", render: (r) => <Badge value={r.local_status} /> },
              { key: "match_status", label: "Đối chiếu", render: (r) => <Badge value={r.match_status} /> },
              { key: "provider_time", label: "Thời gian PayOS", render: (r) => date(r.provider_time) },
            ]
        : ["jobs", "outbox"].includes(tab)
          ? [idColumn,
              { key: "task_type", label: "Công việc", render: (r) => taskLabel(text(r.task_type)) },
              { key: "project_title", label: "Dự án" },
              statusColumn,
              { key: "last_error", label: "Lỗi gần nhất" },
              { key: "available_at", label: "Lịch xử lý", render: (r) => date(r.available_at || r.run_at) }]
          : [];
  }
  const s = selected;
  return (
    <>
      <PageHeading title={title} subtitle={subtitle} back={base}>
        {toolbar}
      </PageHeading>
      {section === "transfers" && (
        <Notice>
          Hệ thống kiểm tra số dư ví chi PayOS trước khi gửi lệnh. Nếu thiếu tiền,
          admin sẽ nhận thông báo tại nút chuông; lệnh tự kiểm tra lại mỗi phút.
          Chỉ cần nạp thêm vào ví chi, không cần tạo phiếu hoặc tải chứng từ.
        </Notice>
      )}
      {section === "reconciliation" && ["payos-collections", "payos-payouts"].includes(tab) && (
        <Notice>
          Dữ liệu được tra trực tiếp từ PayOS khi tải hoặc bấm Cập nhật. “Khớp” nghĩa là mã tham chiếu,
          số tiền và trạng thái phù hợp với dữ liệu nội bộ. “Lệch” hoặc “Không có trong hệ thống” cần kiểm tra.
        </Notice>
      )}
      <div className="fl-tabs">
        {tabs.map(([v, label]) => (
          <button
            key={v}
            className={tab === v ? "active" : ""}
            onClick={() => {
              setTab(v);
              setSelected(null);
            }}
          >
            {label}
          </button>
        ))}
      </div>
      {error && <Notice danger>{error}</Notice>}
      <div className={s ? "fl-grid" : ""}>
        <Panel
          title={
            section === "reconciliation" && tab === "outbox"
              ? "Tác vụ tài chính cần xử lý"
              : section === "reconciliation" && tab === "jobs"
                ? "Tác vụ theo lịch chưa hoàn tất"
                : "Hàng đợi hồ sơ"
          }
        >
          {section === "reconciliation" && ["jobs", "outbox"].includes(tab) && (
            <Notice>
              Chỉ hiển thị tác vụ đang chờ, đang xử lý, cần thử lại hoặc đã dừng do lỗi.
              Các lần gọi API thu và tác vụ kỹ thuật đã hoàn tất được ẩn để tránh nhầm với
              giao dịch tiền thành công.
            </Notice>
          )}
          <List
            key={section + tab}
            path={path}
            onRows={(items) =>
              setSelected((current) => {
                const fresh = items.find(
                  (x) => text(x.id) === text(current?.id),
                );
                return fresh && current
                  ? { ...obj(fresh.submitted_snapshot), ...fresh }
                  : null;
              })
            }
            columns={columns}
            actions={(r) => (
              <>
                {section === "disputes" ? (
                  <Link
                    className="fl-button secondary"
                    to={`${base}/disputes/${r.id}`}
                  >
                    Mở hồ sơ
                  </Link>
                ) : section === "projects" && tab !== "expansions" ? (
                  <Link
                    className="fl-button secondary"
                    to={`${base}/projects/${r.id}`}
                  >
                    Thẩm định
                  </Link>
                ) : (
                  <button
                    className="fl-button secondary"
                    onClick={() =>
                      setSelected({ ...obj(r.submitted_snapshot), ...r })
                    }
                  >
                    Xem chi tiết
                  </button>
                )}
              </>
            )}
          />
        </Panel>
        {s && (
          <aside key={`${section}:${tab}:${s.id}`}>
            <Panel
              title={`Chi tiết #${s.id}`}
              aside={
                <button className="fl-link" onClick={() => setSelected(null)}>
                  Đóng
                </button>
              }
            >
              <ShieldCheck size={24} />
              {section === "reconciliation" && ["jobs", "outbox"].includes(tab) && (
                <>
                  <Facts data={[
                    ["Công việc", taskLabel(text(s.task_type))],
                    ["Dự án", s.project_id ? <Link to={`${base}/projects/${s.project_id}`}>{text(s.project_title)}</Link> : "Chưa xác định dự án liên quan"],
                    ["Sinh viên", text(s.student_name) || "—"],
                    ["Bên thuê", text(s.client_name) || "—"],
                    ["Hợp đồng", s.contract_id ? <Link to={`${base}/contracts/${s.contract_id}`}>Hợp đồng #{text(s.contract_id)}</Link> : "—"],
                  ]} />
                  <h3>Lịch sử các lần xử lý</h3>
                  <Table data={rows(s.attempt_history)} columns={[
                    { key: "finished_at", label: "Kết thúc", render: (r) => date(r.finished_at) },
                    statusColumn,
                    { key: "error", label: "Lỗi" },
                  ]} />
                  <Notice>
                    Mỗi dòng lịch sử là kết quả của một lần xử lý. Trạng thái chờ thử lại thuộc tác vụ hiện tại.
                    Lịch sử chi tiết được ghi từ bản cập nhật này; các lần cũ chưa được lưu đầy đủ.
                    Một lần tra cứu thất bại không có nghĩa giao dịch chuyển tiền đã thất bại.
                  </Notice>
                </>
              )}
              <Facts
                data={Object.entries(s)
                  .filter(
                    ([k, v]) =>
                      ![
                        "destination_snapshot",
                        "raw_payload_json",
                        "payload_json",
                        "idempotency_key",
                        "request_hash",
                        "project_title", "student_name", "client_name", "task_type",
                        "event_key", "event_type", "entity_type", "entity_id",
                        "project_id", "contract_id", "milestone_id", "milestone_no",
                        "total_debit", "total_credit", "is_balanced",
                      ].includes(k) &&
                      (typeof v === "string" ||
                        typeof v === "number" ||
                        typeof v === "boolean"),
                  )
                  .map(
                    ([k, v]) =>
                      [
                        fieldLabel(k),
                        k === "category" ? (
                          projectOptionLabel(projectCategories, v)
                        ) : k === "experience_level" ? (
                          projectOptionLabel(projectExperience, v)
                        ) : k.includes("amount") ||
                          ["freelancer_gross", "net_amount"].includes(k) ? (
                          money(v)
                        ) : k.endsWith("_at") ||
                          k.endsWith("_until") ||
                          k.endsWith("_from") ||
                          k.endsWith("deadline") ? (
                          date(v)
                        ) : k === "status" || k === "verification_status" ? (
                          section === "banks" ? text(s.status_label) : <Badge value={v} />
                        ) : k === "verification_source" && v === "SELF_DECLARED" ? (
                          "Người dùng tự khai báo"
                        ) : typeof v === "boolean" ? (
                          v ? (
                            "Có"
                          ) : (
                            "Không"
                          )
                        ) : (
                          text(v)
                        ),
                      ] as [string, ReactNode],
                  )}
              />
              {section === "banks" && (
                <BankInspection key={text(s.id)} id={text(s.id)} />
              )}
              {section === "banks" && ["ACTIVE", "VERIFIED"].includes(text(s.verification_status)) && (
                <Action label="Ngừng sử dụng tài khoản" path={`/bank-destinations/${s.id}/disable`} fields={reason} danger />
              )}
              {section === "projects" &&
                tab === "expansions" &&
                s.status === "PENDING" && (
                  <div className="fl-actions">
                    {["approve", "reject"].map((a) => (
                      <Action
                        label={
                          a === "approve" ? "Duyệt mở rộng" : "Từ chối mở rộng"
                        }
                        key={a}
                        path={`/admin/freelance-projects/${s.project_id}/expansions/${encodeURIComponent(text(s.request_key))}/${a}`}
                        fields={a === "approve" ? [] : reason}
                      />
                    ))}
                  </div>
                )}
              {section === "projects" &&
                tab !== "expansions" &&
                rows(s.attachments).map((f) => (
                  <p key={text(f.file_id)}>
                    <button
                      className="fl-link"
                      onClick={() =>
                        void download(f.file_id).catch((e) =>
                          setError(errorText(e)),
                        )
                      }
                    >
                      {text(f.original_name)}
                    </button>
                  </p>
                ))}
              {section === "receipts" && tab === "main" && (
                <>
                  <ReceiptInfo id={text(s.payment_transaction_id)} />
                  {s.status !== "RESOLVED" && (
                    <div className="fl-actions">
                      {["ALLOCATE", "RETURN"].map((action) => (
                        <Action
                          label={
                            action === "ALLOCATE"
                              ? "Phân bổ vào mốc"
                              : "Yêu cầu hoàn khoản thu"
                          }
                          key={action}
                          path={`/admin/payment-reviews/${s.id}/resolve`}
                          body={{ action }}
                          fields={reason}
                          danger={action === "RETURN"}
                        >
                          <Notice>
                            Chỉ xử lý theo giao dịch và người trả đã xác định.
                            Hệ thống kiểm tra lại điều kiện trước khi thực hiện.
                          </Notice>
                        </Action>
                      ))}
                    </div>
                  )}
                </>
              )}
              {section === "transfers" && (
                <>
                  <Action
                    label="Kiểm tra lại giao dịch"
                    path={`/admin/money-transfers/${s.id}/refresh`}
                    fields={reason}
                  />
                  <Notice>
                    Kiểm tra lại chỉ tra cứu giao dịch cũ. Không tạo lệnh chi
                    mới và không xác nhận thành công bằng tay.
                  </Notice>
                  {s.settlement_id && (
                    <Link to={`${base}/settlements/${s.settlement_id}`}>
                      Xem các nhánh quyết toán →
                    </Link>
                  )}
                </>
              )}
              {section === "reconciliation" &&
                ["jobs", "outbox"].includes(tab) &&
                ["RETRY", "DEAD"].includes(text(s.status)) && (
                  <Action
                    label="Đưa lại vào hàng đợi"
                    path={`/admin/freelancer/${tab}/${s.id}/retry`}
                    fields={reason}
                  />
                )}
            </Panel>
          </aside>
        )}
      </div>
    </>
  );
}

function ReceiptInfo({ id }: { id: string }) {
  const q = useRead(`/admin/payment-transactions/${id}`);
  const r = unwrap(q.data);
  return (
    <>
      <LoadingError query={q} />
      {r.id && (
        <Facts
          data={[
            ["Thực nhận", money(r.amount)],
            ["Yêu cầu thu", text(r.payment_order_id)],
            ["Phân bổ", text(r.allocation_status)],
            ["Tham chiếu ngân hàng", text(r.external_ref)],
          ]}
        />
      )}
    </>
  );
}
const fieldNames: Record<string, string> = {
  recruitment_deadline: "Hạn nhận ứng tuyển",
  deadline: "Hạn hoàn thành dự án",
  category: "Danh mục công việc",
  experience_level: "Trình độ mong muốn",
  id: "Mã",
  user_id: "Người dùng",
  company_id: "Doanh nghiệp",
  status: "Trạng thái",
  reason: "Lý do",
  amount: "Số tiền",
  bank_bin: "Mã ngân hàng",
  user_name: "Người dùng",
  user_email: "Email tài khoản",
  user_role_label: "Vai trò",
  status_label: "Trạng thái sử dụng",
  verification_source: "Nguồn thông tin tài khoản",
  account_name: "Chủ tài khoản",
  account_last4: "Bốn số cuối",
  verification_status: "Xác minh",
  created_at: "Ngày tạo",
  updated_at: "Cập nhật",
  proposed_by: "Người đề xuất",
  approved_by: "Người duyệt",
  external_reference: "Tham chiếu thực tế",
  kind: "Loại giao dịch",
  company_name: "Tên pháp nhân",
  legal_name: "Tên pháp nhân",
  tax_code: "Mã số thuế",
  representative_name: "Người đại diện",
  representative_position: "Chức vụ",
  business_license_file_id: "giấy phép",
  authorization_file_id: "ủy quyền",
  document_file_id: "MOU",
  school_authority_file_id: "thẩm quyền trường",
  company_authority_file_id: "thẩm quyền doanh nghiệp",
  evidence_file_id: "chứng từ",
  payment_transaction_id: "Giao dịch thực nhận",
  purpose: "Mục đích",
  provider_transaction_state: "Kết quả giao dịch",
  provider_approval_state: "Tình trạng phê duyệt",
  recipient_user_id: "Người nhận",
  settlement_id: "Quyết toán",
  payment_order_id: "Yêu cầu thu",
  external_ref: "Tham chiếu ngân hàng",
  received_at: "Ngày nhận",
  available_at: "Thời điểm xử lý",
  attempts: "Số lần xử lý",
  last_error: "Mã lỗi vận hành",
  posted_at: "Ngày ghi sổ",
  request_key: "Mã yêu cầu",
  budget_amount: "Ngân sách",
  max_students: "Trần sinh viên",
  review_reason: "Lý do xử lý",
  agreement_code: "Mã MOU",
  effective_from: "Hiệu lực từ",
  effective_until: "Hiệu lực đến",
  signed_at: "Ngày ký",
  verified_by: "Người xác minh",
  verification_note: "Ghi chú xác minh",
};
function fieldLabel(k: string) {
  return fieldNames[k] ?? k.replaceAll("_", " ");
}

function taskLabel(kind: string) {
  return ({
    "finance.transfer": "Giải ngân / hoàn tiền",
    "finance.order": "Xử lý đơn thanh toán",
    "finance.receipt": "Xác minh khoản thu",
    "file.scan": "Kiểm tra tệp tải lên",
    "notification": "Gửi thông báo",
    "email": "Gửi email",
    "settlement.completed": "Hoàn tất quyết toán",
    "contract_version.expire": "Hết hạn đề nghị hợp đồng",
    "milestone.auto_accept": "Tự động nghiệm thu",
    "mou.expire": "Cập nhật MOU hết hiệu lực",
    "dispute.evidence_deadline": "Đóng hạn nộp chứng cứ",
    "contract.closure": "Đóng hợp đồng và dự án",
  } as Record<string, string>)[kind] || kind;
}


