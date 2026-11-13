import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth";
import { money, text, unwrap } from "./api";
import { useBase, useRead } from "./hooks";
import { List, LoadingError, PageHeading, Panel, Stats } from "./ui";
import { statusColumn } from "./columns";

export function OverviewStats() {
  const { user } = useAuth();
  const q = useRead("/freelancer/overview");
  const v = unwrap(q.data);
  const fields =
    user?.role === "ADMIN"
      ? [
          ["pending_verifications", "Pháp nhân chờ duyệt"],
          ["pending_projects", "Dự án chờ duyệt"],
          ["waiting_bank_transfers", "Khoản chi chờ bổ sung ngân hàng"],
          ["open_disputes", "Tranh chấp đang mở"],
        ]
      : user?.role === "STUDENT"
        ? [
            ["project_count", "Dự án đang tham gia"],
            ["active_contracts", "Hợp đồng đang làm"],
            ["work_milestones", "Mốc cần hoàn thành"],
            ["review_milestones", "Bản nộp chờ nghiệm thu"],
          ]
        : [
            ["project_count", "Dự án của tôi"],
            ["active_contracts", "Hợp đồng đang làm"],
            ["unfunded_milestones", "Mốc cần ký quỹ"],
            ["review_milestones", "Mốc chờ nghiệm thu"],
          ];
  return (
    <>
      <LoadingError query={q} />
      {!q.isPending && !q.isError && (
        <Stats
          data={fields.map(([key, label]) => [label, text(v[key], "0")])}
        />
      )}
    </>
  );
}
export function FinanceHome() {
  const base = useBase();
  const q = useRead("/freelancer/overview");
  const v = unwrap(q.data);
  return (
    <>
      <PageHeading
        title="Ký quỹ & lịch sử thanh toán"
        subtitle="Tiền được theo dõi theo hợp đồng và từng mốc công việc."
      />
      <LoadingError query={q} />
      {!q.isPending && !q.isError && (
        <Stats
          data={[
            ["Đã ký quỹ", money(v.funded_amount)],
            ["Đang giữ", money(v.held_amount)],
            ["Trong đó đang xử lý chi", money(v.reserved_amount)],
            ["Đã giải ngân (gộp phí)", money(v.released_gross)],
            ["Đã hoàn người thuê", money(v.refunded_amount)],
          ]}
        />
      )}
      <Panel title="Thanh toán theo hợp đồng">
        <p>
          Khoản đang xử lý chi nằm trong tiền đang giữ. Phần thực nhận và phí
          được thể hiện trong quyết toán từng mốc.
        </p>
        <List
          path="/freelancer/contracts"
          columns={[
            { key: "project_title", label: "Dự án" },
            { key: "student_name", label: "Sinh viên" },
            statusColumn,
          ]}
          actions={(r) => (
            <Link
              className="fl-button secondary"
              to={`${base}/contracts/${r.id}?tab=finance`}
            >
              Xem ký quỹ & giao dịch
            </Link>
          )}
        />
      </Panel>
    </>
  );
}
