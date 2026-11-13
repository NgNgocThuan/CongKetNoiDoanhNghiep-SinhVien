import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const paged = (items: unknown[]) => ({
  items,
  total: items.length,
  page: 1,
  pages: 1,
  size: 20,
});

test('first project requires scrolling escrow terms, persists consent and preserves guide drafts', async ({ page }) => {
  await fixture(page);
  let accepted = false;
  let accepts = 0;
  await page.route('**/api/v1/auth/escrow-terms', async route => {
    if (route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toEqual({ accepted: true, version: '2026-11-12' });
      accepted = true; accepts++;
    }
    await route.fulfill({ json: { data: { has_accepted_escrow_terms: accepted, review_period_seconds: 604800 } } });
  });
  await page.goto('/client/freelancer/projects/new');
  const agree = page.getByRole('button', { name: 'Tôi đã đọc, hiểu rõ và đồng ý với điều khoản' });
  await expect(agree).toBeDisabled();
  await page.getByLabel('Điều khoản ký quỹ', { exact: true }).evaluate(el => { el.scrollTop = el.scrollHeight; el.dispatchEvent(new Event('scroll')); });
  await expect(agree).toBeEnabled();
  await agree.click();
  await page.getByLabel('Tên dự án', { exact: true }).fill('Giữ nguyên bản nháp của tôi');
  await page.getByRole('button', { name: /Xem hướng dẫn & dự án mẫu/ }).click();
  await page.getByRole('button', { name: 'Văn phòng / Dữ liệu', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('2.000');
  await page.getByRole('button', { name: 'Đã hiểu & Đóng' }).click();
  await expect(page.getByLabel('Tên dự án', { exact: true })).toHaveValue('Giữ nguyên bản nháp của tôi');
  await page.reload();
  await expect(page.getByLabel('Tên dự án', { exact: true })).toBeVisible();
  await expect(agree).toHaveCount(0);
  expect(accepts).toBe(1);
});

test('new skill tags use persisted ids, support Enter and comma and can be removed', async ({ page }) => {
  const { writes } = await fixture(page);
  await page.route('**/api/v1/catalog/skill-tags', async route => route.fulfill({ json: { id: '92', name: route.request().postDataJSON().name, category: 'OTHER', is_active: true } }));
  await page.goto('/client/freelancer/projects/new');
  await page.getByLabel('Tên dự án', { exact: true }).fill('Dự án kỹ năng mới');
  const input = page.getByLabel('Tìm hoặc thêm kỹ năng');
  await input.fill('Prompt Engineering');
  await input.press('Enter');
  await expect(page.locator('.ux-tag')).toContainText('Prompt Engineering');
  await page.getByRole('button', { name: 'Xóa Prompt Engineering' }).click();
  await expect(page.locator('.ux-tag')).toHaveCount(0);
  await input.fill('Prompt Engineering');
  await input.press(',');
  await expect(page.locator('.ux-tag')).toHaveCount(1);
  await page.getByRole('button', { name: 'Lưu bản nháp', exact: true }).click();
  await expect(page).toHaveURL(/projects\/101$/);
  expect(writes.find(w => w.path === '/freelance-projects')?.body.skill_ids).toEqual(['92']);
});

test('bank picker searches short code and submits BIN invisibly', async ({ page }) => {
  const { writes } = await fixture(page);
  await page.route('**/api/v1/finance/banks', route => route.fulfill({ json: [
    { bin: '970422', code: 'MB', shortName: 'MBBank', name: 'Ngân hàng Quân đội', logo: '' },
    { bin: '970436', code: 'VCB', shortName: 'Vietcombank', name: 'Ngân hàng Ngoại thương', logo: '' },
  ] }));
  await page.goto('/client/freelancer/banks');
  await page.getByRole('button', { name: 'Thêm tài khoản ngân hàng', exact: true }).click();
  await page.getByLabel('Tìm ngân hàng').fill('mb');
  await page.getByRole('button', { name: /MBBank/ }).click();
  await page.getByLabel('Số tài khoản', { exact: true }).fill('00123456789');
  await page.getByLabel('Tên chủ tài khoản', { exact: true }).fill('Nguyễn Văn An');
  await page.getByRole('button', { name: 'Lưu tài khoản', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(writes.find(w => w.path === '/bank-destinations')?.body).toEqual({ bank_bin: '970422', account_number: '00123456789', account_name: 'NGUYEN VAN AN' });
});

test('sidebar order stays stable across routes and active groups expand', async ({ page }) => {
  await fixture(page, 'COMPANY');
  await page.goto('/company/freelancer/projects');
  const titles = page.locator('.sidebar-group-title');
  await expect(titles).toHaveCount(3);
  const order = await titles.allTextContents();
  await page.getByRole('button', { name: 'Dự án Freelancer', exact: true }).click();
  await expect(page.locator('#nav-freelancer')).toBeHidden();
  await page.goto('/company/freelancer/finance');
  await expect(page.locator('#nav-freelancer')).toBeVisible();
  expect(await titles.allTextContents()).toEqual(order);
  await page.screenshot({ path: 'test-results/ux-sidebar-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/company/freelancer/projects/new');
  await expect(page.getByLabel('Tên dự án', { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/ux-project-mobile.png', fullPage: true });
});

test('company verification uses real DTO fields, recovers from 409 and fits mobile', async ({ page }) => {
  const { errors } = await fixture(page, 'COMPANY');
  await contactFixture(page, { verified: true });
  let submitted = false;
  let attempt = 0;
  await page.route('**/api/v1/company/verification/**', async route => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataBuffer()?.toString() ?? '';
      expect(body).toContain('name="license_file"');
      expect(body).toContain('name="legal_representative"');
      attempt++;
      if (attempt === 1) {
        await route.fulfill({ status: 409, json: { error: { code: 'FILE_NOT_READY', message: 'Tệp đang được kiểm tra, vui lòng thử lại.' } } });
        return;
      }
      submitted = true;
      await route.fulfill({ json: { verification_status: 'PENDING' } });
    } else await route.fulfill({ json: {
      company_id: 1, company_name: 'Công ty Công nghệ Sao Mai', tax_code: '0123456789',
      legal_representative: 'Nguyễn Minh Anh', business_address: '12 Nguyễn Huệ, TP. Hồ Chí Minh',
      email_otp_verified: true, verification_status: 'PENDING', license_file_id: submitted ? 41 : null,
    } });
  });
  await page.route('**/api/v1/company/mou/status', route => route.fulfill({ json: { is_mou_partner: false, hybrid_available: false, status: 'NOT_SUBMITTED' } }));
  await page.goto('/company/freelancer/onboarding');
  await expect(page.getByLabel('Tên doanh nghiệp', { exact: true })).toHaveValue('Công ty Công nghệ Sao Mai');
  await page.getByLabel('Giấy phép kinh doanh', { exact: false }).setInputFiles({ name: 'license.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-test') });
  await page.getByRole('button', { name: 'Gửi hồ sơ để xét duyệt' }).click();
  await expect(page.getByRole('button', { name: 'Gửi hồ sơ để xét duyệt' })).toBeEnabled();
  await expect(page.getByLabel('Tên doanh nghiệp', { exact: true })).toHaveValue('Công ty Công nghệ Sao Mai');
  await expect(page.getByText('1. Xác minh email', { exact: true })).toBeVisible();
  await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); window.scrollTo({ top: 0, behavior: 'instant' }); });
  await page.screenshot({ path: 'test-results/company-verification-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: 'test-results/company-verification-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'Gửi hồ sơ để xét duyệt' }).click();
  await expect(page.getByText('Hồ sơ đã được tiếp nhận', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Gửi hồ sơ để xét duyệt' })).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('paper MOU submits signer and correct file field then hides repeated submission', async ({ page }) => {
  const { errors } = await fixture(page, 'COMPANY');
  await contactFixture(page, { verified: true });
  await page.route('**/api/v1/company/verification/status', route => route.fulfill({ json: { company_name: 'Sao Mai', tax_code: '0123456789', email_otp_verified: true, verification_status: 'VERIFIED' } }));
  let submitted = false;
  await page.route('**/api/v1/company/mou/**', async route => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataBuffer()?.toString() ?? '';
      expect(body).toContain('name="mou_file"');
      expect(body).toContain('name="signer_name"');
      submitted = true;
      await route.fulfill({ json: { status: 'PENDING_REVIEW' } });
    } else await route.fulfill({ json: { is_mou_partner: false, hybrid_available: false, status: submitted ? 'PENDING_REVIEW' : 'NOT_SUBMITTED', agreement_code: 'MOU-41' } });
  });
  await page.goto('/company/freelancer/onboarding');
  await expect(page.getByRole('radio', { name: /Ký số điện tử/ })).toBeDisabled();
  await page.getByLabel('Họ tên người ký', { exact: true }).fill('Nguyễn Minh Anh');
  await page.getByLabel('Chức vụ', { exact: true }).fill('Giám đốc');
  await page.getByLabel('Tài liệu đã ký', { exact: false }).setInputFiles({ name: 'mou.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-test') });
  await page.getByRole('button', { name: 'Gửi thỏa thuận MOU' }).click();
  await expect(page.getByText('Mã thỏa thuận: MOU-41')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Gửi thỏa thuận MOU' })).toHaveCount(0);
  expect(errors).toEqual([]);
});

async function contactFixture(
  page: Page,
  options: { verified?: boolean; limited?: boolean } = {},
) {
  let verified = options.verified ?? false;
  let challenge: Record<string, unknown> | null = null;
  const requests: Record<string, unknown>[] = [];
  let attempts = 5;
  await page.route("**/api/v1/auth/verification**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const body =
      route.request().method() === "POST"
        ? (route.request().postDataJSON() as Record<string, unknown>)
        : {};
    if (route.request().method() === "POST") requests.push(body);
    if (path.endsWith("/verification-status")) {
      await route.fulfill({
        json: {
          data: {
            server_time: new Date().toISOString(),
            contacts: {
              EMAIL: {
                identifier: "client@example.test",
                verified,
                verified_at: verified ? new Date().toISOString() : null,
                challenge: verified ? null : challenge,
              },
            },
          },
        },
      });
    } else if (path.endsWith("/verify")) {
      if (body.code !== "012345") {
        attempts--;
        challenge = { ...challenge, attempts_left: attempts };
        await route.fulfill({
          status: 409,
          json: { error: { code: "OTP_INVALID", message: "Invalid OTP" } },
        });
      } else {
        verified = true;
        await route.fulfill({
          json: { data: { status: "success", verified: true } },
        });
      }
    } else {
      challenge = {
        challenge_id: "3",
        status: "PENDING",
        attempts_left: 5,
        expires_at: new Date(Date.now() + 300_000).toISOString(),
        resend_after: new Date(Date.now() + 60_000).toISOString(),
      };
      await route.fulfill({ json: { data: { ...challenge, status: "sent" } } });
    }
  });
  return requests;
}

test("email OTP opens inline, shows timer, rejects wrong code and persists verified state after reload", async ({
  page,
}) => {
  await fixture(page);
  const requests = await contactFixture(page);
  await page.goto("/client/freelancer/onboarding");
  const card = page.getByRole("region", {
    name: "Xác minh email",
    exact: true,
  });
  await card.getByRole("button", { name: "Gửi mã xác minh email" }).click();
  const code = card.getByLabel("Mã OTP email");
  await expect(code).toBeVisible();
  await expect(code).toBeFocused();
  await page.screenshot({
    path: "test-results/otp-inline.png",
    fullPage: true,
  });
  await expect(card.getByText(/Mã hết hạn sau/)).toBeVisible();
  await expect(
    card.getByRole("button", { name: /Gửi lại sau/ }),
  ).toBeDisabled();
  await code.fill("999999");
  await card
    .getByRole("button", { name: "Xác nhận email", exact: true })
    .click();
  await expect(card.getByRole("alert")).toContainText("Mã xác minh không đúng");
  await expect(card.getByText(/Còn 4 lần thử/)).toBeVisible();
  await code.fill("012345");
  await card
    .getByRole("button", { name: "Xác nhận email", exact: true })
    .click();
  await expect(card.getByText("Đã xác minh", { exact: true })).toBeVisible();
  await expect(code).toHaveCount(0);
  await expect(card.getByRole("button")).toHaveCount(0);
  expect(
    requests.every(
      (r) => r.identifier === "client@example.test" && r.channel === "EMAIL",
    ),
  ).toBe(true);
  await page.reload();
  await expect(card.getByText("Đã xác minh", { exact: true })).toBeVisible();
  await expect(card.getByRole("button")).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "test-results/otp-verified-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("pending OTP resumes after reload and expired codes cannot be submitted", async ({
  page,
}) => {
  await fixture(page);
  await contactFixture(page);
  await page.clock.install();
  await page.goto("/client/freelancer/onboarding");
  const card = page.getByRole("region", {
    name: "Xác minh email",
    exact: true,
  });
  await card.getByRole("button", { name: "Gửi mã xác minh email" }).click();
  await page.reload();
  await expect(card.getByLabel("Mã OTP email")).toBeVisible();
  await page.clock.fastForward(301_000);
  await expect(card.getByLabel("Mã OTP email")).toHaveCount(0);
  await expect(card.getByText(/Mã đã hết hạn/)).toBeVisible();
  await expect(
    card.getByRole("button", { name: "Gửi lại mã", exact: true }),
  ).toBeEnabled();
});

