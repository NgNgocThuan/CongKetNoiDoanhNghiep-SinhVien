import ContactVerification from "./ContactVerification";
import { UserAvatar } from '@/components/common/UserAvatar';
import { BankForm } from "./BankForm";
import { RegistrationConsent, TERMS_VERSION } from "./RegisterTermsModal";
import { CompanyVerificationFlow } from "./CompanyVerificationFlow";
import { MouPartnerFlow } from "./MouPartnerFlow";
import { useRead } from "./hooks";
import { statusColumn } from "./columns";
import { formBody, reason } from "./forms";
import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Building2, Landmark, ShieldCheck } from "lucide-react";
import { publicHttp } from "@/lib/http";
import { errorText } from "./messages";
import { useAuth } from "@/features/auth";
import { date, obj, text, unwrap, rows } from "./api";
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
  Table,
} from "./ui";
import type { Field } from "./forms";
import { useBase } from "./hooks";

export function Banks() {
  const catalog = useRead('/finance/banks');
  const overview = useRead('/freelancer/overview');
  const waiting = Number(unwrap(overview.data).waiting_bank_transfers || 0);
  return (
    <>
      <PageHeading
        title="Tài khoản ngân hàng nhận tiền"
        subtitle="Quản lý tài khoản nhận giải ngân và hoàn tiền theo hợp đồng."
      />
      {waiting > 0 && <Notice>Bạn có {waiting} khoản giải ngân/hoàn tiền đang chờ tài khoản nhận tiền. Thêm ngân hàng bên dưới để hệ thống tự động tiếp tục xử lý.</Notice>}
      <div className="fl-grid">
        <Panel title="Tài khoản đã khai báo">
          <List
            path="/bank-destinations"
            columns={[
              { key: "bank_bin", label: "Ngân hàng", render: r => text(rows(catalog.data).find(b => b.bin === r.bank_bin)?.shortName, 'Ngân hàng đã khai báo') },
              { key: "account_name", label: "Chủ tài khoản" },
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
            ]}
            actions={(r) =>
              r.verification_status !== "DISABLED" && (
                <Action
                  label="Ngừng dùng"
                  path={`/bank-destinations/${r.id}/disable`}
                  fields={reason}
                  danger
                />
              )
            }
          />
        </Panel>
        <aside>
          <Panel title="Thêm tài khoản nhận tiền">
            <Landmark size={28} />
            <p>
              Thêm tài khoản thuộc sở hữu của bạn để nhận giải ngân hoặc hoàn tiền.
              Tài khoản hợp lệ được sử dụng ngay, không cần admin duyệt.
            </p>
            <BankForm />
            <Notice>
              Khoản chi đang chờ bổ sung ngân hàng sẽ tự động được tiếp tục xử lý
              sau khi thêm tài khoản. Tài khoản mới không thay đổi người nhận của
              lệnh đã được gán tài khoản hoặc đã gửi đi.
            </Notice>
          </Panel>
        </aside>
      </div>
    </>
  );
}

