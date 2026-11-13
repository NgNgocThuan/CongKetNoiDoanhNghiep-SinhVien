import { Badge } from "./ui";
import type { Column } from "./ui";
import { money, date } from "./api";
export const statusColumn: Column = {
  key: "status",
  label: "Trạng thái",
  render: (r) => <Badge value={r.status} />,
};
export const applicationStatusColumn: Column = {
  key: "status",
  label: "Trạng thái",
  render: (r) => (
    <Badge value={r.status === "SUBMITTED" ? "Đã ứng tuyển" : r.status} />
  ),
};
export const amountColumn = (key = "amount", label = "Số tiền"): Column => ({
  key,
  label,
  render: (r) => money(r[key]),
});
export const dateColumn: Column = {
  key: "created_at",
  label: "Thời gian",
  render: (r) => date(r.created_at),
};