test("already verified email is shown and no phone verification UI exists", async ({
  page,
}) => {
  await fixture(page);
  await contactFixture(page, { verified: true });
  await page.goto("/client/freelancer/onboarding");
  await expect(
    page
      .getByRole("region", { name: "Xác minh email", exact: true })
      .getByText("Đã xác minh", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Xác minh điện thoại", exact: true }),
  ).toHaveCount(0);
});

test("OTP delivery errors stay visible and do not claim a code was sent", async ({
  page,
}) => {
  await fixture(page);
  await contactFixture(page);
  await page.route("**/api/v1/auth/verifications", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "OTP_DELIVERY_FAILED", message: "Delivery failed" },
      },
    }),
  );
  await page.goto("/client/freelancer/onboarding");
  const card = page.getByRole("region", {
    name: "Xác minh email",
    exact: true,
  });
  await card.getByRole("button", { name: "Gửi mã xác minh email" }).click();
  await expect(card.getByRole("alert")).toContainText("Không gửi được mã");
  await expect(card.getByLabel("Mã OTP email")).toHaveCount(0);
  await expect(
    card.getByRole("button", { name: "Gửi mã xác minh email" }),
  ).toBeEnabled();
});

test("pending-company onboarding uses its limited token and the same inline OTP flow", async ({
  page,
}) => {
  await contactFixture(page);
  await page.route("**/api/v1/auth/onboarding-token", (route) =>
    route.fulfill({
      json: { data: { access_token: "limited-only", expires_in: 900 } },
    }),
  );
  await page.route("**/api/v1/companies/me/verifications**", (route) =>
    route.fulfill({ json: paged([]) }),
  );
  const auth: string[] = [];
  page.on("request", (r) => {
    if (r.url().includes("/auth/verification"))
      auth.push(r.headers().authorization);
  });
  await page.goto("/onboarding");
  await page.getByLabel("Email đăng ký").fill("client@example.test");
  await page.getByLabel("Mật khẩu", { exact: true }).fill("Password@123");
  await page.getByRole("button", { name: "Mở hồ sơ chờ duyệt" }).click();
  const card = page.getByRole("region", {
    name: "Xác minh email",
    exact: true,
  });
  await card.getByRole("button", { name: "Gửi mã xác minh email" }).click();
  await card.getByLabel("Mã OTP email").fill("012345");
  await card
    .getByRole("button", { name: "Xác nhận email", exact: true })
    .click();
  await expect(card.getByText("Đã xác minh", { exact: true })).toBeVisible();
  expect(auth.length).toBeGreaterThan(1);
  expect(auth.every((value) => value === "Bearer limited-only")).toBe(true);
  expect(
    await page.evaluate(() =>
      sessionStorage.getItem("student-connect.refresh-token"),
    ),
  ).toBeNull();
});

