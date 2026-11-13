import { useBase, useRead } from "./hooks";
import { reason } from "./forms";
import { amountColumn, dateColumn, statusColumn } from "./columns";
import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  Plus,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { QRCode, Spin } from "antd";
import { useAuth } from "@/features/auth";
import { errorText } from "./messages";
import {
  command,
  date,
  download,
  localInput,
  inputTimestamp,
  money,
  obj,
  rows,
  text,
  unwrap,
} from "./api";
import type { Row } from "./api";
import {
  Action,
  Badge,
  Facts,
  Fields,
  FileUpload,
  List,
  LoadingError,
  Notice,
  PageHeading,
  Panel,
  Stats,
  Table,
} from "./ui";

const REQUIRED_CONTRACT_TERMS = {
  scope_rule: "Chỉ nghiệm thu sản phẩm đáp ứng đúng phạm vi và tiêu chí đã ghi trong hợp đồng.",
  communication_rule: "Hai bên trao đổi và lưu bằng chứng bàn giao trên Student Connect.",
  revision_rule: "Yêu cầu chỉnh sửa phải nằm trong phạm vi, tiêu chí và số lần sửa đã thỏa thuận.",
  intellectual_property_rule: "Quyền sử dụng sản phẩm được chuyển giao sau khi khoản thanh toán tương ứng hoàn tất.",
  cancellation_rule: "Sau khi ký quỹ, việc hủy hoặc phân chia tiền cần có thỏa thuận hai bên hoặc quyết định tranh chấp của Admin.",
  dispute_rule: "Khi có tranh chấp, Admin căn cứ hợp đồng, tiêu chí nghiệm thu, trao đổi và tệp bàn giao trên hệ thống.",
};

