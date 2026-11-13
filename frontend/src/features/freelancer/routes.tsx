import { useRead } from "./hooks";
import { lazy } from "react";
import {
  Navigate,
  Outlet,
  useLocation,
  useSearchParams,
} from "react-router-dom";
import type { RouteObject } from "react-router-dom";
import { useAuth, roleHome } from "@/features/auth";
import { unwrap } from "./api";
import { LoadingError, Notice } from "./ui";
import "./freelancer.css";

const Finance = lazy(() =>
  import("./OverviewStats").then((m) => ({ default: m.FinanceHome })),
);
const Overview = lazy(() =>
  import("./Projects").then((m) => ({ default: m.Overview })),
);
const Projects = lazy(() =>
  import("./Projects").then((m) => ({ default: m.Projects })),
);
const ProjectDetail = lazy(() =>
  import("./Projects").then((m) => ({ default: m.ProjectDetail })),
);
const ProjectEditor = lazy(() =>
  import("./Projects").then((m) => ({ default: m.ProjectEditor })),
);
const Work = lazy(() =>
  import("./Projects").then((m) => ({ default: m.WorkList })),
);
const Contract = lazy(() =>
  import("./Contracts").then((m) => ({ default: m.ContractDetail })),
);
const Milestone = lazy(() =>
  import("./Contracts").then((m) => ({ default: m.MilestoneDetail })),
);
const Fund = lazy(() =>
  import("./Contracts").then((m) => ({ default: m.FundingPage })),
);
const Payment = lazy(() =>
  import("./Contracts").then((m) => ({ default: m.PaymentResult })),
);
const Settlement = lazy(() =>
  import("./Contracts").then((m) => ({ default: m.SettlementDetail })),
);
const Banks = lazy(() =>
  import("./Accounts").then((m) => ({ default: m.Banks })),
);
const Onboarding = lazy(() =>
  import("./Accounts").then((m) => ({ default: m.Onboarding })),
);
const Dispute = lazy(() =>
  import("./Accounts").then((m) => ({ default: m.DisputeDetail })),
);
const Admin = lazy(() =>
  import("./Admin").then((m) => ({ default: m.AdminPage })),
);
export const RegisterClientPage = lazy(() =>
  import("./Accounts").then((m) => ({ default: m.RegisterClient })),
);

function Layout() {
  const location = useLocation();
  return (
    <section className="fl">
      <Outlet key={location.pathname} />
    </section>
  );
}
export function freelancerRoutes(admin = false): RouteObject[] {
  return [
    {
      path: "freelancer",
      element: <Layout />,
      children: [
        { index: true, element: <Overview /> },
        { path: "projects", element: <Projects /> },
        { path: "projects/new", element: <ProjectEditor /> },
        { path: "projects/:id", element: <ProjectDetail /> },
        { path: "projects/:id/edit", element: <ProjectEditor /> },
        { path: "work", element: <Work /> },
        { path: "contracts/:id", element: <Contract /> },
        { path: "milestones/:id", element: <Milestone /> },
        { path: "milestones/:id/fund", element: <Fund /> },
        { path: "payments/:id", element: <Payment /> },
        { path: "settlements/:id", element: <Settlement /> },
        { path: "finance", element: <Finance /> },
        { path: "banks", element: <Banks /> },
        { path: "onboarding", element: <Onboarding /> },
        { path: "disputes/:id", element: <Dispute /> },
        ...(admin
          ? [{
              path: "admin/treasury",
              element: <Navigate to="../admin/transfers" replace />,
            }]
          : []),
        ...(admin
          ? [
              "business",
              "projects",
              "banks",
              "receipts",
              "transfers",
              "disputes",
              "reconciliation",
            ].map((section) => ({
              path: "admin/" + section,
              element: <Admin section={section} key={section} />,
            }))
          : []),
      ],
    },
  ];
}

export function PaymentReturn() {
  const [params] = useSearchParams();
  const code = params.get("orderCode");
  const { user } = useAuth();
  const q = useRead(
    `/payment-orders/by-code/${encodeURIComponent(code ?? "")}`,
    Boolean(code && /^[0-9]+$/.test(code)),
  );
  const p = unwrap(q.data);
  if (p.id && user)
    return (
      <Navigate
        to={`${roleHome[user.role]}/freelancer/payments/${p.id}`}
        replace
      />
    );
  return (
    <main className="fl fl-result">
      <h1>Kiểm tra kết quả thanh toán</h1>
      {code && /^[0-9]+$/.test(code) ? (
        <LoadingError query={q} />
      ) : (
        <Notice>
          Không có mã yêu cầu hợp lệ. Hãy mở hợp đồng và lịch sử ký quỹ để xem
          trạng thái.
        </Notice>
      )}
    </main>
  );
}
