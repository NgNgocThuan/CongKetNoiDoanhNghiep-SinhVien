import SkillPicker from "./SkillPicker";
import { UserAvatar } from '@/components/common/UserAvatar';
import { EscrowTermsGate } from "./EscrowTermsModal";
import { ProjectGuidesModal } from "./ProjectGuidesModal";
import { OverviewStats } from "./OverviewStats";
import { useBase } from "./hooks";
import { useRead } from "./hooks";
import { formBody, reason } from "./forms";
import { amountColumn, statusColumn, applicationStatusColumn } from "./columns";
import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  FileText,
  Layers3,
  Paperclip,
  Plus,
  ShieldCheck,
  Sparkles,
  Target,
  Trash2,
  Users,
} from "lucide-react";
import { useAuth } from "@/features/auth";
import { errorText } from "./messages";
import {
  command,
  date,
  download,
  downloadPath,
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
import {
  projectCategories,
  projectExperience,
  projectOptionLabel,
} from "./projectOptions";

export function Overview() {
  const base = useBase();
  const { user } = useAuth();
  const admin = user?.role === "ADMIN";
  const student = user?.role === "STUDENT";
  const projects = useRead(
    "/freelance-projects?mine=true&size=5",
    !admin && !student,
  );
  const contracts = useRead("/freelancer/contracts?size=5", !admin);
  return (
    <>
      <PageHeading
        title={
          admin
            ? "Tổng quan & hàng đợi chờ xử lý"
            : student
              ? "Không gian Freelancer của bạn"
              : `Xin chào, ${user?.company?.name ?? user?.email ?? ""}!`
        }
        subtitle="Theo dõi công việc, hợp đồng và những việc cần hoàn thành tại một nơi."
      >
        {!student && !admin && (
          <Link className="fl-button" to={base + "/projects/new"}>
            <Plus size={16} /> Tạo dự án
          </Link>
        )}
      </PageHeading>
      <OverviewStats />
      <section className="fl-hero">
        <p className="fl-eyebrow" style={{ color: "#b5edda" }}>
          KẾT NỐI NĂNG LỰC · CÙNG TẠO GIÁ TRỊ
        </p>
        <h2>
          {admin
            ? "Chủ động xử lý, minh bạch từng giao dịch."
            : student
              ? "Biến kỹ năng thành những dự án thực tế."
              : "Kết nối đúng người. Hoàn thành đúng việc."}
        </h2>
        <p>
          Mỗi sinh viên có hợp đồng và các mốc công việc riêng. Theo dõi ký quỹ,
          bàn giao và thanh toán xuyên suốt quá trình hợp tác.
        </p>
        <Link
          className="fl-button"
          to={base + (admin ? "/admin/projects" : "/projects")}
        >
          {admin
            ? "Mở hàng đợi dự án"
            : student
              ? "Khám phá dự án"
              : "Quản lý dự án"}{" "}
          <ArrowRight size={16} />
        </Link>
      </section>
      {admin ? (
        <div className="fl-card-list">
          {[
            [
              "business",
              "Pháp nhân & MOU",
              "Kiểm tra thông tin đại diện và hồ sơ đối tác.",
            ],
            [
              "projects",
              "Dự án & mở rộng",
              "Xem xét ngân sách và phạm vi tuyển sinh viên.",
            ],
            [
              "banks",
              "Tài khoản ngân hàng",
              "Tra cứu tài khoản nhận tiền gắn với từng người dùng.",
            ],
            [
              "receipts",
              "Khoản thu cần kiểm tra",
              "Xử lý các giao dịch chưa phân bổ hoặc sai lệch.",
            ],
            [
              "transfers",
              "Giải ngân & hoàn tiền",
              "Theo dõi kết quả chi tiền của từng nghĩa vụ.",
            ],
            [
              "disputes",
              "Tranh chấp",
              "Tiếp nhận bằng chứng và phê duyệt quyết định.",
            ],
            [
              "reconciliation",
              "Đối soát",
              "Theo dõi sai lệch và các tác vụ cần xử lý.",
            ],
          ].map(([path, name, desc]) => (
            <Link
              className="fl-project-card"
              to={base + "/admin/" + path}
              key={path}
            >
              <ShieldCheck size={22} />
              <h3>{name}</h3>
              <p>{desc}</p>
              <span>Xem hàng đợi →</span>
            </Link>
          ))}
        </div>
      ) : (
        <>
          <div className="fl-columns">
            <Panel title="Hợp đồng của bạn">
              <LoadingError query={contracts} />
              {!contracts.isError && !contracts.isPending && (
                <Table
                  data={rows(obj(contracts.data).items)}
                  columns={[
                    { key: "project_title", label: "Dự án" },
                    { key: "student_name", label: "Sinh viên" },
                    statusColumn,
                  ]}
                  actions={(r) => (
                    <Link to={`${base}/contracts/${r.id}`}>Mở hợp đồng →</Link>
                  )}
                />
              )}
              <Link to={base + "/work"}>Xem tất cả hợp đồng</Link>
            </Panel>
            <Panel title={student ? "Sẵn sàng hợp tác" : "Dự án gần đây"}>
              {student ? (
                <>
                  <p>
                    Khám phá dự án phù hợp, chuẩn bị đề xuất và tài khoản ngân
                    hàng để nhận thanh toán.
                  </p>
                  <Link className="fl-button" to={base + "/projects"}>
                    Tìm dự án
                  </Link>
                </>
              ) : (
                <>
                  <LoadingError query={projects} />
                  {rows(obj(projects.data).items).map((p) => (
                    <div className="fl-step" key={text(p.id)}>
                      <Link to={`${base}/projects/${p.id}`}>
                        {text(p.title)}
                      </Link>
                      <p>
                        {money(p.budget_amount)} · <Badge value={p.status} />
                      </p>
                    </div>
                  ))}
                </>
              )}
            </Panel>
          </div>
          <Notice>
            Tiền ký quỹ và tiền được giải ngân được theo dõi trong từng hợp
            đồng. Ngân sách dự án là trần phân bổ, không phải số tiền đã chuyển.
          </Notice>
        </>
      )}
    </>
  );
}

export function Projects() {
  const base = useBase();
  const { user } = useAuth();
  const student = user?.role === "STUDENT";
  const [p, setP] = useState(1);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [category, setCategory] = useState("");
  const q = useRead(
    `/freelance-projects?mine=${!student && user?.role !== "ADMIN"}&page=${p}&size=12&q=${encodeURIComponent(filter)}&category=${category}`,
  );
  const data = obj(q.data);
  const items = rows(data.items);
  return (
    <>
      <PageHeading
        title={student ? "Tìm dự án Freelancer" : "Dự án của tôi"}
        subtitle={
          student
            ? "Khám phá cơ hội thực tế và gửi đề xuất phù hợp với năng lực của bạn."
            : "Quản lý ngân sách, ứng viên và các hợp đồng sinh viên độc lập."
        }
      >
        {!student && user?.role !== "ADMIN" && (
          <Link className="fl-button" to={base + "/projects/new"}>
            <Plus size={16} /> Tạo dự án
          </Link>
        )}
      </PageHeading>
      <form
        className="fl-project-filters"
        onSubmit={(e) => {
          e.preventDefault();
          setP(1);
          setFilter(search.trim());
        }}
      >
        <input
          type="search"
          aria-label="Tìm dự án"
          placeholder="Tìm theo tên dự án…"
          maxLength={200}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="fl-button secondary" disabled={q.isFetching}>
          Tìm kiếm
        </button>
        <select
          aria-label="Lọc danh mục"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setP(1);
          }}
        >
          <option value="">Tất cả danh mục</option>
          {projectCategories.map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        {(filter || category) && (
          <button
            type="button"
            className="fl-link"
            onClick={() => {
              setSearch("");
              setFilter("");
              setCategory("");
              setP(1);
            }}
          >
            Xóa bộ lọc
          </button>
        )}
      </form>
      <LoadingError query={q} />
      <div className="fl-card-list">
        {items.map((r) => (
          <article className="fl-project-card" key={text(r.id)}>
            <div className="fl-project-card__top">
              <span className="fl-project-card__icon" aria-hidden="true">
                <BriefcaseBusiness size={22} />
              </span>
              <span className="fl-project-card__category">
                {projectOptionLabel(projectCategories, r.category)}
              </span>
              <Badge value={r.status} />
            </div>
            <h3 className="fl-project-card__title">
              <Link to={`${base}/projects/${r.id}`}>{text(r.title)}</Link>
            </h3>
            <p className="fl-project-card__client">
              <UserAvatar userId={text(r.client_user_id)} name={text(r.client_display_name, 'Người thuê')} size={28} /> {text(r.client_display_name, "Người thuê đã xác minh")}
            </p>
            <p className="fl-project-card__description">{text(r.description).slice(0, 190)}</p>
            <div className="fl-card-meta">
              <span>
                <Users size={14} /> {text(r.max_students)} vị trí
              </span>
              <span>
                <CalendarDays size={14} /> Hạn ứng tuyển {date(r.recruitment_deadline ?? r.deadline)}
              </span>
              <Badge value={r.recruitment_status} />
            </div>
            <div className="fl-project-card__footer">
              <div>
                <span className="fl-muted">Ngân sách dự án</span>
                <strong className="fl-money">
                  <CircleDollarSign size={19} />
                  {r.budget_amount == null ? "Chưa cập nhật" : money(r.budget_amount)}
                </strong>
              </div>
              <Link
                className="fl-button secondary"
                to={`${base}/projects/${r.id}`}
              >
                Xem dự án <ArrowRight size={14} />
              </Link>
            </div>
          </article>
        ))}
      </div>
      {!q.isPending && !q.isError && !items.length && (
        <Panel>
          <p>Chưa có dự án phù hợp{filter ? ` với “${filter}”` : ""}.</p>
        </Panel>
      )}
      <div className="fl-pagination">
        <span>
          {text(data.total, "0")} dự án · Trang {p}
        </span>
        <button
          className="fl-button secondary"
          disabled={p === 1}
          onClick={() => setP(p - 1)}
        >
          Trước
        </button>
        <button
          className="fl-button secondary"
          disabled={p >= Number(data.pages ?? 1)}
          onClick={() => setP(p + 1)}
        >
          Sau
        </button>
      </div>
    </>
  );
}