export function ContractDetail() {
  const { id } = useParams();
  const base = useBase();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const [tab, setTab] = useState(
    params.get("tab") === "finance" ? "finance" : "milestones",
  );
  const q = useRead(`/freelance-contracts/${id}`, true, true);
  const c = unwrap(q.data);
  const ms = useRead(`/freelance-contracts/${id}/milestones`, true, true);
  const milestones = rows(ms.data);
  const versions = useRead(
    `/freelance-contracts/${id}/versions?page=1&size=100`,
    true,
    true,
  );
  const v = obj(c.effective_version);
  const reviews = useRead(
    `/freelance-contracts/${id}/reviews`,
    tab === "reviews",
  );
  const own = text(c.client_user_id) === text(user?.id);
  const admin = user?.role === "ADMIN";
  return (
    <>
      <LoadingError query={q} />
      {c.id && (
        <>
          <PageHeading
            title={text(c.project_title, `Hợp đồng #${id}`)}
            subtitle={`Dự án #${c.project_id} · Sinh viên #${c.freelancer_student_id}`}
            back={base + "/work"}
          >
            <Badge value={c.status} />
            {own && c.status === "DRAFT" && (
              <Action
                label="Hủy hợp đồng nháp"
                path={`/freelance-contracts/${id}/cancel-draft`}
                fields={reason}
                danger
              />
            )}
          </PageHeading>
          <Stats
            data={[
              ["Ngân sách hợp đồng", money(c.allocated_amount)],
              ["Phiên bản có hiệu lực", text(v.version_no, "Chưa thống nhất")],
              ["Số mốc công việc", milestones.length],
              [
                "Chính sách ký quỹ",
                v.funding_policy === "FULL"
                  ? "Toàn bộ hợp đồng"
                  : v.funding_policy === "PER_MILESTONE"
                    ? "Theo mốc"
                    : "Chờ thống nhất",
              ],
            ]}
          />
          <div className="fl-tabs">
            {[
              ["milestones", "Mốc công việc"],
              ["versions", "Điều khoản & phiên bản"],
              ["finance", "Ký quỹ & thanh toán"],
              ["reviews", "Đánh giá"],
            ].map(([k, label]) => (
              <button
                key={k}
                className={tab === k ? "active" : ""}
                onClick={() => setTab(k)}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === "milestones" && (
            <div className="fl-grid">
              <Panel title="Các mốc thực hiện">
                <LoadingError query={ms} />
                {milestones.map((m, i) => {
                  const t = obj(m.effective_terms);
                  return (
                    <div className="fl-step" key={text(m.id)}>
                      <div className="fl-step-head">
                        <h3>
                          <span className="fl-step-number">{i + 1}</span>
                          {text(t.title, `Mốc ${i + 1}`)}
                        </h3>
                        <Badge value={m.status} />
                      </div>
                      <p>{text(t.acceptance_criteria)}</p>
                      <div className="fl-card-meta">
                        <strong>{money(t.amount)}</strong>
                        <span>Hạn: {date(t.due_at)}</span>
                      </div>
                      <div className="fl-actions">
                        <Link
                          className="fl-button secondary"
                          to={`${base}/milestones/${m.id}`}
                        >
                          Mở không gian công việc
                        </Link>
                        {own &&
                          ["NOT_FUNDED", "FUNDING_PENDING"].includes(
                            text(m.status),
                          ) && (
                            <Link
                              className="fl-button"
                              to={`${base}/milestones/${m.id}/fund`}
                            >
                              Ký quỹ mốc này
                            </Link>
                          )}
                      </div>
                    </div>
                  );
                })}
                {!milestones.length && !ms.isPending && !ms.isError && (
                  <Notice>
                    Chưa có mốc có hiệu lực. Mở tab điều khoản để thống nhất
                    phiên bản hợp đồng.
                  </Notice>
                )}
              </Panel>
              <aside>
                <Panel title="Hai bên hợp tác">
                  <Facts
                    data={[
                      [
                        "Người thuê",
                        text(c.client_name, `Tài khoản #${c.client_user_id}`),
                      ],
                      [
                        "Sinh viên",
                        text(
                          c.student_name,
                          `Hồ sơ #${c.freelancer_student_id}`,
                        ),
                      ],
                      ["Tạo ngày", date(c.created_at)],
                      ["Có hiệu lực", date(c.activated_at)],
                    ]}
                  />
                  <div className="fl-section-footer">
                    <ShieldCheck size={18} /> Mỗi sinh viên có hợp đồng, tiền ký
                    quỹ và quyết toán riêng.
                  </div>
                </Panel>
                {v.funding_policy === "FULL" && (
                  <Notice>
                    Cần ký quỹ đủ các mốc thuộc hợp đồng này trước khi bắt đầu
                    công việc.
                  </Notice>
                )}
              </aside>
            </div>
          )}
          {tab === "versions" && (
            <>
              <LoadingError query={versions} />
              {!admin &&
                !["COMPLETED", "CANCELLED", "CLOSED"].includes(
                  text(c.status),
                ) && (
                  <VersionEditor contract={c} milestones={milestones} />
                )}{" "}
              {rows(obj(versions.data).items).map((version) => (
                <VersionCard key={text(version.id)} version={version} />
              ))}
            </>
          )}
          {tab === "finance" && <ContractFinance id={text(c.id)} />}
          {tab === "reviews" && (
            <Panel title="Đánh giá hợp tác">
              <LoadingError query={reviews} />
              <Table
                data={rows(reviews.data)}
                columns={[
                  { key: "rating", label: "Điểm sao" },
                  { key: "comment", label: "Nhận xét" },
                  dateColumn,
                ]}
              />
              {!admin &&
                !reviews.isPending &&
                !reviews.isError &&
                !rows(reviews.data).some(
                  (r) => text(r.reviewer_user_id) === text(user?.id),
                ) &&
                ["COMPLETED", "CLOSED"].includes(text(c.status)) && (
                  <Action
                    label="Đánh giá đối tác"
                    path={`/freelance-contracts/${id}/reviews`}
                    fields={[
                      {
                        name: "rating",
                        label: "Điểm từ 1 đến 5",
                        type: "number",
                        min: 1,
                        max: 5,
                      },
                      { name: "comment", label: "Nhận xét", type: "textarea" },
                    ]}
                  />
                )}
            </Panel>
          )}
        </>
      )}
    </>
  );
}

function VersionCard({ version: v }: { version: Row }) {
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const mine = text(v.created_by) === text(user?.id);
  const accepted =
    user?.role === "STUDENT" ? v.freelancer_accepted_at : v.client_accepted_at;
  const signed = obj(v.terms_json);
  const cancellation = obj(signed.cancellation_policy);
  return (
    <Panel
      title={`Phiên bản ${v.version_no}`}
      aside={<Badge value={v.status} />}
    >
      <Table
        data={rows(v.milestone_terms)}
        columns={[
          { key: "title", label: "Mốc công việc" },
          amountColumn(),
          { key: "acceptance_criteria", label: "Tiêu chí" },
          { key: "due_at", label: "Hạn", render: (r) => date(r.due_at) },
        ]}
      />
      <Facts
        data={[
          ["Người thuê theo điều khoản", text(signed.client_name)],
          ["Sinh viên theo điều khoản", text(signed.freelancer_name)],
          [
            "Chính sách ký quỹ",
            v.funding_policy === "FULL" ? "Toàn bộ hợp đồng" : "Theo từng mốc",
          ],
          [
            "Thời hạn nộp chứng cứ tranh chấp",
            signed.evidence_period_seconds
              ? `${Number(signed.evidence_period_seconds) / 86400} ngày`
              : "Theo điều khoản áp dụng",
          ],
          [
            "Hủy trước khi bắt đầu",
            cancellation.allow_before_start === true
              ? "Theo điều kiện đã thống nhất"
              : "Cần thỏa thuận / xử lý tranh chấp",
          ],
          [
            "Hủy do quá hạn",
            cancellation.allow_overdue === true
              ? "Theo điều kiện đã thống nhất"
              : "Cần thỏa thuận / xử lý tranh chấp",
          ],
        ]}
      />
      <Facts
        data={[
          ["Tổng hợp đồng", money(v.total_amount)],
          ["Phí nền tảng", `${Number(v.fee_rate_bp) / 100}%`],
          [
            "Thời hạn phản hồi",
            `${Number(v.review_period_seconds) / 86400} ngày`,
          ],
          ["Số lần sửa", text(v.max_revision_count)],
          ["Hạn chấp nhận", date(v.acceptance_deadline)],
        ]}
      />
      {!admin && (
        <div className="fl-actions">
          {v.status === "DRAFT" && mine && (
            <Action
              label="Gửi đề nghị điều khoản"
              path={`/contract-versions/${v.id}/offer`}
              fields={[
                {
                  name: "acceptance_deadline",
                  label: "Hạn chấp nhận (bỏ trống dùng mặc định)",
                  type: "datetime-local",
                  required: false,
                },
              ]}
            >
              <Notice>
                Gửi đề nghị đồng nghĩa bạn chấp nhận nội dung phiên bản này. Bên
                còn lại cần xem và chấp nhận để điều khoản có hiệu lực.
              </Notice>
            </Action>
          )}
          {v.status === "OFFERED" && !accepted && (
            <Action
              label="Chấp nhận điều khoản"
              path={`/contract-versions/${v.id}/accept`}
              body={{ content_hash: v.content_hash }}
            >
              <Notice>
                Bạn đang chấp nhận đúng phiên bản {text(v.version_no)}. Tổng hợp
                đồng {money(v.total_amount)}; phí {Number(v.fee_rate_bp) / 100}
                %. Vui lòng đọc đầy đủ mốc, thời hạn, điều kiện trong phiên bản
                này.
              </Notice>
            </Action>
          )}
          {v.status === "OFFERED" && !mine && (
            <Action
              label="Từ chối đề nghị"
              danger
              path={`/contract-versions/${v.id}/decline`}
              fields={[
                { name: "response_note", label: "Lý do", type: "textarea" },
              ]}
            />
          )}
          {["DRAFT", "OFFERED"].includes(text(v.status)) && mine && (
            <Action
              label="Rút đề nghị"
              path={`/contract-versions/${v.id}/withdraw`}
              danger
            />
          )}
        </div>
      )}
      {Boolean(accepted) && (
        <p className="fl-muted">Bạn đã chấp nhận lúc {date(accepted)}.</p>
      )}
    </Panel>
  );
}

function VersionEditor({
  contract,
  milestones,
}: {
  contract: Row;
  milestones: Row[];
}) {
  const [open, setOpen] = useState(false);
  const [steps, setSteps] = useState<Row[]>([
    { title: "", amount: "", acceptance_criteria: "", due_at: "" },
  ]);
  const [splitMilestones, setSplitMilestones] = useState(false);
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: (b: Row) =>
      command(`/freelance-contracts/${contract.id}/versions`, b),
    onSuccess: async () => {
      setOpen(false);
      await client.invalidateQueries({ queryKey: ["freelancer"] });
    },
  });
  const [error, setError] = useState("");
  const policy = obj(contract.effective_version).funding_policy;
  const effective = obj(contract.effective_version);
  const locked = (s: Row) =>
    milestones.some(
      (m) => text(m.id) === text(s.milestone_id) && m.status !== "NOT_FUNDED",
    );
  return (
    <Panel title="Đề xuất điều khoản">
      <p>
        Tạo phiên bản mới để hai bên xem xét. Các mốc đã khóa được hệ thống bảo
        vệ và không thể thay đổi.
      </p>
      <button
        className="fl-button secondary"
        onClick={() => {
          if (!open) {
            mutation.reset();
            setError("");
            const previous = rows(effective.milestone_terms);
            setSplitMilestones(previous.length > 1);
            setSteps(
              previous.length
                ? previous
                : [
                    {
                      title: "Bàn giao toàn bộ dự án",
                      amount: text(contract.allocated_amount, ""),
                      due_at: text(contract.project_deadline, ""),
                      acceptance_criteria: "Hoàn thành đầy đủ phạm vi, sản phẩm bàn giao và tiêu chí nghiệm thu của dự án.",
                    },
                  ],
            );
          }
          setOpen(!open);
        }}
      >
        <Plus size={15} /> {open ? "Ẩn biểu mẫu" : "Soạn phiên bản"}
      </button>
      {open && (
        <form
          onSubmit={(e: FormEvent<HTMLFormElement>) => {
            e.preventDefault();
            if (mutation.isPending) return;
            setError("");
            try {
              const terms = steps.map((s) => ({
                title: String(s.title),
                description: s.description ?? null,
                amount: String(s.amount),
                acceptance_criteria: String(s.acceptance_criteria),
                due_at: inputTimestamp(s.due_at),
                included: s.included !== false,
              }));
              if (terms.some((term) => Number(term.amount) <= 2000))
                throw new Error("Mỗi khoản ký quỹ phải lớn hơn 2.000 ₫.");
              if (
                contract.project_deadline &&
                terms.some((term) => new Date(term.due_at).getTime() > new Date(text(contract.project_deadline)).getTime())
              )
                throw new Error("Hạn bàn giao không được muộn hơn hạn hoàn thành dự án.");
              const total = terms
                .filter((s) => s.included)
                .reduce((sum, s) => sum + BigInt(s.amount), 0n)
                .toString();
              mutation.mutate({
                terms_json: { ...REQUIRED_CONTRACT_TERMS, ...obj(effective.terms_json) },
                total_amount: total,
                funding_policy: new FormData(e.currentTarget).get(
                  "funding_policy",
                ),
                milestone_terms: terms,
                review_period_seconds:
                  Number(new FormData(e.currentTarget).get("review_days")) *
                  86400,
                max_revision_count: Number(
                  new FormData(e.currentTarget).get("max_revision_count"),
                ),
                grace_period_seconds:
                  Number(new FormData(e.currentTarget).get("grace_days")) *
                  86400,
              });
            } catch (err) {
              setError(err instanceof Error ? err.message : "Kiểm tra lại số tiền và thời hạn bàn giao.");
            }
          }}
        >
          <Fields
            fields={[
              {
                name: "funding_policy",
                label: "Chính sách ký quỹ",
                type: "select",
                initial: text(policy, "FULL"),
                options: [
                  ["FULL", "Toàn bộ hợp đồng"],
                  ["PER_MILESTONE", "Theo từng mốc"],
                ],
              },
              {
                name: "review_days",
                label: "Thời hạn phản hồi sản phẩm (ngày)",
                type: "number",
                min: 1,
                max: 30,
                initial: String(
                  Number(effective.review_period_seconds ?? 604800) / 86400,
                ),
              },
              {
                name: "max_revision_count",
                label: "Số lần yêu cầu chỉnh sửa",
                type: "number",
                min: 0,
                max: 100,
                initial: text(effective.max_revision_count, "3"),
              },
              {
                name: "grace_days",
                label: "Thời gian gia hạn (ngày)",
                type: "number",
                min: 0,
                max: 30,
                initial: String(
                  Number(effective.grace_period_seconds ?? 259200) / 86400,
                ),
              },
            ]}
          />
          <Notice>
            <strong>Nội dung cần thỏa thuận rõ:</strong> phạm vi và sản phẩm bàn giao, tiêu chí nghiệm thu,
            số lần chỉnh sửa, thời hạn, quyền sở hữu sản phẩm, điều kiện hủy và bằng chứng dùng khi tranh chấp.
            Các điều lệ bắt buộc về ký quỹ, bàn giao, hủy và tranh chấp đã được hệ thống điền sẵn.
          </Notice>
          {!steps.some(locked) && (
            <label>
              <input
                type="checkbox"
                checked={splitMilestones}
                onChange={(event) => {
                  setSplitMilestones(event.target.checked);
                  if (!event.target.checked) setSteps([steps[0]]);
                }}
              />{" "}
              Chia công việc thành nhiều mốc
            </label>
          )}
          {steps.map((s, i) => (
            <div className="fl-step" key={i}>
              <h3>{splitMilestones ? `Mốc ${i + 1}` : "Bàn giao toàn bộ dự án"}</h3>
              <div className="fl-form-grid">
                {[
                  ["title", "Tên mốc"],
                  ["amount", "Số tiền (₫)"],
                  ["due_at", "Hạn bàn giao"],
                  ["acceptance_criteria", "Tiêu chí nghiệm thu"],
                ].map(([k, label]) => (
                  <label key={k}>
                    {label}
                    <input
                      required
                      disabled={locked(s)}
                      type={k === "due_at" ? "datetime-local" : "text"}
                      inputMode={k === "amount" ? "numeric" : undefined}
                      min={k === "amount" ? 2001 : undefined}
                      max={k === "due_at" && contract.project_deadline ? localInput(contract.project_deadline) : undefined}
                      value={k === "due_at" ? localInput(s[k]) : text(s[k], "")}
                      onChange={(e) =>
                        setSteps(
                          steps.map((x, j) =>
                            j === i ? { ...x, [k]: e.target.value } : x,
                          ),
                        )
                      }
                    />
                  </label>
                ))}
              </div>
              {locked(s) && (
                <Notice>
                  Mốc này đã bị khóa theo tiến độ hoặc nghĩa vụ tài chính. Điều
                  khoản đã chấp nhận được giữ nguyên.
                </Notice>
              )}
              {steps.length > 1 && !steps.some(locked) && (
                <button
                  type="button"
                  className="fl-button danger"
                  onClick={() => setSteps(steps.filter((_, j) => j !== i))}
                >
                  Bỏ mốc
                </button>
              )}
            </div>
          ))}
          <div className="fl-actions">
            {splitMilestones && <button
              className="fl-button secondary"
              type="button"
              onClick={() =>
                setSteps([
                  ...steps,
                  {
                    title: "",
                    amount: "",
                    due_at: "",
                    acceptance_criteria: "",
                  },
                ])
              }
            >
              Thêm mốc
            </button>}
            <button className="fl-button" disabled={mutation.isPending}>
              Lưu phiên bản nháp
            </button>
          </div>
          {(error || mutation.isError) && (
            <Notice danger>{error || errorText(mutation.error)}</Notice>
          )}
        </form>
      )}
    </Panel>
  );
}

