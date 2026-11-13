import { http } from "@/lib/http";
import { ApiError, toApiError } from "@/lib/api-error";
import { session } from "@/features/auth/lib/session";

export interface Row {
  [key: string]: unknown;
  id?: string | number;
}
export interface Page {
  items: Row[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
export const text = (value: unknown, fallback = "—"): string =>
  value == null || value === "" ? fallback : String(value);
export const obj = (value: unknown): Row =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Row)
    : {};
export const rows = (value: unknown): Row[] =>
  Array.isArray(value) ? value.map(obj) : [];
export const unwrap = (value: unknown): Row => {
  const r = obj(value);
  return "data" in r ? obj(r.data) : r;
};
export function money(value: unknown) {
  try {
    return (
      new Intl.NumberFormat("vi-VN").format(BigInt(String(value ?? 0))) + " ₫"
    );
  } catch {
    return "—";
  }
}
function utc(value: unknown) {
  const s = String(value);
  return /^\d{4}-\d{2}-\d{2}T/.test(s) && !/(Z|[+-]\d\d:\d\d)$/i.test(s)
    ? s + "Z"
    : s;
}
export const date = (v: unknown) =>
  v ? new Date(utc(v)).toLocaleString("vi-VN") : "—";
export function localInput(value: unknown) {
  const s = text(value, "");
  if (!s || s.length === 16) return s;
  const d = new Date(utc(s));
  if (!Number.isFinite(d.getTime())) return "";
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
// Datetime controls contain local minutes; unchanged API dates may be naive UTC
// with seconds/microseconds. Keep their precision when editing locked terms.
export function inputTimestamp(value: unknown) {
  const s = text(value, "");
  if (s.length === 16) return new Date(s).toISOString();
  const normalized = utc(s);
  if (!s || !Number.isFinite(new Date(normalized).getTime()))
    throw new Error("Thời hạn không hợp lệ.");
  return normalized;
}
export const api = {
  get: async (path: string, signal?: AbortSignal): Promise<unknown> =>
    (await http.get(path, { signal })).data,
  resource: async (path: string): Promise<Row> => unwrap(await api.get(path)),
};
// Retain the same key on uncertain errors. Never turn a timeout into a new financial instruction.
const pending = new Map<string, string>();
const active = new Map<string, Promise<Row>>();
export function command(
  path: string,
  body: Row = {},
  method = "POST",
): Promise<Row> {
  const identity = session.identity;
  const fingerprint = `${identity}:${method}:${path}:${JSON.stringify(body)}`;
  const existing = active.get(fingerprint);
  if (existing) return existing;
  const key = pending.get(fingerprint) ?? crypto.randomUUID();
  pending.set(fingerprint, key);
  const promise = http
    .request({
      url: path,
      method,
      data: body,
      headers: { "Idempotency-Key": key },
    })
    .then(({ data }) => {
      if (identity !== session.identity)
        throw new ApiError("Session changed", 401, "SESSION_CHANGED");
      pending.delete(fingerprint);
      return unwrap(data);
    })
    .catch((err) => {
      // A timeout or server error may arrive after commit: retry the same instruction.
      const { status } = toApiError(err);
      if (status !== null && status >= 400 && status < 500 && status !== 408)
        pending.delete(fingerprint);
      throw err;
    })
    .finally(() => active.delete(fingerprint));
  active.set(fingerprint, promise);
  return promise;
}
export async function upload(file: File, category: string) {
  const body = new FormData();
  body.append("file", file);
  body.append("category", category);
  return unwrap((await http.post("/files", body)).data);
}
export async function download(id: unknown, preferredName?: string) {
  const { data, headers } = await http.get<Blob>(
    `/files/${encodeURIComponent(text(id))}/download`,
    {
      responseType: "blob",
      // The shared API client uses a short timeout suitable for JSON calls.
      // Product archives and office documents need more time to stream.
      timeout: 120_000,
    },
  );
  // Axios normally returns a Blob here.  Normalise it explicitly because some
  // browser/adapter combinations return an ArrayBuffer-like value instead and
  // URL.createObjectURL then throws, which used to be reported as a network
  // failure even though the server had returned 200.
  const contentType = String(headers["content-type"] || "application/octet-stream");
  const blob = data instanceof Blob ? data : new Blob([data], { type: contentType });
  if (!blob.size) throw new Error("Máy chủ trả về tệp rỗng. Vui lòng thử lại.");

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = preferredName || `tai-lieu-${text(id)}`;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Keep the object URL alive long enough for Chrome/Edge to start a large
  // download, including when DevTools device emulation is enabled.
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

export async function downloadPath(path: string, preferredName?: string) {
  const { data, headers } = await http.get<Blob>(path.replace(/^\/api\/v1/, ""), {
    responseType: "blob",
    timeout: 120_000,
  });
  const contentType = String(headers["content-type"] || "application/octet-stream");
  const blob = data instanceof Blob ? data : new Blob([data], { type: contentType });
  if (!blob.size) throw new Error("Máy chủ trả về tệp rỗng. Vui lòng thử lại.");
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = preferredName || "cv-ung-vien";
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}