export function Onboarding() {
  const { user, retry } = useAuth();
  const company = user?.role === "COMPANY";
  const profileQuery = useRead("/client-accounts/me", user?.role === "CLIENT");
  const profile = unwrap(profileQuery.data);
  const eligibility = useRead(
    "/client-accounts/eligibility/me",
    true,
    (data) => unwrap(data).business_status === "PENDING_VERIFICATION",
  );
  const e = unwrap(eligibility.data);
  return (
    <>
      <PageHeading
        title={
          company
            ? "Xác minh doanh nghiệp & MOU"
            : "Hoàn thiện hồ sơ người thuê"
        }
        subtitle="Hoàn thiện thông tin để đăng dự án, thống nhất hợp đồng và ký quỹ."
      />
      <div className="fl-grid">
        <div>
          <Panel title="Điều kiện sử dụng">
            <LoadingError query={eligibility} />
            {Boolean(e.user_id) && (
              <Facts
                data={[
                  ["Hạng tài khoản", <Badge value={e.tier} />],
                  ["Tạo nháp", e.can_draft ? "Được phép" : "Cần hoàn thiện"],
                  [
                    "Gửi duyệt / giao kết",
                    e.can_submit ? "Được phép" : "Cần hoàn thiện",
                  ],
                  ["Ký quỹ", e.can_fund ? "Được phép" : "Cần hoàn thiện"],
                ]}
              />
            )}
            {Array.isArray(e.reason_codes) && e.reason_codes.length > 0 && (
              <Notice>
                {e.reason_codes
                  .map(
                    (v) =>
                      ({
                        EMAIL_NOT_VERIFIED: "Email chưa xác minh",
                        COMPANY_NOT_VERIFIED:
                          "Hồ sơ doanh nghiệp chưa được duyệt",
                        COMPANY_SUSPENDED: "Doanh nghiệp đang bị đình chỉ",
                        USER_INACTIVE: "Tài khoản chưa hoạt động",
                        NO_COMPANY: "Chưa hoàn thiện hồ sơ doanh nghiệp",
                      })[text(v)] ?? text(v),
                  )
                  .join(" · ")}
                . Hãy hoàn thiện các mục bên dưới và kiểm tra lại.
              </Notice>
            )}
          </Panel>
          {!company && (
            <Panel title="Xác minh email">
              <ContactVerification />
            </Panel>
          )}
          {company && (
            <>
              <Panel title="Xác minh doanh nghiệp">
                <CompanyVerificationFlow />
              </Panel>
              <Panel title="Hợp tác với Nhà trường">
                <MouPartnerFlow />
              </Panel>
            </>
          )}
          {user?.role === "CLIENT" && (
            <Panel title="Hồ sơ cá nhân">
              <LoadingError query={profileQuery} />
              {profile.id && (
                <Facts
                  data={[
                    ["Họ tên", text(profile.full_name)],
                    ["Địa chỉ", text(profile.address)],
                  ]}
                />
              )}
              <Action
                disabled={profileQuery.isPending || profileQuery.isError}
                label="Cập nhật hồ sơ người thuê"
                path="/client-accounts/me"
                method="PATCH"
                fields={[
                  {
                    name: "full_name",
                    label: "Họ tên",
                    initial: text(profile.full_name, ""),
                  },
                  {
                    name: "address",
                    label: "Địa chỉ",
                    required: false,
                    initial: text(profile.address, ""),
                    maxLength: 500,
                  },
                ]}
              />
            </Panel>
          )}
          <Panel title="Cập nhật liên hệ">
            <p>
              Đổi email sẽ cần xác minh lại email mới. Số điện thoại chỉ dùng để liên hệ, không cần OTP.
            </p>
            <Action
              label="Đổi thông tin liên hệ"
              path="/auth/contacts"
              method="PATCH"
              onDone={() => void retry()}
              transform={(body) => {
                if (!body.email && !body.phone)
                  throw new Error("Nhập email hoặc điện thoại cần cập nhật.");
                return body;
              }}
              fields={[
                {
                  name: "password",
                  label: "Mật khẩu hiện tại",
                  type: "password",
                },
                {
                  name: "email",
                  label: "Email mới",
                  type: "email",
                  required: false,
                },
                {
                  name: "phone",
                  label: "Điện thoại mới (+84…)",
                  required: false,
                },
              ]}
            />
          </Panel>
        </div>
        <aside>
          <Panel title="Một hồ sơ, một người đại diện">
            <Building2 size={28} />
            <p>
              Thông tin đúng giúp bảo vệ quá trình hợp tác. Doanh nghiệp sử dụng
              một tài khoản đại diện duy nhất.
            </p>
            <ShieldCheck size={24} />
            <p>
              Xác minh pháp nhân và hiệu lực MOU được theo dõi độc lập với các
              hợp đồng đang thực hiện.
            </p>
          </Panel>
        </aside>
      </div>
    </>
  );
}

const registerFields: Field[] = [
  { name: "full_name", label: "Họ tên" },
  { name: "email", label: "Email", type: "email" },
  {
    name: "password",
    label: "Mật khẩu (8–72 ký tự)",
    type: "password",
    minLength: 8,
    maxLength: 72,
  },
  {
    name: "phone",
    label: "Số điện thoại",
    required: false,
    hint: "Nhập 09… hoặc +849…; số Việt Nam sẽ được chuyển sang +84.",
  },
  { name: "address", label: "Địa chỉ", required: false },
];
export function RegisterClient() {
  const [terms, setTerms] = useState(false);
  const navigate = useNavigate();
  const [done, setDone] = useState(false);
  const mutation = useMutation({
    mutationFn: async (b: Row) =>
      (await publicHttp.post("/auth/register-client", b)).data,
    onSuccess: () => setDone(true),
  });
  return (
    <div className="fl fl-result">
      <PageHeading
        title="Đăng ký người thuê cá nhân"
        subtitle="Kết nối với sinh viên và triển khai công việc theo hợp đồng."
      />
      <Panel>
        {done ? (
          <>
            <CheckCircleText />
            <button className="fl-button" onClick={() => navigate("/login")}>
              Đăng nhập
            </button>
          </>
        ) : (
          <form
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              if (!terms || mutation.isPending) return;
              mutation.mutate({ ...formBody(event.currentTarget, registerFields), terms_acceptance: { accepted: terms, version: TERMS_VERSION } });
            }}
          >
            <Fields fields={registerFields} />
            <RegistrationConsent checked={terms} onChange={setTerms} />
            {mutation.isError && (
              <Notice danger>{errorText(mutation.error)}</Notice>
            )}
            <div className="fl-actions">
              <button className="fl-button" disabled={mutation.isPending || !terms}>
                {mutation.isPending
                  ? "Đang đăng ký…"
                  : "Tạo tài khoản người thuê"}
              </button>
              <Link to="/login">Đã có tài khoản? Đăng nhập</Link>
            </div>
          </form>
        )}
      </Panel>
    </div>
  );
}
function CheckCircleText() {
  return (
    <Notice>
      Đã tạo tài khoản. Đăng nhập và xác minh thông tin liên hệ để bắt đầu.
    </Notice>
  );
}