test("registration normalizes Vietnamese phone numbers and displays server field errors", async ({
  page,
}) => {
  let body: Record<string, unknown> = {};
  await page.route("**/api/v1/auth/register-client", async (route) => {
    body = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      status: 422,
      json: { detail: [{ loc: ["body", "email"], msg: "Email không hợp lệ" }] },
    });
  });
  await page.goto("/register-client");
  await page.getByLabel("Họ tên", { exact: true }).fill("Nguyễn Văn An");
  await page.getByLabel("Email", { exact: true }).fill("a@example.test");
  await page.getByLabel(/Mật khẩu/).fill("Password@123");
  await page.getByLabel(/Số điện thoại/).fill("0912345678");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Tạo tài khoản người thuê" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Email: Email không hợp lệ",
  );
  expect(body.phone).toBe("+84912345678");
});

test("switching work tabs resets pagination and already-applied students cannot submit again", async ({
  page,
}) => {
  await fixture(page, "STUDENT");
  await page.route("**/api/v1/freelancer/contracts?**", (route) =>
    route.fulfill({ json: { ...paged([contract]), pages: 3, total: 41 } }),
  );
  const applicationPages: string[] = [];
  await page.route("**/api/v1/freelance-applications/me?**", (route) => {
    applicationPages.push(
      new URL(route.request().url()).searchParams.get("page") ?? "",
    );
    return route.fulfill({ json: paged([]) });
  });
  await page.goto("/student/freelancer/work");
  await page.getByRole("button", { name: "Trang sau", exact: true }).click();
  await expect(page.getByText(/Trang 2\/3/)).toBeVisible();
  await page
    .getByRole("button", { name: "Đơn ứng tuyển", exact: true })
    .click();
  await expect(page.getByText(/Trang 1\/1/)).toBeVisible();
  expect(applicationPages.every((p) => p === "1")).toBe(true);
  await page.route("**/api/v1/freelance-projects/100", (route) =>
    route.fulfill({
      json: {
        data: { ...project, my_application: { id: "20", status: "SUBMITTED" } },
      },
    }),
  );
  await page.goto("/student/freelancer/projects/100");
  await expect(page.getByText(/Bạn đã ứng tuyển dự án này/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Ứng tuyển dự án", exact: true }),
  ).toHaveCount(0);
});
test("profile editing preloads saved fields and refreshes the displayed profile", async ({
  page,
}) => {
  await fixture(page);
  await contactFixture(page, { verified: true });
  let profile = { id: "42", full_name: "Tên hiện tại", address: "Hà Nội" };
  await page.route("**/api/v1/client-accounts/me", async (route) => {
    if (route.request().method() === "PATCH")
      profile = { ...profile, ...route.request().postDataJSON() };
    await route.fulfill({ json: { data: profile } });
  });
  await page.goto("/client/freelancer/onboarding");
  await page.getByRole("button", { name: "Cập nhật hồ sơ người thuê" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("Họ tên", { exact: true })).toHaveValue(
    "Tên hiện tại",
  );
  await expect(dialog.getByLabel("Địa chỉ", { exact: true })).toHaveValue(
    "Hà Nội",
  );
  await dialog.getByLabel("Họ tên", { exact: true }).fill("Tên đã cập nhật");
  await dialog.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(
    page.getByText("Tên đã cập nhật", { exact: true }),
  ).toBeVisible();
});

test("business review requires acknowledgements and hides approval actions after success", async ({
  page,
}) => {
  await fixture(page, "ADMIN");
  let status = "PENDING";
  await page.route("**/api/v1/admin/business-verifications?**", (route) =>
    route.fulfill({
      json: paged([
        {
          id: "11",
          company_id: "21",
          status,
          submitted_snapshot: { company_name: "Doanh nghiệp thử nghiệm" },
        },
      ]),
    }),
  );
  await page.route(
    "**/api/v1/admin/business-verifications/11/approve",
    async (route) => {
      expect(route.request().postDataJSON()).toMatchObject({
        legal_identity_checked: true,
        representative_authority_checked: true,
      });
      status = "APPROVED";
      await route.fulfill({ json: { data: { id: "11", status } } });
    },
  );
  await page.goto("/admin/freelancer/admin/business");
  await page.getByRole("button", { name: "Xem chi tiết", exact: true }).click();
  await page
    .getByRole("button", { name: "Duyệt pháp nhân", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByLabel("Lý do / nội dung xác nhận")
    .fill("Đã đối chiếu hồ sơ và thẩm quyền.");
  await expect(dialog.getByLabel("Đã đối chiếu pháp nhân")).toHaveAttribute(
    "required",
    "",
  );
  await dialog.getByLabel("Đã đối chiếu pháp nhân").check();
  await dialog.getByLabel("Đã đối chiếu quyền đại diện").check();
  await dialog.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Duyệt pháp nhân", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Đã duyệt", { exact: true }).first(),
  ).toBeVisible();
});

const project = {
  id: "100",
  title: "Xây dựng website giới thiệu doanh nghiệp",
  client_user_id: "1",
  description: "Thiết kế và phát triển website có giao diện thích ứng.",
  budget_amount: "1500000",
  max_students: 1,
  deadline: "2027-12-20T10:00:00Z",
  recruitment_deadline: "2027-12-15T10:00:00Z",
  category: "DEVELOPMENT",
  experience_level: "ENTRY",
  attachments: [],
  funding_policy: "FULL",
  acceptance_criteria: "Chạy tốt trên máy tính và điện thoại.",
  deliverables_description: "Mã nguồn và tài liệu sử dụng.",
  status: "APPROVED",
  recruitment_status: "OPEN",
  proposals: [
    {
      id: "101",
      title: "Bàn giao website hoàn chỉnh",
      amount: "1500000",
      due_at: "2027-12-18T10:00:00Z",
      acceptance_criteria: "Chạy đúng yêu cầu.",
    },
  ],
};
const term = {
  id: "701",
  milestone_id: "601",
  title: "Bàn giao website hoàn chỉnh",
  description: "Hoàn thành mã nguồn và tài liệu.",
  amount: "1500000",
  due_at: "2027-12-18T10:00:00Z",
  acceptance_criteria: "Chạy đúng yêu cầu.",
  included: true,
};
const version = {
  id: "200",
  contract_id: "500",
  version_no: 1,
  created_by: "1",
  status: "EFFECTIVE",
  fee_rate_bp: 500,
  total_amount: "1500000",
  funding_policy: "FULL",
  review_period_seconds: 604800,
  max_revision_count: 2,
  acceptance_deadline: "2027-12-10T00:00:00Z",
  client_accepted_at: "2027-01-01",
  freelancer_accepted_at: "2027-01-01",
  milestone_terms: [term],
};
const contract = {
  id: "500",
  project_id: "100",
  client_user_id: "1",
  freelancer_student_id: "10",
  status: "ACTIVE",
  allocated_amount: "1500000",
  effective_version: version,
  project_title: project.title,
  student_name: "Nguyễn Minh Anh",
  client_email: "owner@example.test",
};
const bank = {
  id: "5",
  user_id: "2",
  bank_bin: "970422",
  account_name: "NGUYEN MINH ANH",
  account_last4: "1234",
  verification_status: "PENDING",
};
const dispute = {
  id: "8",
  milestone_id: "601",
  description: "Đề nghị xem xét chất lượng bàn giao.",
  status: "EVIDENCE_COLLECTION",
  reason_code: "QUALITY",
  evidence_deadline: "2027-12-20T00:00:00Z",
};

async function fixture(
  page: Page,
  role: "CLIENT" | "STUDENT" | "ADMIN" | "COMPANY" = "CLIENT",
  adminId = 901,
) {
  const writes: {
    path: string;
    method: string;
    body: Record<string, unknown>;
    key: string | undefined;
  }[] = [];
  const state = { milestone: "SUBMITTED", order: "PENDING", bank: "PENDING" };
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() =>
    sessionStorage.setItem("student-connect.refresh-token", "test-refresh"),
  );
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api/v1", "");
    const method = request.method();
    let data: unknown = paged([]);
    if (!["GET", "OPTIONS"].includes(method)) {
      const body = request.postData()
        ? (request.postDataJSON() as Record<string, unknown>)
        : {};
      writes.push({
        path,
        method,
        body,
        key: request.headers()["idempotency-key"],
      });
      if (path === "/milestones/601/accept")
        state.milestone = "SETTLEMENT_PENDING";
      if (path === "/admin/bank-destinations/5/review")
        state.bank = body.approve ? "VERIFIED" : "REJECTED";
      if (path === "/freelance-projects")
        data = { data: { ...project, id: "101", ...body } };
      else if (path === "/freelance-projects/100/applications")
        data = { data: { id: "20", status: "SUBMITTED" } };
      else if (path === "/admin/bank-destinations/5/verification-data")
        data = {
          data: {
            id: "5",
            account_name: "NGUYEN MINH ANH",
            bank_bin: "970422",
            account_number: "123456789012",
          },
        };
      else data = { data: { id: "1", status: "PROCESSING" } };
    }
    if (path === "/auth/refresh" || path === "/auth/login")
      data = {
        access_token: "test-access",
        refresh_token: "test-refresh",
        token_type: "bearer",
      };
    else if (path === "/auth/me")
      data = {
        id: role === "CLIENT" ? 1 : role === "STUDENT" ? 2 : adminId,
        email: role.toLowerCase() + "@example.test",
        role,
        status: "ACTIVE",
        ...(role === "STUDENT"
          ? { student: { id: 10, full_name: "Nguyễn Minh Anh" } }
          : {}),
      };
    else if (path === "/notifications/unread-count") data = { unread_count: 0 };
    else if (method === "GET") {
      if (path === "/admin/verifications" || path === "/admin/mou/agreements") data = [];
      else if (path === "/freelance-projects") data = paged([project]);
      else if (
        path === "/freelance-projects/100" ||
        path === "/freelance-projects/101"
      )
        data = { data: project };
      else if (path.endsWith("/budget"))
        data = {
          data: {
            allocated_total: "1500000",
            remaining_budget_to_allocate: "0",
          },
        };
      else if (
        path === "/freelance-projects/100/contracts" ||
        path === "/freelancer/contracts"
      )
        data = paged([contract]);
      else if (path === "/freelance-contracts/500") data = contract;
      else if (path === "/freelance-contracts/500/versions")
        data = paged([version]);
      else if (path === "/freelance-contracts/500/milestones")
        data = [
          {
            id: "601",
            contract_id: "500",
            status: state.milestone,
            effective_terms: term,
          },
        ];
      else if (path === "/freelance-contracts/500/reviews") data = [];
      else if (path === "/milestones/601")
        data = {
          id: "601",
          contract_id: "500",
          status: state.milestone,
          effective_terms: term,
          revision_count: 0,
        };
      else if (path === "/milestones/601/deliverables")
        data = paged([
          {
            id: "50",
            submission_no: 1,
            note: "Đã bàn giao mã nguồn.",
            submitted_at: "2027-01-01T00:00:00Z",
            files: [],
            reviews: [],
          },
        ]);
      else if (path === "/milestones/601/activity")
        data = { data: { cancellations: [], disputes: [dispute] } };
      else if (path.endsWith("/finance"))
        data = {
          data: {
            funded_amount: "1500000",
            terms_amount: "1500000",
            fee_rate_bp: 500,
            fee_amount: "75000",
            net_amount: "1425000",
            held_amount: "1500000",
            reserved_amount:
              state.milestone === "SETTLEMENT_PENDING" ? "1500000" : "0",
            released_gross: "0",
            refunded_amount: "0",
            active_hold_ids: [],
          },
        };
      else if (
        path === "/payment-orders/7" ||
        path === "/payment-orders/by-code/1000000001"
      )
        data = {
          data: {
            id: "7",
            milestone_id: "601",
            expected_amount: "1500000",
            order_code: "1000000001",
            status: state.order,
            checkout_url: "https://pay.example.test/link",
            qr_payload: "test-qr-payload",
            expires_at: "2027-12-20T00:00:00Z",
          },
        };
      else if (
        path === "/bank-destinations" ||
        path === "/admin/bank-destinations"
      )
        data = paged([{ ...bank, verification_status: state.bank }]);
      else if (path === "/admin/finance/treasury-entries")
        data = paged([
          {
            id: "9",
            proposed_by: "901",
            amount: "1500000",
            external_reference: "BANK-TRACE-ONE",
            kind: "EQUITY_PAYOUT",
            status: "PROPOSED",
          },
        ]);
      else if (path === "/admin/disputes") data = paged([dispute]);
      else if (path === "/disputes/8" || path === "/admin/disputes/8")
        data = { data: dispute };
      else if (path === "/client-accounts/eligibility/me")
        data = {
          user_id: "1",
          tier: "CLIENT",
          can_draft: true,
          can_submit: true,
          can_fund: true,
          reason_codes: [],
        };
      else if (path === "/auth/escrow-terms") data = { data: { has_accepted_escrow_terms: true, version: "2026-11-12" } };
      else if (path === "/catalog/skills")
        data = paged([{ id: "1", name: "Thiết kế đồ họa" }]);
      else if (path.startsWith("/catalog/")) data = paged([]);
    }
    await route.fulfill({ json: data });
  });
  return { writes, state, errors };
}

