import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { http } from "@/lib/http";
import { session } from "@/features/auth/lib/session";
import { ApiError } from "@/lib/api-error";
import { text, unwrap } from "./api";
import type { Row } from "./api";
import { errorText } from "./messages";
import { Notice } from "./ui";

export default function BankInspection({ id }: { id: string }) {
  const [value, setValue] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function inspect(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    const identity = session.identity;
    const reason = "Tra cứu tài khoản nhận tiền của người dùng";
    const request = new AbortController();
    controller.current = request;
    setError("");
    setBusy(true);
    try {
      const response = await http.post(
        `/admin/bank-destinations/${id}/verification-data`,
        { reason },
        { signal: request.signal },
      );
      if (session.identity !== identity)
        throw new ApiError("Session changed", 401, "SESSION_CHANGED");
      if (!request.signal.aborted) setValue(unwrap(response.data));
    } catch (err) {
      if (!request.signal.aborted) setError(errorText(err));
    } finally {
      if (!request.signal.aborted) setBusy(false);
    }
  }
  return (
    <details
      className="fl-section-footer"
      onToggle={(e) => {
        if (!e.currentTarget.open) {
          controller.current?.abort();
          setValue(null);
          setBusy(false);
        }
      }}
    >
      <summary>Xem số tài khoản đầy đủ</summary>
      <p>
        Lượt tra cứu được ghi lại trong lịch sử quản trị.
      </p>
      <form onSubmit={(e) => void inspect(e)}>
        <button className="fl-button secondary" disabled={busy}>
          {busy ? "Đang mở…" : "Xem thông tin tài khoản"}
        </button>
      </form>
      {error && <Notice danger>{error}</Notice>}
      {value && (
        <Notice>
          <strong>{text(value.account_name)}</strong>
          <p>
            Ngân hàng: {text(value.bank_bin)}
            <br />
            Số tài khoản: <strong>{text(value.account_number)}</strong>
          </p>
          <button className="fl-link" onClick={() => setValue(null)}>
            Ẩn thông tin
          </button>
        </Notice>
      )}
    </details>
  );
}