export function DisputeDetail() {
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const base = useBase();
  const navigate = useNavigate();
  const { id } = useParamsCompat();
  const prefix = admin ? "/admin/disputes" : "/disputes";
  const q = useRead(`${prefix}/${id}`, true, true);
  const d = unwrap(q.data);
  const activity = useRead(
    `/milestones/${d.milestone_id}/activity`,
    Boolean(d.milestone_id),
    true,
  );
  const decisions = useRead(
    `/admin/disputes/${id}/decisions?page=1&size=100`,
    admin,
    true,
  );
  const a = unwrap(activity.data);
  const matched = Array.isArray(a.disputes)
    ? (a.disputes.map(obj).find((x) => text(x.id) === text(id)) ?? {})
    : {};
  const withdrawal = obj(matched.withdrawal);
  const [file, setFile] = useState<Row | null>(null);
  const evidence = useRead(
    `${prefix}/${id}/evidence?page=1&size=100`,
    true,
    true,
  );
  const [error, setError] = useState("");
  const evidenceDeadlineMs = Date.parse(text(d.evidence_deadline));
  const evidenceCollectionOpen =
    Number.isFinite(evidenceDeadlineMs) && evidenceDeadlineMs > Date.now();
  const visibleDecisions = admin
    ? rows(obj(decisions.data).items)
    : rows(matched.decisions);
  const finalDecision = visibleDecisions.find((item) =>
    ["APPROVED", "EXECUTING", "EXECUTED"].includes(text(item.status)),
  );
  const finalDecisionIssued = Boolean(finalDecision);
  const outcomeFields: Field[] = [
    {
      name: "outcome",
      label: "Hướng giải quyết",
      type: "select",
      options: [
        ["PAYOUT", "Giải ngân cho sinh viên"],
        ["REFUND", "Hoàn cho người thuê"],
        ["SPLIT", "Phân chia hai bên"],
      ],
    },
    {
      name: "freelancer_gross",
      label: "Phần sinh viên trước phí (₫)",
      type: "money",
      initial: "0",
    },
    {
      name: "refund_amount",
      label: "Phần hoàn người thuê (₫)",
      type: "money",
      initial: "0",
    },
    ...reason,
  ];
  return (
    <>
      <LoadingError query={q} />
      {d.id && (
        <>
          <PageHeading
            title={`Hồ sơ tranh chấp #${id}`}
            subtitle={`Mốc công việc #${d.milestone_id}`}
            back={admin ? base + "/admin/disputes" : base + "/work"}
          >
            <Badge value={d.status} />
          </PageHeading>
          <div className="fl-grid">
            <div>
              <Panel title="Nội dung vụ việc">
                <p>{text(d.description)}</p>
                <Facts
                  data={[
                    ["Vấn đề", <Badge value={d.reason_code} />],
                    ["Mở lúc", date(d.created_at)],
                    ["Hạn nộp bằng chứng", date(d.evidence_deadline)],
                  ]}
                />
                <Link to={`${base}/milestones/${d.milestone_id}`}>
                  Xem mốc và các lần bàn giao →
                </Link>
              </Panel>
              <Panel title="Bằng chứng hai bên">
                <LoadingError query={evidence} />
                <Table
                  data={
                    Array.isArray(obj(evidence.data).items)
                      ? (obj(evidence.data).items as Row[])
                      : []
                  }
                  columns={[
                    { key: "submitted_by_name", label: "Người nộp", render: (r) => (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <UserAvatar userId={text(r.submitted_by)} name={text(r.submitted_by_name)} />
                        <span>{text(r.submitted_by_name, `Tài khoản #${r.submitted_by}`)} ({text(r.submitted_by_role_label, 'Người dùng')})</span>
                      </div>
                    ) },
                    { key: "note", label: "Nội dung" },
                    {
                      key: "created_at",
                      label: "Thời gian",
                      render: (r) => date(r.created_at),
                    },
                  ]}
                  actions={(r) =>
                    r.file_id ? (
                      <button
                        className="fl-button secondary"
                        onClick={() =>
                          void import("./api")
                            .then((a) => a.download(r.file_id))
                            .catch((err) => setError(errorText(err)))
                        }
                      >
                        Tải chứng cứ
                      </button>
                    ) : null
                  }
                />
                {error && <Notice danger>{error}</Notice>}
                {!admin &&
                  !finalDecisionIssued &&
                  !["RESOLVED", "WITHDRAWN"].includes(text(d.status)) && (
                    <>
                      <FileUpload category="EVIDENCE" onReady={setFile} />
                      <Action
                        label="Bổ sung bằng chứng"
                        path={`/disputes/${id}/evidence`}
                        body={file ? { file_id: file.id } : {}}
                        fields={[
                          {
                            name: "note",
                            label: "Nội dung chứng minh",
                            type: "textarea",
                          },
                        ]}
                      />
                    </>
                  )}
              </Panel>
              <Panel title="Quyết định xử lý">
                <LoadingError query={admin ? decisions : activity} />
                {!admin && finalDecision && (
                  <Notice>
                    Admin đã ra quyết định cuối cùng: <Badge value={finalDecision.outcome} />.
                    {text(d.status) === "RESOLVED" || text(finalDecision.status) === "EXECUTED"
                      ? " Tranh chấp đã được giải quyết và hoàn tất."
                      : " Tranh chấp đã đóng, hệ thống đang xử lý kết quả thanh toán."}
                  </Notice>
                )}
                {!admin && text(d.status) === "WITHDRAWN" && (
                  <Notice>Tranh chấp đã được hai bên thống nhất rút.</Notice>
                )}
                <Table
                  data={visibleDecisions}
                  columns={[
                    { key: "revision_no", label: "Phiên bản" },
                    {
                      key: "outcome",
                      label: "Kết quả",
                      render: (r) => <Badge value={r.outcome} />,
                    },
                    {
                      key: "freelancer_gross",
                      label: "Phần sinh viên",
                      render: (r) => importMoney(r.freelancer_gross),
                    },
                    {
                      key: "refund_amount",
                      label: "Hoàn người thuê",
                      render: (r) => importMoney(r.refund_amount),
                    },
                    statusColumn,
                  ]}
                  actions={(v) =>
                    admin ? (
                      <>
                        {v.status === "APPROVED" && (
                          <Action
                            label="Thực hiện quyết định"
                            path={`/admin/dispute-decisions/${v.id}/execute`}
                            onDone={(r) => {
                              if (r.settlement_id)
                                navigate(
                                  `${base}/settlements/${r.settlement_id}`,
                                );
                            }}
                          />
                        )}
                      </>
                    ) : null
                  }
                />
              </Panel>
            </div>
            <aside>
              <Panel title="Xử lý tiếp theo">
                {admin && finalDecisionIssued && text(d.status) !== "RESOLVED" && (
                  <Notice>
                    Quyết định đã được chốt. Hệ thống đang xử lý kết quả thanh toán.
                  </Notice>
                )}
                {admin ? (
                  <>
                    {evidenceCollectionOpen && (
                      <Notice>
                        Hai bên đang trong thời gian nộp bằng chứng. Admin có thể đề
                        xuất quyết định sau {date(d.evidence_deadline)}.
                      </Notice>
                    )}
                    <Action
                      label="Đề xuất quyết định"
                      disabled={
                        evidenceCollectionOpen ||
                        ["RESOLVED", "WITHDRAWN"].includes(text(d.status))
                      }
                      path={`/admin/disputes/${id}/decisions`}
                      fields={outcomeFields}
                    />
                  </>
                ) : (
                  <>
                    {!finalDecisionIssued &&
                      !["RESOLVED", "WITHDRAWN"].includes(text(d.status)) && (
                      <Action
                        label="Đề nghị rút tranh chấp"
                        path={`/disputes/${id}/withdrawal`}
                        fields={reason}
                      />
                    )}
                    {withdrawal.id &&
                      !withdrawal.confirmed_by &&
                      text(withdrawal.requested_by) !== text(user?.id) && (
                        <Action
                          label="Đồng ý rút tranh chấp"
                          path={`/disputes/${id}/withdrawal/confirm`}
                          body={{ content_hash: withdrawal.terms_hash }}
                        />
                      )}
                  </>
                )}
              </Panel>
            </aside>
          </div>
        </>
      )}
    </>
  );
}

// Kept as hooks/helpers in a separate module to share exact route and money contracts.
import { useParams as useParamsCompat } from "react-router-dom";
import { money as importMoney } from "./api";
