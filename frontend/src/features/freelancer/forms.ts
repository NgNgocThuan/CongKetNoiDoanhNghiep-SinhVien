import type { Row } from "./api";
export interface Field {
  name: string;
  label: string;
  type?:
    | "text"
    | "textarea"
    | "number"
    | "datetime-local"
    | "date"
    | "email"
    | "password"
    | "checkbox"
    | "select"
    | "money";
  required?: boolean;
  options?: [string, string][];
  initial?: string | boolean;
  min?: string | number;
  max?: string | number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  hint?: string;
  onChange?: (value: string) => void;
}
export function normalizePhone(value: string) {
  const compact = value.replace(/[\s().-]/g, "");
  return /^0\d{9}$/.test(compact) ? "+84" + compact.slice(1) : compact;
}
export function formBody(form: HTMLFormElement, fields: Field[]): Row {
  const d = new FormData(form);
  const r: Row = {};
  fields.forEach((f) => {
    const value = d.get(f.name);
    if (f.type === "money" && value !== "" && value !== null) {
      const amount = Number(value);
      if (!Number.isSafeInteger(amount) || amount < Number(f.min ?? 0))
        throw new Error(
          f.min ? `${f.label} phải từ ${Number(f.min).toLocaleString("vi-VN")} ₫.` : `${f.label} không hợp lệ.`,
        );
    }
    if (f.type === "checkbox") r[f.name] = value === "on";
    else if (value !== "" && value !== null)
      r[f.name] =
        f.type === "number"
          ? Number(value)
          : f.type === "datetime-local" || f.type === "date"
            ? new Date(String(value)).toISOString()
            : f.name === "phone"
              ? normalizePhone(String(value))
              : String(value);
  });
  return r;
}
export const reason: Field[] = [
  { name: "reason", label: "Lý do / nội dung xác nhận", type: "textarea" },
];