export function ContractFinance({ id }: { id: string }) {
  const q = useRead(`/contracts/${id}/finance`, true, true);
  const f = unwrap(q.data);
  const base = useBase();
  return (
    <>
      <LoadingError query={q} />
      {!q.isError && !q.isPending && (
        <Stats
          data={[
            ["Đã ký quỹ", money(f.funded_amount)],
            ["Tiền đang giữ", money(f.held_amount)],
            ["Trong đó đang xử lý chi", money(f.reserved_amount)],
            ["Đã giải ngân (gộp phí)", money(f.released_gross)],
            ["Đã hoàn", money(f.refunded_amount)],
          ]}
        />
      )}
      <Panel title="Các yêu cầu ký quỹ">
        <List
          path={`/contracts/${id}/payment-orders`}
          columns={[
            { key: "id", label: "Yêu cầu" },
            { key: "milestone_id", label: "Mốc" },
            amountColumn("expected_amount"),
            statusColumn,
          ]}
          actions={(r) => (
            <Link to={`${base}/payments/${r.id}`}>Xem trạng thái</Link>
          )}
        />
      </Panel>
    </>
  );
}

export function MilestoneDetail() {
  const { id } = useParams();
  const base = useBase();
  const { user } = useAuth();
  const student = user?.role === "STUDENT";
  const [fileIds, setFileIds] = useState<string[]>([]);
  const [fileError, setFileError] = useState("");
  const q = useRead(`/milestones/${id}`, true, true);
  const m = unwrap(q.data);
  const t = obj(m.effective_terms);
  const deliveries = useRead(
    `/milestones/${id}/deliverables?page=1&size=100`,
    true,
    true,
  );
  const ds = rows(obj(deliveries.data).items);
  const finance = useRead(`/milestones/${id}/finance`, true, true);
  const f = unwrap(finance.data);
  const activity = useRead(`/milestones/${id}/activity`, true, true);
  const a = unwrap(activity.data);
  const d = rows(a.disputes)[0];
  return (
    <>
      <LoadingError query={q} />
      {m.id && (
        <>
          <PageHeading
            title={text(t.title, `Mốc công việc #${id}`)}
            subtitle={`Hợp đồng #${m.contract_id} · Hạn bàn giao ${date(t.due_at)}`}
            back={`${base}/contracts/${m.contract_id}`}
          >
            <Badge value={m.status} />
            {student && m.status === "FUNDED" && (
              <Action
                label="Bắt đầu công việc"
                path={`/milestones/${id}/start`}
              />
            )}
            {!student &&
              user?.role !== "ADMIN" &&
              ["NOT_FUNDED", "FUNDING_PENDING"].includes(text(m.status)) && (
                <Link
                  className="fl-button"
                  to={`${base}/milestones/${id}/fund`}
                >
                  Ký quỹ
                </Link>
              )}
          </PageHeading>
          <div className="fl-grid">
            <div>
              <Panel title="Yêu cầu & tiêu chí nghiệm thu">
                <p>{text(t.description, "")}</p>
                <p>{text(t.acceptance_criteria)}</p>
                <Facts
                  data={[
                    ["Giá trị mốc", money(t.amount)],
                    ["Hạn phản hồi", date(m.review_deadline)],
                    ["Lần yêu cầu chỉnh sửa", text(m.revision_count, "0")],
                  ]}
                />
              </Panel>
              <Panel title="Các lần bàn giao">
                <LoadingError query={deliveries} />
                {ds.map((delivery) => (
                  <article className="fl-step" key={text(delivery.id)}>
                    <div className="fl-step-head">
                      <h3>
                        <FileText size={17} /> Lần nộp{" "}
                        {text(delivery.submission_no)}
                      </h3>
                      <span className="fl-muted">
                        {date(delivery.submitted_at)}
                      </span>
                    </div>
                    <p>{text(delivery.note)}</p>
                    <div className="fl-files">
                      {rows(delivery.files).map((file) => (
                        <button
                          className="fl-button secondary"
                          key={text(file.file_id)}
                          onClick={() => {
                            setFileError("");
                            void download(
                              file.file_id,
                              text(file.original_name, `tai-lieu-${text(file.file_id)}`),
                            )
                              .then(() => setFileError(""))
                              .catch((err) => setFileError(errorText(err)));
                          }}
                        >
                          Tải {text(file.original_name, `tệp #${text(file.file_id)}`)}
                        </button>
                      ))}
                    </div>
                    {rows(delivery.reviews).map((r) => (
                      <Notice key={text(r.id)}>
                        {text(r.action) === "ACCEPT"
                          ? "Đã nghiệm thu"
                          : text(r.action) === "REQUEST_REVISION"
                            ? "Yêu cầu chỉnh sửa"
                            : text(r.action)}{" "}
                        · {text(r.reason, "Không có ghi chú")} ·{" "}
                        {date(r.reviewed_at)}
                      </Notice>
                    ))}
                    {!student &&
                      user?.role !== "ADMIN" &&
                      m.status === "SUBMITTED" &&
                      delivery.id === ds[0]?.id && (
                        <div className="fl-actions">
                          <Action
                            label="Nghiệm thu & xử lý giải ngân"
                            disabled={
                              finance.isPending ||
                              finance.isError ||
                              f.net_amount == null
                            }
                            path={`/milestones/${id}/accept`}
                            body={{ deliverable_id: delivery.id }}
                          >
                            <Facts
                              data={[
                                [
                                  "Giá trị được nghiệm thu",
                                  money(f.terms_amount ?? t.amount),
                                ],
                                [
                                  "Phí nền tảng theo điều khoản",
                                  money(f.fee_amount),
                                ],
                                [
                                  "Sinh viên thực nhận sau phí",
                                  money(f.net_amount),
                                ],
                              ]}
                            />
                            <Notice>
                              Chấp nhận sản phẩm của mốc này ({money(t.amount)}
                              ). Hệ thống chuẩn bị quyết toán theo phí đã thống
                              nhất; trạng thái đã trả tiền chỉ có sau xác nhận
                              giao dịch chi.
                            </Notice>
                          </Action>
                          <Action
                            label="Yêu cầu chỉnh sửa"
                            path={`/milestones/${id}/request-revision`}
                            body={{ deliverable_id: delivery.id }}
                            fields={reason}
                          />
                        </div>
                      )}
                  </article>
                ))}
                {!ds.length && !deliveries.isPending && (
                  <p>Chưa có sản phẩm được bàn giao.</p>
                )}
                {fileError && <Notice danger>{fileError}</Notice>}
              </Panel>
              {student &&
                ["IN_PROGRESS", "REVISION_REQUESTED"].includes(
                  text(m.status),
                ) && (
                  <Panel title="Bàn giao sản phẩm">
                    <FileUpload
                      category="DELIVERABLE"
                      onReady={(r) => setFileIds([...fileIds, text(r.id)])}
                    />
                    <p className="fl-muted">
                      Đã chọn {fileIds.length} tệp hợp lệ.
                    </p>
                    <Action
                      label="Nộp sản phẩm"
                      path={`/milestones/${id}/deliverables`}
                      body={{ file_ids: fileIds }}
                      fields={[
                        {
                          name: "note",
                          label: "Nội dung bàn giao",
                          type: "textarea",
                        },
                      ]}
                      onDone={() => setFileIds([])}
                    />
                  </Panel>
                )}
              <Panel title="Hủy & tranh chấp">
                <div className="fl-actions">
                  {user?.role !== "ADMIN" &&
                    ![
                      "PAID_OUT",
                      "REFUNDED",
                      "PARTIALLY_RELEASED",
                      "CANCELLED",
                      "SETTLEMENT_PENDING",
                    ].includes(text(m.status)) && (
                      <Action
                        label="Đề nghị hủy / thỏa thuận"
                        path={`/milestones/${id}/cancellations`}
                        fields={[
                          {
                            name: "basis",
                            label: "Căn cứ",
                            type: "select",
                            options: [["MUTUAL", "Thỏa thuận hai bên"]],
                          },
                          ...reason,
                          {
                            name: "freelancer_gross",
                            label: "Phần trả sinh viên trước phí (₫)",
                            type: "money",
                            initial: "0",
                          },
                          {
                            name: "refund_amount",
                            label: "Phần hoàn người thuê (₫)",
                            type: "money",
                            initial: text(f.funded_amount, "0"),
                          },
                        ]}
                      />
                    )}
                  {user?.role !== "ADMIN" &&
                    ["FUNDED", "IN_PROGRESS", "SUBMITTED", "REVISION_REQUESTED"].includes(
                      text(m.status),
                    ) && (
                      <Action
                        label="Mở tranh chấp"
                        path={`/milestones/${id}/disputes`}
                        fields={[
                          {
                            name: "reason_code",
                            label: "Loại vấn đề",
                            type: "select",
                            options: [
                              ["NON_COOPERATION", "Bên còn lại không hợp tác"],
                              ["QUALITY", "Chất lượng sản phẩm"],
                              ["DEADLINE", "Thời hạn"],
                              ["OTHER", "Vấn đề khác"],
                            ],
                          },
                          {
                            name: "description",
                            label: "Mô tả vấn đề",
                            type: "textarea",
                          },
                        ]}
                      />
                    )}
                </div>
                {rows(a.cancellations).map((c) => (
                  <div className="fl-step" key={text(c.id)}>
                    <h3>Đề nghị hủy #{text(c.id)}</h3>
                    <p>{text(c.reason)}</p>
                    <Facts
                      data={[
                        ["Phần sinh viên (gộp phí)", money(c.freelancer_gross)],
                        ["Phần hoàn người thuê", money(c.refund_amount)],
                        ["Trạng thái", <Badge value={c.status} />],
                      ]}
                    />
                    <div className="fl-actions">
                      {c.status === "PROPOSED" && user?.role !== "ADMIN" && (
                        <>
                          {text(c.requested_by) !== text(user?.id) ? (
                            <>
                              <Action
                                label="Đồng ý thỏa thuận"
                                path={`/cancellations/${c.id}/accept`}
                                body={{ content_hash: c.terms_hash }}
                              />
                              <Action
                                label="Từ chối"
                                path={`/cancellations/${c.id}/reject`}
                                danger
                              />
                            </>
                          ) : (
                            <Action
                              label="Rút đề nghị"
                              path={`/cancellations/${c.id}/withdraw`}
                              danger
                            />
                          )}
                        </>
                      )}
                      {c.status === "ACCEPTED" && user?.role !== "ADMIN" && (
                        <Action
                          label="Thực hiện thỏa thuận"
                          path={`/cancellations/${c.id}/execute`}
                        />
                      )}
                    </div>
                  </div>
                ))}
                {d && (
                  <Link
                    className="fl-button secondary"
                    to={`${base}/disputes/${d.id}`}
                  >
                    Xem hồ sơ tranh chấp #{text(d.id)}
                  </Link>
                )}
              </Panel>
            </div>
            <aside>
              <Panel title="Tình hình ký quỹ">
                <LoadingError query={finance} />
                {!finance.isError && !finance.isPending && (
                  <Facts
                    data={[
                      ["Đã ký quỹ", money(f.funded_amount)],
                      ["Đang giữ", money(f.held_amount)],
                      ["Trong đó đang xử lý chi", money(f.reserved_amount)],
                    ]}
                  />
                )}
                {rows(f.active_hold_ids).length > 0 && (
                  <Notice>Khoản tiền đang được giữ để xử lý nghiệp vụ.</Notice>
                )}
                <p className="fl-muted">
                  Tiến độ công việc và kết quả chuyển tiền được cập nhật riêng
                  biệt.
                </p>
              </Panel>
              <Panel title="Quyết toán">
                <List
                  path={`/milestones/${id}/settlements`}
                  columns={[{ key: "id", label: "Mã" }, statusColumn]}
                  actions={(s) => (
                    <Link to={`${base}/settlements/${s.id}`}>Xem chi tiết</Link>
                  )}
                />
              </Panel>
            </aside>
          </div>
        </>
      )}
    </>
  );
}