const projectFields: Field[] = [
  { name: "title", label: "Tên dự án" },
  {
    name: "category",
    label: "Danh mục công việc",
    type: "select",
    options: [["", "Chọn danh mục"], ...projectCategories],
  },
  {
    name: "experience_level",
    label: "Trình độ mong muốn (tùy chọn)",
    type: "select",
    options: [["", "Không yêu cầu cụ thể"], ...projectExperience],
  },
  { name: "description", label: "Mô tả công việc", type: "textarea" },
  { name: "budget_amount", label: "Tổng ngân sách dự án (₫)", type: "money" },
  {
    name: "max_students",
    label: "Số sinh viên tối đa",
    type: "number",
    min: 1,
    max: 1000,
    initial: "1",
  },
  {
    name: "recruitment_deadline",
    label: "Hạn nhận ứng tuyển",
    type: "datetime-local",
  },
  { name: "deadline", label: "Hạn hoàn thành dự án", type: "datetime-local" },
  {
    name: "funding_policy",
    label: "Chính sách ký quỹ",
    type: "select",
    options: [
      ["FULL", "Ký quỹ toàn bộ hợp đồng"],
      ["PER_MILESTONE", "Ký quỹ theo từng mốc"],
    ],
  },
  {
    name: "acceptance_criteria",
    label: "Tiêu chí nghiệm thu",
    type: "textarea",
  },
  {
    name: "deliverables_description",
    label: "Sản phẩm cần bàn giao",
    type: "textarea",
  },
];
export function ProjectEditor() {
  const { id } = useParams();
  const { user } = useAuth();
  const allowed = user?.role === "CLIENT" || user?.role === "COMPANY";
  const q = useRead(`/freelance-projects/${id}`, Boolean(id) && allowed);
  const project = unwrap(q.data);
  if (!allowed)
    return (
      <Notice>Chỉ người thuê hoặc doanh nghiệp được tạo và sửa dự án.</Notice>
    );
  if (id && (q.isPending || q.isError)) return <LoadingError query={q} />;
  if (
    id &&
    (text(project.client_user_id) !== text(user?.id) ||
      !["DRAFT", "NEEDS_REVISION"].includes(text(project.status)))
  )
    return (
      <Notice>Dự án này không ở trạng thái cho phép bạn chỉnh sửa.</Notice>
    );
  return id ? <ProjectForm key={id} project={project} /> : <EscrowTermsGate><ProjectForm key="new" /></EscrowTermsGate>;
}
function ProjectForm({ project }: { project?: Row }) {
  const base = useBase();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [skills, setSkills] = useState<string[]>(
    Array.isArray(project?.skill_ids) ? project.skill_ids.map(String) : [],
  );
  const [steps, setSteps] = useState<Row[]>(
    project ? rows(project.proposals) : [],
  );
  const [attachments, setAttachments] = useState<Row[]>(
    rows(project?.attachments),
  );
  const [error, setError] = useState("");
  const [projectDeadline, setProjectDeadline] = useState(text(project?.deadline, ""));
  const save = useMutation({
    mutationFn: (body: Row) =>
      command(
        project ? `/freelance-projects/${project.id}` : "/freelance-projects",
        body,
        project ? "PATCH" : "POST",
      ),
    onSuccess: async (r) => {
      await client.invalidateQueries({ queryKey: ["freelancer"] });
      navigate(`${base}/projects/${r.id}`);
    },
  });
  const fields = projectFields.map((f) => ({
    ...f,
    required: f.name === "title",
    onChange: f.name === "deadline" ? setProjectDeadline : f.onChange,
    initial:
      project?.[f.name] != null
        ? f.type === "datetime-local"
          ? localInput(project[f.name])
          : String(project[f.name])
        : f.initial,
  }));
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (save.isPending) return;
    setError("");
    try {
      const body = formBody(e.currentTarget, fields);
      for (const key of [
        "budget_amount",
        "deadline",
        "recruitment_deadline",
        "category",
        "experience_level",
      ]) {
        if (!(key in body)) body[key] = null;
      }
      for (const key of [
        "description",
        "acceptance_criteria",
        "deliverables_description",
      ]) {
        if (!(key in body)) body[key] = "";
      }
      const proposals = steps.map((s) => ({
        title: String(s.title),
        amount: String(s.amount),
        due_at: inputTimestamp(s.due_at),
        acceptance_criteria: String(s.acceptance_criteria),
      }));
      if (
        body.deadline &&
        proposals.some((proposal) => new Date(proposal.due_at).getTime() > new Date(String(body.deadline)).getTime())
      )
        throw Error("Hạn bàn giao của mốc phải trước hoặc bằng hạn hoàn thành dự án.");
      if (
        proposals.some(
          (s) =>
            !s.title ||
            !/^[1-9][0-9]*$/.test(s.amount) ||
            !s.acceptance_criteria,
        )
      )
        throw Error(
          "Điền đầy đủ tên, số tiền nguyên dương và tiêu chí cho mỗi mốc.",
        );
      save.mutate({
        ...body,
        proposals,
        skill_ids: skills,
        attachment_file_ids: attachments.map((a) => a.file_id ?? a.id),
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Kiểm tra lại các mốc công việc.",
      );
    }
  }
  return (
    <>
      <PageHeading
        title={project ? "Chỉnh sửa dự án" : "Tạo dự án Freelancer"}
        subtitle="Lưu nháp chỉ cần tên dự án. Hoàn thiện thông tin trước khi gửi duyệt."
        back={base + "/projects"}
      />
      <form onSubmit={submit}>
        <div className="fl-grid">
          <div>
            <Panel title="Thông tin công việc">
              <ProjectGuidesModal />
              <Fields fields={fields} />
              <SkillPicker value={skills} onChange={setSkills} initialNames={Object.fromEntries(rows(project?.skills).map(s => [text(s.id), text(s.name)]))} />
              <p className="fl-muted">
                Khi gửi duyệt, cần chọn ít nhất một kỹ năng và điền đầy đủ thông
                tin, trừ trình độ mong muốn.
              </p>
            </Panel>
            <Panel title="Tài liệu tham khảo (tùy chọn)">
              <p>
                Tối đa 10 tệp. Chỉ đính kèm tài liệu được phép chia sẻ với người
                xem tin sau khi dự án được duyệt.
              </p>
              {attachments.map((a) => (
                <div className="fl-actions" key={text(a.file_id ?? a.id)}>
                  <span>{text(a.original_name)}</span>
                  <button
                    type="button"
                    className="fl-link"
                    onClick={() =>
                      setAttachments(
                        attachments.filter(
                          (f) => (f.file_id ?? f.id) !== (a.file_id ?? a.id),
                        ),
                      )
                    }
                  >
                    Gỡ tài liệu
                  </button>
                </div>
              ))}
              {attachments.length < 10 && (
                <FileUpload
                  category="PROJECT_REFERENCE"
                  onReady={(file) =>
                    setAttachments((current) =>
                      current.some(
                        (f) => text(f.file_id ?? f.id) === text(file.id),
                      )
                        ? current
                        : [...current, file].slice(0, 10),
                    )
                  }
                />
              )}
            </Panel>
            <Panel title="Các mốc công việc đề xuất">
              <Notice>
                Đây là đề xuất cho dự án. Các mốc và số tiền chính thức sẽ được
                thống nhất trong hợp đồng riêng của từng sinh viên.
              </Notice>
              {steps.map((s, i) => (
                <div className="fl-step" key={i}>
                  <div className="fl-step-head">
                    <h3>
                      <span className="fl-step-number">{i + 1}</span>Mốc công
                      việc
                    </h3>
                    {steps.length > 0 && (
                      <button
                        type="button"
                        className="fl-button danger"
                        onClick={() =>
                          setSteps(steps.filter((_, j) => i !== j))
                        }
                      >
                        <Trash2 size={14} /> Xóa mốc
                      </button>
                    )}
                  </div>
                  <div className="fl-form-grid">
                    {[
                      ["title", "Tên mốc"],
                      ["amount", "Số tiền (₫)"],
                      ["due_at", "Hạn bàn giao"],
                      ["acceptance_criteria", "Tiêu chí nghiệm thu"],
                    ].map(([key, label]) => (
                      <label key={key}>
                        {label}
                        <input
                          required
                          type={key === "due_at" ? "datetime-local" : "text"}
                          inputMode={key === "amount" ? "numeric" : undefined}
                          max={key === "due_at" && projectDeadline ? localInput(projectDeadline) : undefined}
                          value={
                            key === "due_at"
                              ? localInput(s[key])
                              : text(s[key], "")
                          }
                          onChange={(e) =>
                            setSteps(
                              steps.map((r, j) =>
                                j === i ? { ...r, [key]: e.target.value } : r,
                              ),
                            )
                          }
                        />
                        {key === "due_at" && projectDeadline && (
                          <small className="fl-muted">Không muộn hơn hạn dự án: {date(projectDeadline)}</small>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <button
                type="button"
                className="fl-button secondary"
                disabled={steps.length >= 100}
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
                <Plus size={16} /> Thêm mốc
              </button>
              {!steps.length && (
                <p>
                  Chưa đề xuất mốc. Bạn có thể thống nhất các mốc khi lập hợp
                  đồng.
                </p>
              )}
            </Panel>
          </div>
          <aside>
            <Panel title="Sẵn sàng đăng dự án">
              <p>
                Ngân sách là tổng trần cho tất cả sinh viên. Dự án nhỏ có thể
                chỉ gồm một mốc và một sinh viên trong hợp đồng.
              </p>
              <p>
                Bạn có thể lưu nháp trước, sau đó hoàn thiện hồ sơ và gửi Admin
                xét duyệt.
              </p>
              {(error || save.isError) && (
                <Notice danger>{error || errorText(save.error)}</Notice>
              )}
              <button className="fl-button" disabled={save.isPending}>
                {save.isPending ? "Đang lưu…" : "Lưu bản nháp"}
              </button>
            </Panel>
          </aside>
        </div>
      </form>
    </>
  );
}

export function ProjectDetail() {
  const { id } = useParams();
  const base = useBase();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("overview");
  const [cvId, setCvId] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const q = useRead(`/freelance-projects/${id}`);
  const p = unwrap(q.data);
  const myApplication = obj(p.my_application);
  const own = text(p.client_user_id) === text(user?.id);
  const admin = user?.role === "ADMIN";
  const student = user?.role === "STUDENT";
  const cvs = useRead("/cvs/me", student);
  const availableCvs = rows(cvs.data);
  const selectedCvId = cvId || text(availableCvs.find((item) => item.is_default)?.id ?? availableCvs[0]?.id, "");
  const budget = useRead(
    `/freelance-projects/${id}/budget`,
    Boolean(p.id && (own || admin)),
  );
  const b = unwrap(budget.data);
  return (
    <>
      <LoadingError query={q} />
      {Boolean(p.review_reason) && <Notice>{text(p.review_reason)}</Notice>}
      {downloadError && <Notice danger>{downloadError}</Notice>}
      {p.id && (
        <>
          <PageHeading
            title={text(p.title)}
            subtitle={`Dự án #${p.id} · ${p.funding_policy === "FULL" ? "Ký quỹ toàn bộ hợp đồng" : "Ký quỹ theo mốc"}`}
            back={base + "/projects"}
          >
            <Badge value={p.status} />
            {own && ["DRAFT", "NEEDS_REVISION"].includes(text(p.status)) && (
              <>
                <Link
                  className="fl-button secondary"
                  to={`${base}/projects/${id}/edit`}
                >
                  Chỉnh sửa
                </Link>
                <Action
                  label="Gửi duyệt dự án"
                  path={`/freelance-projects/${id}/submit`}
                />
              </>
            )}
            {own && ["APPROVED", "IN_PROGRESS"].includes(text(p.status)) && (
              <Action
                label={
                  p.recruitment_status === "OPEN"
                    ? "Đóng tuyển"
                    : "Mở lại tuyển"
                }
                path={`/freelance-projects/${id}/${p.recruitment_status === "OPEN" ? "close-recruitment" : "reopen-recruitment"}`}
              />
            )}
          </PageHeading>
          <section className="fl-project-summary" aria-label="Tóm tắt dự án">
            <article className="fl-project-summary__primary">
              <span className="fl-project-summary__icon">
                <CircleDollarSign size={22} />
              </span>
              <div>
                <span>Tổng ngân sách</span>
                <strong>
                  {p.budget_amount == null
                    ? "Chưa nhập"
                    : money(p.budget_amount)}
                </strong>
              </div>
            </article>
            <article>
              <span className="fl-project-summary__icon">
                <ShieldCheck size={20} />
              </span>
              <div>
                <span>Đã phân bổ</span>
                <strong>
                  {b.allocated_total == null
                    ? "Theo hợp đồng"
                    : money(b.allocated_total)}
                </strong>
              </div>
            </article>
            <article>
              <span className="fl-project-summary__icon">
                <Users size={20} />
              </span>
              <div>
                <span>Quy mô dự án</span>
                <strong>{text(p.max_students)} sinh viên</strong>
              </div>
            </article>
            <article>
              <span className="fl-project-summary__icon">
                <CalendarDays size={20} />
              </span>
              <div>
                <span>Hạn hoàn thành</span>
                <strong>{date(p.deadline)}</strong>
              </div>
            </article>
            <article>
              <span className="fl-project-summary__icon">
                <BriefcaseBusiness size={20} />
              </span>
              <div>
                <span>Nhận ứng tuyển đến</span>
                <strong>{date(p.recruitment_deadline ?? p.deadline)}</strong>
              </div>
            </article>
          </section>
          <div className="fl-tabs">
            {[
              ["overview", "Thông tin dự án"],
              ...(own || admin ? [["applications", "Ứng viên"]] : []),
              ["contracts", "Hợp đồng"],
            ].map(([key, label]) => (
              <button
                className={tab === key ? "active" : ""}
                onClick={() => setTab(key)}
                key={key}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === "overview" && (
            <div className="fl-grid">
              <div>
                <Panel
                  className="fl-project-detail-card"
                  title="Chi tiết công việc"
                  aside={
                    <span className="fl-project-category">
                      {projectOptionLabel(projectCategories, p.category)}
                    </span>
                  }
                >
                  <div className="fl-project-attributes">
                    <div>
                      <Sparkles size={17} />
                      <span>Trình độ</span>
                      <strong>
                        {projectOptionLabel(
                          projectExperience,
                          p.experience_level,
                        )}
                      </strong>
                    </div>
                    <div className="fl-project-attributes__skills">
                      <Target size={17} />
                      <span>Kỹ năng</span>
                      <div>
                        {rows(p.skills).length ? (
                          rows(p.skills).map((skill) => (
                            <span className="fl-project-skill" key={text(skill.id, text(skill.name))}>
                              {text(skill.name)}
                            </span>
                          ))
                        ) : (
                          <strong>Chưa chọn</strong>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="fl-project-copy">
                    <div className="fl-project-copy__heading">
                      <FileText size={19} />
                      <h3>Mô tả dự án</h3>
                    </div>
                    <p>{text(p.description)}</p>
                  </div>
                  <div className="fl-project-requirements">
                    <article>
                      <span className="fl-project-requirements__icon">
                        <Layers3 size={20} />
                      </span>
                      <div>
                        <h3>Sản phẩm bàn giao</h3>
                        <p>{text(p.deliverables_description)}</p>
                      </div>
                    </article>
                    <article>
                      <span className="fl-project-requirements__icon">
                        <CheckCircle2 size={20} />
                      </span>
                      <div>
                        <h3>Tiêu chí nghiệm thu</h3>
                        <p>{text(p.acceptance_criteria)}</p>
                      </div>
                    </article>
                  </div>
                  {!!rows(p.attachments).length && (
                    <div className="fl-project-attachments">
                      <div className="fl-project-copy__heading">
                        <Paperclip size={18} />
                        <h3>Tài liệu tham khảo</h3>
                      </div>
                      {rows(p.attachments).map((f) => (
                        <div key={text(f.file_id)}>
                          <button
                            className="fl-link"
                            onClick={() =>
                              void download(f.file_id).catch((err) =>
                                setDownloadError(errorText(err)),
                              )
                            }
                          >
                            {text(f.original_name)}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </Panel>
                <Panel
                  className="fl-project-milestones"
                  title="Lộ trình công việc đề xuất"
                  aside={
                    rows(p.proposals).length ? (
                      <span>{rows(p.proposals).length} mốc</span>
                    ) : undefined
                  }
                >
                  {!rows(p.proposals).length && (
                    <div className="fl-project-empty-milestones">
                      <span><Layers3 size={24} /></span>
                      <div>
                        <strong>Chưa chia mốc ở cấp dự án</strong>
                        <p>Các mốc cụ thể sẽ được hai bên thống nhất trong hợp đồng riêng.</p>
                      </div>
                    </div>
                  )}
                  {rows(p.proposals).map((m, i) => (
                    <div className="fl-step" key={text(m.id, String(i))}>
                      <span className="fl-step-number">{i + 1}</span>
                      <div className="fl-step-content">
                        <div className="fl-step-head">
                          <h3>{text(m.title)}</h3>
                          <strong>{money(m.amount)}</strong>
                        </div>
                        <p>{text(m.acceptance_criteria)}</p>
                        <span className="fl-step-deadline">
                          <CalendarDays size={15} /> Hạn bàn giao {date(m.due_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </Panel>
              </div>
              <aside className="fl-application-aside">
                <Panel
                  className="fl-project-side-card"
                  title={student ? "Gửi đề xuất của bạn" : "Thông tin dự án"}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 22px 18px' }}>
                    <UserAvatar userId={text(p.client_user_id)} name={text(p.client_display_name, 'Người thuê')} size={42} />
                    <div><small className="fl-muted">Người đăng dự án</small><div><strong>{text(p.client_display_name, 'Người thuê')}</strong></div></div>
                  </div>
                  <div className="fl-project-side-budget">
                    <span>Ngân sách toàn dự án</span>
                    <strong>
                      {p.budget_amount == null
                        ? "Chưa cập nhật"
                        : money(p.budget_amount)}
                    </strong>
                  </div>
                  <dl className="fl-project-side-facts">
                    <div>
                      <dt>Trạng thái tuyển</dt>
                      <dd><Badge value={p.recruitment_status} /></dd>
                    </div>
                    <div>
                      <dt>Hình thức ký quỹ</dt>
                      <dd>{p.funding_policy === "FULL" ? "Toàn bộ hợp đồng" : "Theo từng mốc"}</dd>
                    </div>
                    <div>
                      <dt>Hạn ứng tuyển</dt>
                      <dd>{date(p.recruitment_deadline ?? p.deadline)}</dd>
                    </div>
                  </dl>
                  <p className="fl-application-aside__intro">
                    Ngân sách hiển thị là ngân sách toàn dự án. Mỗi sinh viên
                    thống nhất giá trị hợp đồng riêng.
                  </p>
                  {student && myApplication.id && (
                    <Notice>
                      Bạn đã ứng tuyển dự án này.{" "}
                      <Badge
                        value={
                          myApplication.status === "SUBMITTED"
                            ? "PENDING"
                            : myApplication.status
                        }
                      />
                      <p>
                        <Link to={base + "/work"}>
                          Xem đơn ứng tuyển và hợp đồng của bạn
                        </Link>
                      </p>
                    </Notice>
                  )}
                  {student &&
                    !myApplication.id &&
                    p.recruitment_status === "OPEN" &&
                    new Date(
                      inputTimestamp(p.recruitment_deadline ?? p.deadline),
                    ).getTime() > Date.now() &&
                    ["APPROVED", "IN_PROGRESS"].includes(text(p.status)) && (
                      <>
                        <LoadingError query={cvs} />
                        <div className="fl-application-callout">
                          <strong>Ứng tuyển bằng hồ sơ phù hợp nhất</strong>
                          <span>Trình bày ngắn gọn cách bạn sẽ thực hiện, mức giá và thời gian dự kiến.</span>
                        </div>
                        {availableCvs.length ? (
                          <label className="fl-application-cv">
                            <span>CV đính kèm</span>
                            <select value={selectedCvId} onChange={(event) => setCvId(event.target.value)}>
                              {availableCvs.map((item) => (
                                <option key={text(item.id)} value={text(item.id)}>
                                  {text(item.title)}{item.is_default ? " · Mặc định" : ""}
                                </option>
                              ))}
                            </select>
                          </label>
                        ) : (
                          <Notice>
                            Bạn chưa có CV. Hãy tạo CV trong mục <Link to="/student/cvs">CV của tôi</Link> trước khi ứng tuyển.
                          </Notice>
                        )}
                        <Action
                          label="Ứng tuyển dự án"
                          path={`/freelance-projects/${id}/applications`}
                          body={selectedCvId ? { cv_id: selectedCvId } : {}}
                          fields={[
                            {
                              name: "proposal",
                              label: "Đề xuất thực hiện",
                              type: "textarea",
                            },
                            {
                              name: "quoted_amount",
                              label: "Mức giá đề xuất (₫)",
                              type: "money",
                            },
                            {
                              name: "estimated_days",
                              label: "Thời gian thực hiện (ngày)",
                              type: "number",
                              min: 1,
                              max: 3650,
                            },
                          ]}
                        >
                          <div className="fl-application-modal-intro">
                            <strong>{text(p.title)}</strong>
                            <span>{text(p.client_display_name)}</span>
                          </div>
                          {selectedCvId && (
                            <Notice>
                              CV đã chọn: {text(availableCvs.find((item) => text(item.id) === selectedCvId)?.title)}
                            </Notice>
                          )}
                        </Action>
                      </>
                    )}
                  {own && (
                    <>
                      <div className="fl-divider" />
                      <Action
                        disabled={
                          !["APPROVED", "IN_PROGRESS"].includes(text(p.status))
                        }
                        label="Yêu cầu mở rộng dự án"
                        path={`/freelance-projects/${id}/expansions`}
                        fields={[
                          {
                            name: "budget_amount",
                            label: "Trần ngân sách mới (₫)",
                            type: "money",
                          },
                          {
                            name: "max_students",
                            label: "Số sinh viên tối đa mới",
                            type: "number",
                            min: 1,
                          },
                          ...reason,
                        ]}
                      />
                      <Action
                        disabled={[
                          "COMPLETED",
                          "CANCELLED",
                          "CLOSED",
                          "REJECTED",
                        ].includes(text(p.status))}
                        label="Đóng dự án"
                        path={`/freelance-projects/${id}/close`}
                      />
                      <Action
                        disabled={
                          !["DRAFT", "APPROVED"].includes(text(p.status))
                        }
                        label="Hủy dự án"
                        danger
                        path={`/freelance-projects/${id}/cancel`}
                      />
                    </>
                  )}
                  {admin && p.status === "PENDING_REVIEW" && (
                    <div className="fl-actions">
                      {["approve", "request-revision", "reject"].map((a, i) => (
                        <Action
                          key={a}
                          label={["Phê duyệt", "Yêu cầu bổ sung", "Từ chối"][i]}
                          path={`/admin/freelance-projects/${id}/${a}`}
                          fields={a === "approve" ? [] : reason}
                          danger={a === "reject"}
                        />
                      ))}
                    </div>
                  )}
                </Panel>
              </aside>
            </div>
          )}
          {tab === "applications" && (
            <Panel title="Hồ sơ ứng viên">
              <List
                path={`/freelance-projects/${id}/applications`}
                columns={[
                  { key: "student_name", label: "Sinh viên", render: (r) => <span style={{ display: 'flex', alignItems: 'center', gap: 9 }}><UserAvatar userId={text(r.student_user_id)} name={text(r.student_name)} />{text(r.student_name)}</span> },
                  { key: "proposal", label: "Đề xuất" },
                  amountColumn("quoted_amount", "Mức giá"),
                  { key: "estimated_days", label: "Số ngày" },
                  applicationStatusColumn,
                ]}
                actions={(a) =>
                  own &&
                  ["SUBMITTED", "SHORTLISTED"].includes(text(a.status)) ? (
                    <>
                      {a.cv_download_url && (
                        <button
                          className="fl-button secondary"
                          onClick={() => void downloadPath(text(a.cv_download_url), `cv-${text(a.student_name, text(a.student_id))}`).catch((err) => setDownloadError(errorText(err)))}
                        >
                          Mở CV
                        </button>
                      )}
                      <Action
                        disabled={a.status === "SHORTLISTED"}
                        label="Cân nhắc"
                        path={`/freelance-applications/${a.id}/shortlist`}
                      />
                      <Action
                        label="Từ chối"
                        path={`/freelance-applications/${a.id}/reject`}
                        danger
                      />
                      <Action
                        label="Chọn sinh viên"
                        path={`/freelance-projects/${id}/select`}
                        body={{ application_id: a.id }}
                        fields={[
                          {
                            name: "allocated_amount",
                            label: "Ngân sách phân bổ hợp đồng (₫)",
                            type: "money",
                            min: 2001,
                            hint: "Số tiền ký quỹ phải lớn hơn 2.000 ₫.",
                            initial: text(a.quoted_amount, ""),
                          },
                        ]}
                        onDone={(r) =>
                          navigate(`${base}/contracts/${r.contract_id ?? r.id}`)
                        }
                      >
                        <Notice>
                          Tạo hợp đồng riêng cho sinh viên #{text(a.student_id)}
                          . Chọn người chưa tự động ký hợp đồng hoặc chuyển
                          tiền.
                        </Notice>
                      </Action>
                    </>
                  ) : null
                }
              />
            </Panel>
          )}
          {tab === "contracts" && (
            <Panel
              title={
                student ? "Hợp đồng của bạn" : "Hợp đồng riêng từng sinh viên"
              }
            >
              <List
                path={`/freelance-projects/${id}/contracts`}
                columns={[
                  { key: "id", label: "Hợp đồng" },
                  { key: "student_name", label: "Sinh viên" },
                  statusColumn,
                ]}
                actions={(r) => (
                  <Link to={`${base}/contracts/${r.id}`}>Mở hợp đồng →</Link>
                )}
              />
            </Panel>
          )}
        </>
      )}
    </>
  );
}

export function WorkList() {
  const base = useBase();
  const [tab, setTab] = useState("contracts");
  const { user } = useAuth();
  return (
    <>
      <PageHeading
        title="Công việc & hợp đồng của tôi"
        subtitle="Theo dõi riêng từng hợp đồng và các bước hợp tác tiếp theo."
      />
      <div className="fl-tabs">
        <button
          className={tab === "contracts" ? "active" : ""}
          onClick={() => setTab("contracts")}
        >
          Hợp đồng
        </button>
        {user?.role === "STUDENT" && (
          <button
            className={tab === "applications" ? "active" : ""}
            onClick={() => setTab("applications")}
          >
            Đơn ứng tuyển
          </button>
        )}
      </div>
      <Panel>
        {tab === "contracts" ? (
          <List
            path="/freelancer/contracts"
            columns={[
              { key: "project_title", label: "Dự án" },
              { key: "student_name", label: "Sinh viên" },
              { key: "client_email", label: "Người thuê" },
              statusColumn,
            ]}
            actions={(r) => (
              <Link
                className="fl-button secondary"
                to={`${base}/contracts/${r.id}`}
              >
                Mở hợp đồng
              </Link>
            )}
          />
        ) : (
          <List
            path="/freelance-applications/me"
            columns={[
              { key: "project_id", label: "Dự án" },
              { key: "proposal", label: "Đề xuất" },
              amountColumn("quoted_amount"),
              applicationStatusColumn,
            ]}
            actions={(r) => (
              <>
                <Link to={`${base}/projects/${r.project_id}`}>Xem dự án</Link>
                {["SUBMITTED", "SHORTLISTED"].includes(text(r.status)) && (
                  <Action
                    label="Rút đơn"
                    path={`/freelance-applications/${r.id}/withdraw`}
                    danger
                  />
                )}
              </>
            )}
          />
        )}
      </Panel>
    </>
  );
}
