import { beforeEach, describe, expect, it, vi } from "vitest";
import { session } from "@/features/auth/lib/session";

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
}));
vi.mock("@/lib/http", () => ({ http: mocks }));
import { command, inputTimestamp, localInput, money, unwrap } from "./api";
import { normalizePhone } from "./forms";

beforeEach(() => {
  session.clear();
  mocks.request.mockReset();
});

describe("Freelancer money and provider requests", () => {
  it("keeps unchanged UTC deadlines and subsecond precision when editing terms", () => {
    expect(inputTimestamp("2027-04-12T10:30:45.123456")).toBe(
      "2027-04-12T10:30:45.123456Z",
    );
    expect(inputTimestamp(localInput("2027-04-12T10:30:00Z"))).toBe(
      "2027-04-12T10:30:00.000Z",
    );
  });
  it("normalizes local Vietnamese phones without rewriting international numbers", () => {
    expect(normalizePhone("0912 345 678")).toBe("+84912345678");
    expect(normalizePhone("+1 (212) 555-1234")).toBe("+12125551234");
    expect(normalizePhone("bad-number")).toBe("badnumber");
  });
  it("preserves integer VND above JavaScript safe number precision", () => {
    expect(money("9007199254740993")).toContain("9.007.199.254.740.993");
    expect(money("1.5")).toBe("—");
  });
  it("retains an idempotency key after an unknown POST outcome", async () => {
    mocks.request.mockRejectedValueOnce(new Error("network outcome unknown"));
    await expect(command("/milestones/601/payment-orders")).rejects.toThrow(
      "unknown",
    );
    const key = mocks.request.mock.calls[0][0].headers["Idempotency-Key"];
    mocks.request.mockResolvedValueOnce({ data: { data: { id: "7" } } });
    await expect(command("/milestones/601/payment-orders")).resolves.toEqual({
      id: "7",
    });
    expect(mocks.request.mock.calls[1][0].headers["Idempotency-Key"]).toBe(key);
  });
  it("coalesces double submissions into one in-flight instruction", async () => {
    let finish: (value: unknown) => void = () => {};
    mocks.request.mockReturnValueOnce(
      new Promise((resolve) => {
        finish = resolve;
      }),
    );
    const first = command("/milestones/601/accept", { deliverable_id: "50" });
    const second = command("/milestones/601/accept", { deliverable_id: "50" });
    expect(first).toBe(second);
    expect(mocks.request).toHaveBeenCalledTimes(1);
    finish({ data: { id: "1" } });
    await first;
  });
  it("does not deliver the previous account response after identity changes", async () => {
    let finish: (value: unknown) => void = () => {};
    mocks.request.mockReturnValueOnce(
      new Promise((resolve) => {
        finish = resolve;
      }),
    );
    const result = command("/bank-destinations", { account_number: "123456" });
    session.clear();
    finish({ data: { data: { id: "private-old-account" } } });
    await expect(result).rejects.toMatchObject({ code: "SESSION_CHANGED" });
  });
  it("round-trips backend UTC timestamps through local datetime inputs", () => {
    const input = localInput("2027-04-12T10:30:00Z");
    expect(new Date(input).getTime()).toBe(Date.UTC(2027, 3, 12, 10, 30));
    expect(localInput("2027-04-12T10:30:00")).toBe(input);
  });
  it("reads both resource envelopes and legacy typed resources", () => {
    expect(unwrap({ data: { id: "10" } })).toEqual({ id: "10" });
    expect(unwrap({ id: "10" })).toEqual({ id: "10" });
  });
});