test("CLIENT role can create a small project with exactly one milestone", async ({
  page,
}) => {
  const { writes, errors } = await fixture(page);
  await page.goto("/client/freelancer/projects/new");
  await page.getByLabel("Tên dự án", { exact: false }).fill("Dự án một mốc");
  await page.getByLabel("Mô tả công việc").fill("Thiết kế logo cho dự án nhỏ.");
  await page.getByLabel("Tổng ngân sách").fill("500000");
  await page.getByLabel("Hạn hoàn thành dự án").fill("2027-12-20T10:00");
  await page.getByLabel("Hạn nhận ứng tuyển").fill("2027-12-15T10:00");
  await page.getByLabel("Danh mục công việc").selectOption("DESIGN");
  await page.getByLabel("Trình độ mong muốn (tùy chọn)").selectOption("ENTRY");
  await page.getByRole("button", { name: "Thiết kế đồ họa", exact: true }).click();
  await page
    .getByLabel("Tiêu chí nghiệm thu", { exact: false })
    .first()
    .fill("Đúng màu thương hiệu.");
  await page.getByLabel("Sản phẩm cần bàn giao").fill("Bộ logo hoàn chỉnh.");
  await page.getByRole("button", { name: "Thêm mốc" }).click();
  await page.getByLabel("Tên mốc", { exact: true }).fill("Bàn giao logo");
  await page.getByLabel("Số tiền (₫)", { exact: true }).fill("500000");
  await page.getByLabel("Hạn bàn giao").fill("2027-12-18T10:00");
  await page
    .getByLabel("Tiêu chí nghiệm thu", { exact: true })
    .last()
    .fill("Bàn giao đủ tệp.");
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    document.documentElement.style.scrollBehavior = "auto";
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: "test-results/project-posting-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Lưu bản nháp", exact: true }).click();
  await expect(page).toHaveURL(/projects\/101$/);
  const call = writes.find((w) => w.path === "/freelance-projects");
  expect(call?.body.budget_amount).toBe("500000");
  expect(call?.body.max_students).toBe(1);
  expect(call?.body.category).toBe("DESIGN");
  expect(call?.body.experience_level).toBe("ENTRY");
  expect(call?.body.recruitment_deadline).not.toBe(call?.body.deadline);
  expect(call?.body.skill_ids).toEqual(["1"]);
  expect(call?.body.proposals).toHaveLength(1);
  expect(errors).toEqual([]);
});