export function FundingPage() {
  const { id } = useParams();
  const base = useBase();
  const navigate = useNavigate();
  const { user } = useAuth();
  const q = useRead(`/milestones/${id}`);
  const m = unwrap(q.data);
  const t = obj(m.effective_terms);
  return (
    <>
      <PageHeading
        title="Ký quỹ mốc công việc"
        subtitle="Thanh toán an toàn qua payOS, gắn đúng hợp đồng và sinh viên."
        back={
          m.contract_id ? `${base}/contracts/${m.contract_id}` : base + "/work"
        }
      />
      <LoadingError query={q} />
      {m.id && (
        <div className="fl-grid">
          <Panel title={text(t.title)}>
            <Facts
              data={[
                ["Hợp đồng", `#${m.contract_id}`],
                ["Mốc công việc", `#${m.id}`],
                ["Số tiền ký quỹ", money(t.amount)],
                ["Trạng thái", <Badge value={m.status} />],
              ]}
            />
            <Notice>
              Mỗi yêu cầu thanh toán chỉ cấp vốn cho mốc này. Khi có yêu cầu
              đang xử lý, hãy mở lại yêu cầu cũ để theo dõi.
            </Notice>
            {m.status === "NOT_FUNDED" &&
              ["CLIENT", "COMPANY"].includes(user?.role ?? "") && (
                <Action
                  label="Tạo yêu cầu ký quỹ payOS"
                  path={`/milestones/${id}/payment-orders`}
                  onDone={(r) => navigate(`${base}/payments/${r.id}`)}
                >
                  <p>
                    Xác nhận ký quỹ <strong>{money(t.amount)}</strong> cho mốc{" "}
                    {text(t.title)} thuộc hợp đồng #{text(m.contract_id)}.
                  </p>
                </Action>
              )}
            <Link
              className="fl-button secondary"
              to={`${base}/contracts/${m.contract_id}`}
            >
              Xem lịch sử thanh toán hợp đồng
            </Link>
          </Panel>
          <aside>
            <Panel title="Các bước tiếp theo">
              <p>1. Tạo yêu cầu ký quỹ.</p>
              <p>2. Mở trang payOS hoặc quét QR của yêu cầu.</p>
              <p>3. Chờ hệ thống xác nhận và cập nhật vào hợp đồng.</p>
            </Panel>
          </aside>
        </div>
      )}
    </>
  );
}
export function PaymentResult() {
  const { id } = useParams();
  const base = useBase();
  const queryClient = useQueryClient();
  const q = useRead(
    `/payment-orders/${id}`,
    Boolean(id),
    (data: unknown) => {
      const root = obj(data);
      const st = text(obj(root.data ?? root).status);
      return !["PAID", "CANCELLED", "EXPIRED"].includes(st);
    },
  );
  const p = unwrap(q.data);
  const navigate = useNavigate();
  const success = p.status === "PAID";
  const expired = p.status === "EXPIRED";
  const cancelled = p.status === "CANCELLED";
  const needsReview = p.status === "NEEDS_REVIEW";
  const settled = ["PAID", "EXPIRED", "CANCELLED", "NEEDS_REVIEW"].includes(
    text(p.status),
  );
  const hasQr = Boolean(p.qr_payload);
  const checkout = text(p.checkout_url, "");
  const safeCheckout = /^https:\/\//i.test(checkout);

  useEffect(() => {
    if (success) {
      queryClient.invalidateQueries({ queryKey: ["freelancer"] });
    }
  }, [success, queryClient]);

  return (
    <div className="fl-result">
      <PageHeading
        title={
          success
            ? "Ký quỹ đã được xác nhận thành công"
            : needsReview
              ? "Giao dịch cần được kiểm tra"
              : cancelled
                ? "Yêu cầu ký quỹ đã được hủy"
                : expired
                  ? "Yêu cầu ký quỹ đã hết hạn thanh toán"
                  : "Thanh toán ký quỹ mốc công việc"
        }
        subtitle="Hệ thống tự động đồng bộ trạng thái trực tiếp từ PayOS VietQR."
      />
      <LoadingError query={q} />
      {p.id && (
        <div className="fl-grid">
          <Panel>
            <div className="fl-result-icon">
              {success ? (
                <CheckCircle2 size={42} style={{ color: "#16a34a" }} />
              ) : expired ? (
                <Clock size={42} style={{ color: "#dc2626" }} />
              ) : cancelled ? (
                <XCircle size={42} style={{ color: "#64748b" }} />
              ) : needsReview ? (
                <AlertCircle size={42} style={{ color: "#d97706" }} />
              ) : (
                <ShieldCheck size={42} style={{ color: "#2563eb" }} />
              )}
            </div>
            <h2>
              {success
                ? "Ký quỹ thành công! Tiền đã vào tài khoản đảm bảo"
                : expired
                  ? "Đã quá thời gian thanh toán (15 phút)"
                  : cancelled
                    ? "Yêu cầu thanh toán đã bị hủy"
                    : needsReview
                      ? "Khoản tiền đang được đối soát"
                      : "Quét mã VietQR để hoàn tất ký quỹ"}
            </h2>
            <div style={{ marginBottom: "16px" }}>
              <Badge value={p.status} />
            </div>

            {/* Trạng thái thành công */}
            {success && (
              <div
                style={{
                  padding: "16px",
                  background: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  borderRadius: "10px",
                  color: "#166534",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                <strong>Giao dịch ký quỹ đã được xác nhận!</strong> Khoản tiền{" "}
                <strong>{money(p.expected_amount)}</strong> đã được ghi nhận an toàn
                cho mốc công việc. Sinh viên có thể an tâm bắt đầu thực hiện.
              </div>
            )}

            {/* Trạng thái hết hạn */}
            {expired && (
              <div
                style={{
                  padding: "16px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "10px",
                  color: "#991b1b",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                <strong>Đơn thanh toán đã quá thời hạn hiệu lực!</strong> Mỗi mã
                VietQR có thời hạn thanh toán là 15 phút để đảm bảo an toàn. Bạn
                vui lòng bấm <strong>Tạo lại yêu cầu ký quỹ</strong> để nhận mã
                QR mới.
              </div>
            )}

            {/* Trạng thái bị hủy */}
            {cancelled && (
              <div
                style={{
                  padding: "16px",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: "10px",
                  color: "#475569",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                Yêu cầu thanh toán này đã được hủy. Mốc công việc đã quay về
                trạng thái chưa ký quỹ để bạn có thể thực hiện lại khi sẵn sàng.
              </div>
            )}

            {/* Trạng thái cần đối soát */}
            {needsReview && (
              <div
                style={{
                  padding: "16px",
                  background: "#fffbeb",
                  border: "1px solid #fde68a",
                  borderRadius: "10px",
                  color: "#92400e",
                  marginBottom: "20px",
                  lineHeight: 1.6,
                }}
              >
                Khoản tiền đang chờ đối chiếu với ngân hàng. Vui lòng không
                chuyển thêm tiền để tránh trùng lặp; quản trị viên sẽ kiểm tra và
                xác nhận sớm.
              </div>
            )}

            {/* Đang chờ thanh toán */}
            {!settled && (
              <Notice>
                Mở ứng dụng ngân hàng hoặc ví điện tử bất kỳ, quét mã VietQR bên
                dưới và giữ nguyên nội dung chuyển khoản. Trạng thái sẽ{" "}
                <strong>tự động cập nhật ngay lập tức</strong> khi bạn chuyển tiền
                xong.
              </Notice>
            )}

            {/* Loading spinner khi chưa load được mã QR */}
            {!settled && !hasQr && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "48px 24px",
                  gap: "16px",
                  background: "#f8fafc",
                  borderRadius: "12px",
                  margin: "20px 0",
                  border: "1px dashed #cbd5e1",
                }}
              >
                <Spin size="large" />
                <span
                  style={{
                    color: "var(--muted, #64748b)",
                    fontSize: "14px",
                    fontWeight: 500,
                  }}
                >
                  Đang khởi tạo mã QR thanh toán PayOS...
                </span>
                <span style={{ color: "#94a3b8", fontSize: "12px" }}>
                  Vui lòng đợi giây lát, không tải lại trang
                </span>
              </div>
            )}

            {/* Hiển thị mã QR khi đã có payload */}
            {!settled && hasQr && (
              <div
                className="fl-qr"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  margin: "24px 0",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    padding: "20px",
                    background: "#ffffff",
                    borderRadius: "16px",
                    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.08)",
                    border: "1px solid #e2e8f0",
                  }}
                >
                  <QRCode type="svg" value={text(p.qr_payload)} size={240} />
                </div>
                <span
                  style={{
                    fontSize: "13px",
                    color: "var(--muted, #64748b)",
                    fontWeight: 500,
                  }}
                >
                  Quét mã VietQR bằng App Ngân hàng để thanh toán tự động
                </span>
              </div>
            )}

            {/* Các nút thao tác */}
            <div className="fl-actions" style={{ marginTop: "24px" }}>
              {!settled && safeCheckout && (
                <a
                  className="fl-button"
                  href={checkout}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Mở trang thanh toán payOS
                </a>
              )}
              {!settled && (
                <Action
                  label="Kiểm tra giao dịch ngay"
                  path={`/payment-orders/${id}/refresh`}
                />
              )}
              {expired && (
                <button
                  className="fl-button primary"
                  onClick={() => navigate(`${base}/milestones/${p.milestone_id}`)}
                >
                  Tạo lại yêu cầu ký quỹ
                </button>
              )}
              {!settled && (
                <Action
                  label="Yêu cầu hủy đơn"
                  path={`/payment-orders/${id}/cancel`}
                  fields={reason}
                  danger
                />
              )}
              <button
                className="fl-button secondary"
                onClick={() => navigate(`${base}/milestones/${p.milestone_id}`)}
              >
                {success ? "Xem mốc công việc" : "Về mốc công việc"}
              </button>
            </div>
          </Panel>
          <aside>
            <Panel title="Tóm tắt thanh toán">
              <Facts
                data={[
                  ["Yêu cầu", `#${p.id}`],
                  ["Mốc công việc", `#${p.milestone_id}`],
                  ["Số tiền", money(p.expected_amount)],
                  ["Mã thanh toán", text(p.order_code)],
                  ["Hạn yêu cầu", date(p.expires_at)],
                  ["Ghi nhận lúc", date(p.paid_at)],
                ]}
              />
            </Panel>
          </aside>
        </div>
      )}
      {p.id && (
        <Panel title="Tiền thực nhận của yêu cầu">
          <List
            path={`/payment-orders/${id}/transactions`}
            columns={[
              { key: "external_ref", label: "Tham chiếu" },
              amountColumn(),
              {
                key: "allocation_status",
                label: "Phân bổ",
                render: (r) => <Badge value={r.allocation_status} />,
              },
              {
                key: "received_at",
                label: "Thời gian",
                render: (r) => date(r.received_at),
              },
            ]}
          />
        </Panel>
      )}
    </div>
  );
}

export function SettlementDetail() {
  const { id } = useParams();
  const base = useBase();
  return (
    <>
      <PageHeading
        title={`Theo dõi quyết toán #${id}`}
        subtitle="Giải ngân và hoàn tiền có kết quả riêng; chỉ hoàn tất sau khi các nhánh được xác nhận."
        back={base + "/work"}
      />
      <Panel title="Các nhánh chuyển tiền">
        <List
          path={`/settlements/${id}/money-transfers`}
          columns={[
            {
              key: "purpose",
              label: "Mục đích",
              render: (r) => <Badge value={r.purpose} />,
            },
            { key: "recipient_user_id", label: "Người nhận" },
            amountColumn(),
            statusColumn,
            { key: "provider_transaction_state", label: "Kết quả giao dịch" },
            {
              key: "succeeded_at",
              label: "Xác nhận lúc",
              render: (r) => date(r.succeeded_at),
            },
          ]}
        />
      </Panel>
    </>
  );
}
