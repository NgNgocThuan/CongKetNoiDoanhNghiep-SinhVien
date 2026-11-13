import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

test.skip(
  !process.env.FREELANCER_LIVE_TEST,
  "Requires the disposable database from seed-freelancer-backend.py and local backend on port 18765.",
);

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill("UiTestOnly@2026");
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page).not.toHaveURL(/\/login$/);
}
async function confirm(page: Page, reason?: string) {
  const modal = page.getByRole("dialog");
  if (reason) await modal.getByLabel("Lý do / nội dung xác nhận").fill(reason);
  await modal.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(modal).not.toBeVisible();
}

test("real backend: project approval, application, separate contract and mutual terms acceptance", async ({
  browser,
}) => {
  test.setTimeout(100_000);
  const contexts = await Promise.all([
    browser.newContext(),
    browser.newContext(),
    browser.newContext(),
  ]);
  const [owner, admin, student] = await Promise.all(
    contexts.map((c) => c.newPage()),
  );
  try {
    await login(owner, "client@test.com");
    await owner.goto("/client/freelancer/projects/new");
    await owner
      .getByLabel("Tên dự án", { exact: false })
      .fill("Dự án UI một mốc " + Date.now());
    await owner
      .getByLabel("Mô tả công việc")
      .fill("Thiết kế bộ logo thương hiệu cho dự án nhỏ.");
    await owner.getByLabel("Tổng ngân sách").fill("500000");
    await owner.getByLabel("Hạn hoàn thành dự án").fill("2027-12-20T10:00");
    await owner.getByLabel("Hạn nhận ứng tuyển").fill("2027-12-15T10:00");
    await owner.getByLabel("Danh mục công việc").selectOption("DESIGN");
    await owner.getByLabel("Thiết kế đồ họa").check();
    await owner
      .getByLabel("Tiêu chí nghiệm thu")
      .first()
      .fill("Đúng màu thương hiệu và đủ tệp.");
    await owner
      .getByLabel("Sản phẩm cần bàn giao")
      .fill("Bộ logo và tài liệu.");
    await owner.getByRole("button", { name: "Thêm mốc" }).click();
    await owner.getByLabel("Tên mốc", { exact: true }).fill("Bàn giao logo");
    await owner.getByLabel("Số tiền (₫)", { exact: true }).fill("500000");
    await owner.getByLabel("Hạn bàn giao").fill("2027-12-18T10:00");
    await owner
      .getByLabel("Tiêu chí nghiệm thu", { exact: true })
      .last()
      .fill("Bàn giao đầy đủ sản phẩm.");
    await owner
      .getByRole("button", { name: "Lưu bản nháp", exact: true })
      .click();
    await expect(owner).toHaveURL(/\/projects\/\d+$/);
    const projectId = owner.url().split("/").at(-1);
    await owner
      .getByRole("button", { name: "Gửi duyệt dự án", exact: true })
      .click();
    await confirm(owner);

    await login(admin, "ui-admin@test.com");
    await admin.goto("/admin/freelancer/projects/" + projectId);
    await admin.getByRole("button", { name: "Phê duyệt", exact: true }).click();
    await confirm(
      admin,
      "Đã đối chiếu phạm vi, ngân sách và tiêu chí bàn giao.",
    );

    await login(student, "student@test.com");
    await student.goto("/student/freelancer/projects/" + projectId);
    await student
      .getByRole("button", { name: "Ứng tuyển dự án", exact: true })
      .click();
    await student
      .getByRole("dialog")
      .getByLabel("Đề xuất thực hiện")
      .fill("Tôi có thể hoàn thành bộ logo.");
    await student
      .getByRole("dialog")
      .getByLabel("Mức giá đề xuất")
      .fill("500000");
    await student
      .getByRole("dialog")
      .getByLabel("Thời gian thực hiện")
      .fill("10");
    await confirm(student);

    await owner.reload();
    await owner.getByRole("button", { name: "Ứng viên", exact: true }).click();
    await owner
      .getByRole("button", { name: "Chọn sinh viên", exact: true })
      .click();
    await confirm(owner);
    await expect(owner).toHaveURL(/\/contracts\/\d+$/);
    const contractId = owner.url().split("/").at(-1);
    await owner
      .getByRole("button", { name: "Điều khoản & phiên bản", exact: true })
      .click();
    await owner
      .getByRole("button", { name: "Soạn phiên bản", exact: false })
      .click();
    await owner.getByLabel("Tên mốc", { exact: true }).fill("Bàn giao logo");
    await owner.getByLabel("Số tiền (₫)", { exact: true }).fill("500000");
    await owner.getByLabel("Hạn bàn giao").fill("2027-12-18T10:00");
    await owner
      .getByLabel("Tiêu chí nghiệm thu", { exact: true })
      .fill("Đúng thỏa thuận, đủ tệp gốc.");
    await owner
      .getByRole("button", { name: "Lưu phiên bản nháp", exact: true })
      .click();
    await owner
      .getByRole("button", { name: "Gửi đề nghị điều khoản", exact: true })
      .click();
    await confirm(owner);
    await expect(
      owner.getByText("Bạn đã chấp nhận lúc", { exact: false }),
    ).toBeVisible();

    await student.goto("/student/freelancer/contracts/" + contractId);
    await student
      .getByRole("button", { name: "Điều khoản & phiên bản", exact: true })
      .click();
    await student
      .getByRole("button", { name: "Chấp nhận điều khoản", exact: true })
      .click();
    await confirm(student);
    await expect(
      student.getByText("Đang thực hiện", { exact: true }).first(),
    ).toBeVisible();
    await student
      .getByRole("button", { name: "Mốc công việc", exact: true })
      .click();
    await expect(
      student.getByText("Chưa ký quỹ", { exact: true }).first(),
    ).toBeVisible();
    await expect(
      student.getByRole("link", { name: "Mở không gian công việc" }),
    ).toHaveCount(1);
    await student.screenshot({
      path: "test-results/freelancer-live-contract.png",
      fullPage: true,
    });
  } finally {
    await Promise.allSettled(contexts.map((c) => c.close()));
  }
});