test("project draft only requires a title and has no artificial zero budget or milestones", async ({
  page,
}) => {
  const { writes, errors } = await fixture(page);
  await page.goto("/client/freelancer/projects/new");
  await page.getByLabel("Tên dự án", { exact: true }).fill("Ý tưởng đang soạn");
  await page.getByRole("button", { name: "Lưu bản nháp", exact: true }).click();
  await expect(page).toHaveURL(/projects\/101$/);
  const call = writes.find((w) => w.path === "/freelance-projects");
  expect(call?.body.budget_amount).toBeNull();
  expect(call?.body.deadline).toBeNull();
  expect(call?.body.recruitment_deadline).toBeNull();
  expect(call?.body.proposals).toEqual([]);
  expect(errors).toEqual([]);
});

test("project references use a dedicated category, require a clean scan and can be removed", async ({
  page,
}) => {
  const { writes, errors } = await fixture(page);
  const file = {
    id: "88",
    original_name: "brief.pdf",
    scan_status: "PENDING",
    availability_status: "AVAILABLE",
  };
  await page.route("**/api/v1/files**", async (route) => {
    if (route.request().method() === "POST") {
      expect(route.request().postDataBuffer()?.toString()).toContain(
        "PROJECT_REFERENCE",
      );
    }
    await route.fulfill({ json: { data: file } });
  });
  await page.goto("/client/freelancer/projects/new");
  await page
    .getByLabel("Tên dự án", { exact: true })
    .fill("Có tài liệu tham khảo");
  await page.locator('input[type="file"]').setInputFiles({
    name: "brief.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-brief"),
  });
  await expect(
    page.getByRole("button", { name: "Sử dụng tài liệu này" }),
  ).toBeDisabled();
  file.scan_status = "CLEAN";
  await page.reload();
  await page
    .getByLabel("Tên dự án", { exact: true })
    .fill("Có tài liệu tham khảo");
  await page.locator('input[type="file"]').setInputFiles({
    name: "brief.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-brief"),
  });
  await page.getByRole("button", { name: "Sử dụng tài liệu này" }).click();
  await expect(page.getByRole("button", { name: "Gỡ tài liệu" })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    document.documentElement.style.scrollBehavior = "auto";
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: "test-results/project-posting-mobile.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Gỡ tài liệu" }).click();
  await expect(page.getByRole("button", { name: "Gỡ tài liệu" })).toHaveCount(
    0,
  );
  await page.locator('input[type="file"]').setInputFiles({
    name: "brief.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-brief"),
  });
  await page.getByRole("button", { name: "Sử dụng tài liệu này" }).click();
  await page.getByRole("button", { name: "Lưu bản nháp", exact: true }).click();
  await expect(page).toHaveURL(/projects\/101$/);
  expect(
    writes.find((w) => w.path === "/freelance-projects")?.body
      .attachment_file_ids,
  ).toEqual(["88"]);
  expect(errors).toEqual([]);
});

