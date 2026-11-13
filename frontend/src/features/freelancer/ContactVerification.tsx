import { useEffect, useId, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { http, publicHttp } from "@/lib/http";
import { obj, text, unwrap } from "./api";
import type { Row } from "./api";
import { errorText } from "./messages";
import { LoadingError, Notice } from "./ui";

// Read persisted timestamps on every visit, including limited onboarding sessions.
export default function ContactVerification({ token }: { token?: string }) {
  const instance = useId();
  const client = useQueryClient();
  const queryKey = ["freelancer", "contact-verification", instance];
  const request = async (path: string, body?: Row, signal?: AbortSignal) =>
    unwrap(
      (
        await (token ? publicHttp : http).request({
          url: path,
          method: body ? "POST" : "GET",
          data: body,
          signal,
          ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
        })
      ).data,
    );
  const q = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const data = await request(
        "/auth/verification-status",
        undefined,
        signal,
      );
      return { ...data, receivedAt: Date.now() };
    },
    gcTime: 0,
    retry: false,
  });
  const state = obj(q.data);
  const contacts = obj(state.contacts);
  const refresh = async () => {
    await client.invalidateQueries({ queryKey: ["freelancer"] });
    // Throw on an unreadable status so the last successful send is not discarded.
    await q.refetch({ throwOnError: true });
  };
  return (
    <div className="fl-contact-list">
      <LoadingError query={q} />
      {q.data &&
        ["EMAIL"].map((channel) => (
          <ContactCard
            key={`${channel}:${text(obj(contacts[channel]).identifier)}`}
            channel={channel}
            contact={obj(contacts[channel])}
            serverTime={text(state.server_time, "")}
            receivedAt={Number(state.receivedAt)}
            request={request}
            refresh={refresh}
          />
        ))}
    </div>
  );
}

function ContactCard({
  channel,
  contact,
  serverTime,
  receivedAt,
  request,
  refresh,
}: {
  channel: string;
  contact: Row;
  serverTime: string;
  receivedAt: number;
  request: (path: string, body?: Row) => Promise<Row>;
  refresh: () => Promise<unknown>;
}) {
  const label = "Email";
  const identifier = text(contact.identifier, "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState<Row | null>(null);
  const [completed, setCompleted] = useState(false);
  const [tick, setTick] = useState(Date.now());
  const input = useRef<HTMLInputElement>(null);
  const running = useRef(false);
  const challenge = sent ?? obj(contact.challenge);
  const verified = contact.verified === true || completed;
  const now = Date.parse(serverTime) + (tick - receivedAt);
  const seconds = (value: unknown) =>
    Math.max(0, Math.ceil((Date.parse(text(value, "")) - now) / 1000)) || 0;
  const expires = seconds(challenge.expires_at);
  const cooldown = seconds(challenge.resend_after);
  const active =
    Boolean(challenge.challenge_id) &&
    challenge.status === "PENDING" &&
    expires > 0 &&
    Number(challenge.attempts_left) > 0;
  useEffect(() => {
    if (verified || !challenge.challenge_id) return;
    const timer = window.setInterval(() => setTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [verified, challenge.challenge_id]);
  useEffect(() => {
    if (active && !busy) input.current?.focus();
  }, [active, busy, challenge.challenge_id]);
  async function perform(verify: boolean) {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError("");
    try {
      const payload = { channel, identifier, purpose: "VERIFY_CONTACT" };
      const result = await request(
        verify
          ? `/auth/verifications/${challenge.challenge_id}/verify`
          : "/auth/verifications",
        verify ? { ...payload, code } : payload,
      );
      if (verify) {
        if (result.verified !== true)
          throw new Error(
            "Chưa nhận được kết quả xác minh. Hãy cập nhật trạng thái.",
          );
        setCompleted(true);
        setCode("");
        setSent(null);
      } else {
        setSent({ ...result, status: "PENDING" });
        setCode("");
        setTick(Date.now());
      }
      try {
        await refresh();
        setSent(null);
      } catch {
        setError(
          "Thao tác đã thành công nhưng chưa tải lại được trạng thái. Bạn vẫn có thể dùng mã vừa nhận; thử tải lại khi kết nối ổn định.",
        );
      }
    } catch (err) {
      setError(errorText(err));
      // A rejected/expired code updates attempts and state on the server.
      setSent(null);
      await refresh().catch(() => undefined);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  return (
    <section
      className="fl-contact-card"
      aria-label={`Xác minh ${label.toLowerCase()}`}
    >
      <div className="fl-contact-heading">
        <div>
          <strong>{label}</strong>
          <p>{identifier || "Chưa có thông tin liên hệ"}</p>
        </div>
        {verified ? (
          <span className="fl-badge good" role="status">
            <CheckCircle2 size={16} /> Đã xác minh
          </span>
        ) : (
          <span className="fl-badge">Chưa xác minh</span>
        )}
      </div>
      {completed && (
        <p role="status">Đã xác minh {label.toLowerCase()} thành công.</p>
      )}
      {!verified && identifier && (
        <>
          {active && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void perform(true);
              }}
            >
              <p>Mã đã gửi đến {identifier}. Nhập mã bên dưới để hoàn tất.</p>
              <label className="fl-otp-label">
                Mã OTP {label.toLowerCase()}
                <input
                  ref={input}
                  value={code}
                  onChange={(e) =>
                    setCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  placeholder="Nhập 6 chữ số"
                  disabled={busy}
                />
              </label>
              <p className="fl-muted">
                Mã hết hạn sau {Math.floor(expires / 60)}:
                {String(expires % 60).padStart(2, "0")} · Còn{" "}
                {text(challenge.attempts_left)} lần thử
              </p>
              <button
                className="fl-button"
                disabled={busy || code.length !== 6}
              >
                {busy ? "Đang xử lý…" : `Xác nhận ${label.toLowerCase()}`}
              </button>
            </form>
          )}
          {Boolean(challenge.challenge_id) && !active && (
            <Notice>
              Mã đã hết hạn hoặc không còn sử dụng được. Hãy yêu cầu mã mới.
            </Notice>
          )}
          <button
            type="button"
            className="fl-button secondary"
            disabled={busy || cooldown > 0}
            onClick={() => void perform(false)}
          >
            {busy
              ? "Đang xử lý…"
              : cooldown > 0
                ? `Gửi lại sau ${cooldown}s`
                : challenge.challenge_id
                  ? "Gửi lại mã"
                  : `Gửi mã xác minh ${label.toLowerCase()}`}
          </button>
        </>
      )}
      {!identifier && (
        <p>
          Cập nhật {label.toLowerCase()} trong phần thông tin liên hệ để xác
          minh.
        </p>
      )}
      {error && <Notice danger>{error}</Notice>}
    </section>
  );
}