test("student applies with a proposal and sees only own work routes", async ({
  page,
}) => {
  const { writes, errors } = await fixture(page, "STUDENT");
  await page.goto("/student/freelancer/projects/100");
  await page
    .getByRole("button", { name: "Ứng tuyển dự án", exact: true })
    .click();
  const modal = page.getByRole("dialog");
  await modal
    .getByLabel("Đề xuất thực hiện")
    .fill("Tôi có thể hoàn thành dự án này.");
  await modal.getByLabel("Mức giá đề xuất").fill("1500000");
  await modal.getByLabel("Thời gian thực hiện").fill("10");
  await modal.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(modal).not.toBeVisible();
  expect(writes.find((w) => w.path.endsWith("/applications"))?.body).toEqual({
    proposal: "Tôi có thể hoàn thành dự án này.",
    quoted_amount: "1500000",
    estimated_days: 10,
  });
  await page.goto("/student/freelancer/admin/banks");
  await expect(
    page.getByRole("heading", {
      name: "Xác minh tài khoản ngân hàng",
      exact: true,
    }),
  ).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("acceptance enters settlement pending and never claims that money was paid", async ({
  page,
}) => {
  const { writes } = await fixture(page);
  await page.goto("/client/freelancer/milestones/601");
  await page
    .getByRole("button", { name: "Nghiệm thu & xử lý giải ngân" })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Xác nhận", exact: true })
    .click();
  await expect(
    page.getByText("Đang quyết toán", { exact: true }).first(),
  ).toBeVisible();
  expect(
    writes.filter((w) => w.path === "/milestones/601/accept"),
  ).toHaveLength(1);
  expect(writes.find((w) => w.path.endsWith("/accept"))?.key).toBeTruthy();
  expect(writes.find((w) => w.path.endsWith("/accept"))?.body).toEqual({
    deliverable_id: "50",
  });
  await expect(page.getByText("Đã giải ngân", { exact: true })).toHaveCount(0);
});

test("forged payOS success parameters cannot create a successful result", async ({
  page,
}) => {
  const { writes } = await fixture(page);
  await page.goto(
    "/payments/return?orderCode=1000000001&status=PAID&code=00&cancel=false",
  );
  await expect(page).toHaveURL(/client\/freelancer\/payments\/7$/);
  await expect(
    page.getByRole("heading", { name: "Theo dõi ký quỹ của bạn" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Ký quỹ đã được xác nhận" }),
  ).toHaveCount(0);
  expect(writes.filter((w) => !w.path.startsWith("/auth/"))).toHaveLength(0);
  await expect(page.locator(".fl-qr svg")).toBeVisible();
});

test("legacy treasury page redirects to automatic payout monitoring", async ({ page }) => {
  const { writes } = await fixture(page, "ADMIN", 901);
  await page.goto("/admin/freelancer/admin/treasury");
  await expect(page).toHaveURL(/admin\/transfers$/);
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  expect(writes.filter((w) => !w.path.startsWith("/auth/"))).toHaveLength(0);
});

test("bank verification sends evidence acknowledgement and updates displayed state", async ({
  page,
}) => {
  const { writes } = await fixture(page, "ADMIN");
  await page.goto("/admin/freelancer/admin/banks");
  await page.getByRole("button", { name: "Xem chi tiết", exact: true }).click();
  await page
    .getByRole("button", { name: "Duyệt tài khoản", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("checkbox").check();
  await dialog
    .getByLabel("Lý do / nội dung xác nhận")
    .fill("Đã đối chiếu chứng cứ chủ sở hữu tài khoản.");
  await dialog.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  expect(writes.find((w) => w.path.endsWith("/review"))?.body.approve).toBe(
    true,
  );
  await expect(page.getByRole("table").getByText("Đã xác minh")).toBeVisible();
});

test("desktop and mobile screens render without page errors or viewport overflow", async ({
  page,
}) => {
  const client = await fixture(page);
  for (const path of [
    "projects",
    "projects/100",
    "work",
    "contracts/500",
    "milestones/601",
    "banks",
    "disputes/8",
  ]) {
    await page.goto("/client/freelancer/" + path);
    await expect(page.locator(".fl h1").first()).toBeVisible();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/client/freelancer/projects");
  await expect(page.locator(".fl-project-card").first()).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/freelancer-mobile.png",
    fullPage: true,
  });
  expect(client.errors).toEqual([]);
});

test("full bank number is shown only after explicit inspection and can be hidden", async ({
  page,
}) => {
  const { writes } = await fixture(page, "ADMIN");
  await page.goto("/admin/freelancer/admin/banks");
  await page.getByRole("button", { name: "Xem chi tiết", exact: true }).click();
  await expect(page.getByText("123456789012", { exact: true })).toHaveCount(0);
  await page
    .locator("summary")
    .filter({ hasText: "Đối chiếu số tài khoản đầy đủ" })
    .click();
  await page
    .getByLabel("Lý do xem thông tin")
    .fill("Đối chiếu chứng cứ sở hữu trước khi xét duyệt.");
  await page
    .getByRole("button", { name: "Mở thông tin đối chiếu", exact: true })
    .click();
  await expect(page.getByText("123456789012", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ẩn thông tin", exact: true }).click();
  await expect(page.getByText("123456789012", { exact: true })).toHaveCount(0);
  expect(
    writes.find((w) => w.path.endsWith("/verification-data"))?.body.reason,
  ).toBeTruthy();
});

test("all administrator screens render with live-response-shaped data", async ({
  page,
}) => {
  const { errors } = await fixture(page, "ADMIN");
  for (const section of [
    "business",
    "projects",
    "banks",
    "receipts",
    "transfers",
    "disputes",
    "reconciliation",
  ]) {
    await page.goto("/admin/freelancer/admin/" + section);
    await expect(page.locator(".fl h1").first()).toBeVisible();
    await expect(page.locator(".fl-table, .fl-empty").first()).toBeVisible();
  }
  await page.screenshot({
    path: "test-results/freelancer-admin.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
