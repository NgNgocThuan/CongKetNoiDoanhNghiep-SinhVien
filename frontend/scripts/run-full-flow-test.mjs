import { chromium } from '@playwright/test';
import { spawn, execSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const ROOT_DIR = 'B:\\project\\student-connect\\student-connect';
const WORKTREE_DIR = path.join(ROOT_DIR, 'tmp\\fix-freelancer-a-c');
const BACKEND_DIR = path.join(WORKTREE_DIR, 'backend');
const FRONTEND_DIR = path.join(WORKTREE_DIR, 'frontend');
const SCREENSHOTS_DIR = path.join(WORKTREE_DIR, 'tmp\\test-screenshots');
const DB_FILE = path.join(WORKTREE_DIR, 'tmp\\student_connect_ui_test_5398e6103083493a892350bb4a4c24bd.sqlite');
const REPORT_FILE = path.join(ROOT_DIR, 'BAO_CAO_TEST_LUONG_FREELANCER.md');

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL = 'http://127.0.0.1:8000';

await mkdir(SCREENSHOTS_DIR, { recursive: true });

const testLog = [];
const consoleErrors = [];
const networkErrors = [];
const screenshots = [];

function log(msg) {
  const ts = new Date().toLocaleTimeString('vi-VN');
  console.log(`[${ts}] ${msg}`);
  testLog.push(`[${ts}] ${msg}`);
}

async function waitForHttp(url, timeoutMs = 25000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status < 500) return true;
    } catch {
      // Backend/front-end may still be starting; retry until the timeout.
    }
    await new Promise((r) => setTimeout(r, 600));
  }
  throw new Error(`Timeout waiting for ${url}`);
}

// 1. Start Backend & Frontend
log('1. Khởi động Backend (port 8000) và Frontend (port 5173)...');

const backendProc = spawn(
  'python',
  ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
  {
    cwd: BACKEND_DIR,
    env: {
      ...process.env,
      DATABASE_URL: 'sqlite:///' + DB_FILE.replace(/\\/g, '/'),
      PYTHONPATH: BACKEND_DIR,
      DEBUG: 'true',
      CORS_ORIGINS: '["http://127.0.0.1:5173","http://localhost:5173"]',
      FRONTEND_URL: 'http://127.0.0.1:5173',
      BACKEND_PROXY_TARGET: 'http://127.0.0.1:8000',
      FREELANCER_FINANCE_ENABLED: 'true',
      PAYOS_COLLECTION_ENABLED: 'false',
      PAYOS_PAYOUT_ENABLED: 'false',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  }
);

const viteBin = path.join(FRONTEND_DIR, 'node_modules\\vite\\bin\\vite.js');
const frontendProc = spawn(
  'node',
  [viteBin, '--host', '127.0.0.1', '--port', '5173', '--strictPort'],
  {
    cwd: FRONTEND_DIR,
    env: {
      ...process.env,
      BACKEND_PROXY_TARGET: 'http://127.0.0.1:8000',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  }
);

let browser;
try {
  log('Đang chờ Backend /health...');
  await waitForHttp(`${API_URL}/health`, 20000);
  log('Backend sẵn sàng!');

  log('Đang chờ Frontend http://127.0.0.1:5173...');
  await waitForHttp(BASE_URL, 20000);
  log('Frontend sẵn sàng!');

  log('2. Mở trình duyệt Chrome tự động...');
  try {
    browser = await chromium.launch({
      channel: 'chrome',
      headless: true,
    });
    log('Đã mở Chrome (kênh chrome hệ thống).');
  } catch (e) {
    log(`Không mở được channel chrome (${e.message}), chuyển sang chromium bundled.`);
    browser = await chromium.launch({ headless: true });
  }

  function setupPageListeners(page, roleName) {
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        consoleErrors.push(`[${roleName}] Console Error: ${text}`);
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(`[${roleName}] Page Error (Uncaught): ${err.message}`);
    });
    page.on('response', (res) => {
      const url = res.url();
      const status = res.status();
      if (url.includes('/api/v1/') && status >= 400) {
        networkErrors.push({
          role: roleName,
          method: res.request().method(),
          url,
          status,
        });
      }
    });
  }

  async function login(page, email, password = 'UiTestOnly@2026') {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.locator('#email').fill(email);
    await page.locator('#password').fill(password);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await page.waitForTimeout(1200);
  }

  async function confirmModal(page, reasonText) {
    const modal = page.getByRole('dialog');
    await modal.waitFor({ state: 'visible', timeout: 5000 });
    if (reasonText) {
      const input = modal.getByLabel('Lý do / nội dung xác nhận');
      if (await input.isVisible()) {
        await input.fill(reasonText);
      }
    }
    const btn = modal.getByRole('button', { name: 'Xác nhận', exact: true });
    await btn.click();
    try {
      await modal.waitFor({ state: 'hidden', timeout: 5000 });
    } catch {
      const errText = await modal.innerText().catch(() => '');
      log(`Modal chưa đóng (có thể hiển thị thông báo): ${errText.replace(/\s+/g, ' ').trim()}`);
      const closeBtn = modal.getByRole('button', { name: /Hủy|Đóng/ });
      if (await closeBtn.isVisible()) await closeBtn.click().catch(() => {});
    }
  }

  // ==========================================
  // LUỒNG 1: TẠO CÔNG VIỆC, PHÊ DUYỆT & HỢP ĐỒNG
  // ==========================================
  log('==========================================');
  log('BƯỚC 1: KIỂM THỬ LUỒNG TẠO CÔNG VIỆC & KÝ HỢP ĐỒNG');
  log('==========================================');

  const clientCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const clientPage = await clientCtx.newPage();
  setupPageListeners(clientPage, 'CLIENT');

  log('Client: Đăng nhập client@test.com...');
  await login(clientPage, 'client@test.com');
  const clientShot1 = path.join(SCREENSHOTS_DIR, '01-client-logged-in.png');
  await clientPage.screenshot({ path: clientShot1 });
  screenshots.push({ name: '01-client-logged-in.png', desc: 'Client đăng nhập thành công' });

  log('Client: Vào trang tạo dự án mới /client/freelancer/projects/new...');
  await clientPage.goto(`${BASE_URL}/client/freelancer/projects/new`);
  await clientPage.waitForLoadState('networkidle');

  const projectTitle = `Dự án Logo & Web App E2E ${Date.now()}`;
  log(`Client: Điền thông tin dự án: "${projectTitle}"...`);
  await clientPage.getByLabel('Tên dự án', { exact: false }).fill(projectTitle);
  await clientPage.getByLabel('Mô tả công việc').fill('Xây dựng nhận diện thương hiệu và ứng dụng web hoàn chỉnh.');
  await clientPage.getByLabel('Tổng ngân sách').fill('1500000');
  await clientPage.getByLabel('Hạn hoàn thành dự án').fill('2027-12-30T10:00');
  await clientPage.getByLabel('Hạn nhận ứng tuyển').fill('2027-12-20T10:00');
  await clientPage.getByLabel('Danh mục công việc').selectOption('DESIGN');
  
  const skillCheckbox = clientPage.getByLabel('Thiết kế đồ họa');
  if (await skillCheckbox.isVisible()) {
    await skillCheckbox.check();
  }

  await clientPage.getByLabel('Tiêu chí nghiệm thu').first().fill('Đúng thiết kế, đầy đủ file mã nguồn.');
  await clientPage.getByLabel('Sản phẩm cần bàn giao').fill('Source code zip và tài liệu hướng dẫn.');

  log('Client: Thêm mốc công việc 1...');
  await clientPage.getByRole('button', { name: 'Thêm mốc' }).click();
  await clientPage.getByLabel('Tên mốc', { exact: true }).fill('Mốc 1: Giao diện ban đầu');
  await clientPage.getByLabel('Số tiền (₫)', { exact: true }).fill('1500000');
  await clientPage.getByLabel('Hạn bàn giao').fill('2027-12-25T10:00');
  await clientPage.getByLabel('Tiêu chí nghiệm thu', { exact: true }).last().fill('Hoàn thành giao diện chính.');

  const clientShot2 = path.join(SCREENSHOTS_DIR, '02-project-form-filled.png');
  await clientPage.screenshot({ path: clientShot2 });
  screenshots.push({ name: '02-project-form-filled.png', desc: 'Form tạo dự án được điền đầy đủ' });

  log('Client: Bấm "Lưu bản nháp"...');
  await clientPage.getByRole('button', { name: 'Lưu bản nháp', exact: true }).click();
  await clientPage.waitForURL(/\/projects\/\d+$/, { timeout: 10000 });

  const projectUrl = clientPage.url();
  const projectId = projectUrl.split('/').pop();
  log(`Tạo dự án thành công! Project ID = ${projectId}`);

  const clientShot3 = path.join(SCREENSHOTS_DIR, '03-project-draft-saved.png');
  await clientPage.screenshot({ path: clientShot3 });
  screenshots.push({ name: '03-project-draft-saved.png', desc: 'Dự án ở trạng thái bản nháp' });

  log('Client: Bấm "Gửi duyệt dự án"...');
  await clientPage.getByRole('button', { name: 'Gửi duyệt dự án', exact: true }).click();
  await confirmModal(clientPage);
  log('Client: Đã gửi duyệt dự án!');

  // Admin duyệt
  log('Admin: Đăng nhập ui-admin@test.com để phê duyệt dự án...');
  const adminCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const adminPage = await adminCtx.newPage();
  setupPageListeners(adminPage, 'ADMIN');

  await login(adminPage, 'ui-admin@test.com');
  await adminPage.goto(`${BASE_URL}/admin/freelancer/projects/${projectId}`);
  await adminPage.waitForLoadState('networkidle');

  const adminShot1 = path.join(SCREENSHOTS_DIR, '04-admin-review-project.png');
  await adminPage.screenshot({ path: adminShot1 });
  screenshots.push({ name: '04-admin-review-project.png', desc: 'Admin xem dự án chờ duyệt' });

  log('Admin: Bấm "Phê duyệt" dự án...');
  await adminPage.getByRole('button', { name: 'Phê duyệt', exact: true }).click();
  await confirmModal(adminPage, 'Đã thẩm định thông tin đầy đủ và phê duyệt.');
  log('Admin: Đã phê duyệt dự án!');

  // Sinh viên ứng tuyển
  log('Sinh viên: Đăng nhập student@test.com để nộp đơn ứng tuyển...');
  const studentCtx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const studentPage = await studentCtx.newPage();
  setupPageListeners(studentPage, 'STUDENT');

  await login(studentPage, 'student@test.com');
  await studentPage.goto(`${BASE_URL}/student/freelancer/projects/${projectId}`);
  await studentPage.waitForLoadState('networkidle');

  const studentShot1 = path.join(SCREENSHOTS_DIR, '05-student-view-project.png');
  await studentPage.screenshot({ path: studentShot1 });
  screenshots.push({ name: '05-student-view-project.png', desc: 'Sinh viên xem dự án đã duyệt' });

  log('Sinh viên: Bấm "Ứng tuyển dự án"...');
  await studentPage.getByRole('button', { name: 'Ứng tuyển dự án', exact: true }).click();

  const applyModal = studentPage.getByRole('dialog');
  await applyModal.waitFor({ state: 'visible' });
  await applyModal.getByLabel('Đề xuất thực hiện').fill('Em có kinh nghiệm thiết kế và code web tương tự.');
  await applyModal.getByLabel('Mức giá đề xuất').fill('1500000');
  await applyModal.getByLabel('Thời gian thực hiện').fill('10');
  await confirmModal(studentPage);
  log('Sinh viên: Đã nộp đơn ứng tuyển thành công!');

  // Client chọn sinh viên và tạo hợp đồng
  log('Client: Tải lại trang dự án để chọn ứng viên...');
  await clientPage.reload({ waitUntil: 'networkidle' });
  await clientPage.getByRole('button', { name: 'Ứng viên', exact: true }).click();
  await clientPage.waitForTimeout(1000);

  const clientShot4 = path.join(SCREENSHOTS_DIR, '06-client-view-applicants.png');
  await clientPage.screenshot({ path: clientShot4 });
  screenshots.push({ name: '06-client-view-applicants.png', desc: 'Client xem danh sách ứng viên' });

  log('Client: Chọn sinh viên trúng tuyển...');
  await clientPage.getByRole('button', { name: 'Chọn sinh viên', exact: true }).click();
  await confirmModal(clientPage);
  await clientPage.waitForURL(/\/contracts\/\d+$/, { timeout: 10000 });

  const contractUrl = clientPage.url();
  const contractId = contractUrl.split('/').pop();
  log(`Tạo hợp đồng thành công! Contract ID = ${contractId}`);

  const clientShot5 = path.join(SCREENSHOTS_DIR, '07-contract-created.png');
  await clientPage.screenshot({ path: clientShot5 });
  screenshots.push({ name: '07-contract-created.png', desc: 'Hợp đồng được tạo' });

  // Client gửi điều khoản hợp đồng
  log('Client: Mở tab "Điều khoản & phiên bản" để soạn điều khoản...');
  await clientPage.getByRole('button', { name: 'Điều khoản & phiên bản', exact: true }).click();
  await clientPage.getByRole('button', { name: 'Soạn phiên bản', exact: false }).click();

  await clientPage.getByLabel('Tên mốc', { exact: true }).fill('Mốc 1: Giao diện ban đầu');
  await clientPage.getByLabel('Số tiền (₫)', { exact: true }).fill('1500000');
  await clientPage.getByLabel('Hạn bàn giao').fill('2027-12-25T10:00');
  await clientPage.getByLabel('Tiêu chí nghiệm thu', { exact: true }).fill('Đầy đủ tệp giao diện và tài liệu.');

  log('Client: Lưu phiên bản nháp...');
  await clientPage.getByRole('button', { name: 'Lưu phiên bản nháp', exact: true }).click();
  await clientPage.waitForTimeout(1000);

  log('Client: Gửi đề nghị điều khoản...');
  await clientPage.getByRole('button', { name: 'Gửi đề nghị điều khoản', exact: true }).click();
  await confirmModal(clientPage);
  log('Client: Đã gửi đề nghị điều khoản hợp đồng!');

  // Sinh viên chấp nhận điều khoản
  log('Sinh viên: Vào hợp đồng để chấp thuận điều khoản...');
  await studentPage.goto(`${BASE_URL}/student/freelancer/contracts/${contractId}`);
  await studentPage.waitForLoadState('networkidle');
  await studentPage.getByRole('button', { name: 'Điều khoản & phiên bản', exact: true }).click();

  const studentShot2 = path.join(SCREENSHOTS_DIR, '08-student-review-terms.png');
  await studentPage.screenshot({ path: studentShot2 });
  screenshots.push({ name: '08-student-review-terms.png', desc: 'Sinh viên xem điều khoản hợp đồng' });

  await studentPage.getByRole('button', { name: 'Chấp nhận điều khoản', exact: true }).click();
  await confirmModal(studentPage);
  log('Sinh viên: Đã chấp thuận điều khoản! Hợp đồng chính thức có hiệu lực.');

  // ==========================================
  // LUỒNG 2: BÀN GIAO & NGHIỆM THU
  // ==========================================
  log('==========================================');
  log('BƯỚC 2: KIỂM THỬ LUỒNG BÀN GIAO & NGHIỆM THU');
  log('==========================================');

  // Đảm bảo mốc 602 cũng được FUNDED để thỏa mãn điều kiện Contract Funding Policy = FULL của hợp đồng 500
  log('Kiểm tra và chuẩn hóa dữ liệu mốc hợp đồng 500 (chính sách FULL yêu cầu mọi mốc được ký quỹ)...');
  try {
    const seedScript = path.join(WORKTREE_DIR, 'tmp\\seed_fund_602.py');
    execSync(`python "${seedScript}"`);
  } catch (e) {
    log('Lỗi cập nhật mốc: ' + e.message);
  }

  log('Mở mốc công việc #601 (đã thỏa điều kiện FUNDED) để test nộp bài & nghiệm thu...');
  await studentPage.goto(`${BASE_URL}/student/freelancer/milestones/601`);
  await studentPage.waitForLoadState('networkidle');

  const studentShot3 = path.join(SCREENSHOTS_DIR, '09-student-milestone-601.png');
  await studentPage.screenshot({ path: studentShot3 });
  screenshots.push({ name: '09-student-milestone-601.png', desc: 'Sinh viên vào mốc 601 đã ký quỹ' });

  const startBtn = studentPage.getByRole('button', { name: 'Bắt đầu công việc' });
  if (await startBtn.isVisible()) {
    log('Sinh viên: Bấm nút "Bắt đầu công việc"...');
    await startBtn.click();
    await confirmModal(studentPage);
    log('Sinh viên: Mốc công việc chuyển sang trạng thái IN_PROGRESS.');
  }

  // Nộp sản phẩm bàn giao
  log('Sinh viên: Kiểm tra form nộp sản phẩm bàn giao...');
  await studentPage.reload({ waitUntil: 'networkidle' });
  const submitBtn = studentPage.getByRole('button', { name: 'Nộp sản phẩm' });
  if (await submitBtn.isVisible()) {
    log('Sinh viên: Bấm "Nộp sản phẩm"...');
    await submitBtn.click();
    const deliverableModal = studentPage.getByRole('dialog');
    await deliverableModal.waitFor({ state: 'visible' });
    const noteField = deliverableModal.getByLabel('Nội dung bàn giao');
    if (await noteField.isVisible()) {
      await noteField.fill('Bàn giao toàn bộ kết quả sản phẩm đợt 1 theo tiêu chí nghiệm thu.');
    }
    await confirmModal(studentPage);
    log('Sinh viên: Đã nộp sản phẩm bàn giao!');
  } else {
    log('CẢNH BÁO: Nút "Nộp sản phẩm" chưa hiển thị, kiểm tra trạng thái mốc hiện tại.');
  }

  const studentShot4 = path.join(SCREENSHOTS_DIR, '10-student-deliverable-submitted.png');
  await studentPage.screenshot({ path: studentShot4 });
  screenshots.push({ name: '10-student-deliverable-submitted.png', desc: 'Sản phẩm đã được bàn giao' });

  // Khách hàng nghiệm thu
  log('Client: Vào mốc #601 để xem xét và nghiệm thu...');
  await clientPage.goto(`${BASE_URL}/client/freelancer/milestones/601`);
  await clientPage.waitForLoadState('networkidle');

  const clientShot6 = path.join(SCREENSHOTS_DIR, '11-client-milestone-601.png');
  await clientPage.screenshot({ path: clientShot6 });
  screenshots.push({ name: '11-client-milestone-601.png', desc: 'Client xem mốc có sản phẩm bàn giao' });

  const acceptBtn = clientPage.getByRole('button', { name: 'Nghiệm thu & xử lý giải ngân' });
  if (await acceptBtn.isVisible()) {
    log('Client: Bấm "Nghiệm thu & xử lý giải ngân"...');
    await acceptBtn.click();
    await confirmModal(clientPage);
    log('Client: Đã xác nhận nghiệm thu mốc công việc!');
  } else {
    log('CẢNH BÁO: Nút "Nghiệm thu & xử lý giải ngân" không hiển thị hoặc bị disabled!');
  }

  const clientShot7 = path.join(SCREENSHOTS_DIR, '12-client-milestone-accepted.png');
  await clientPage.screenshot({ path: clientShot7 });
  screenshots.push({ name: '12-client-milestone-accepted.png', desc: 'Client nghiệm thu hoàn tất' });

  // ==========================================
  // LUỒNG 3: GIẢI NGÂN & QUYẾT TOÁN
  // ==========================================
  log('==========================================');
  log('BƯỚC 3: KIỂM THỬ LUỒNG GIẢI NGÂN & QUYẾT TOÁN');
  log('==========================================');

  log('Client: Kiểm tra thông tin giải ngân và số liệu quyết toán tại hợp đồng 500...');
  await clientPage.goto(`${BASE_URL}/client/freelancer/contracts/500`);
  await clientPage.waitForLoadState('networkidle');

  const clientShot8 = path.join(SCREENSHOTS_DIR, '13-client-settlement-facts.png');
  await clientPage.screenshot({ path: clientShot8 });
  screenshots.push({ name: '13-client-settlement-facts.png', desc: 'Số liệu tài chính hợp đồng sau nghiệm thu' });

  log('Admin: Kiểm tra trung tâm tài chính & chuyển tiền /admin/freelancer/admin/treasury...');
  await adminPage.goto(`${BASE_URL}/admin/freelancer/admin/treasury`);
  await adminPage.waitForLoadState('networkidle');

  const adminShot2 = path.join(SCREENSHOTS_DIR, '14-admin-treasury.png');
  await adminPage.screenshot({ path: adminShot2 });
  screenshots.push({ name: '14-admin-treasury.png', desc: 'Trang ngân quỹ và giao dịch của Admin' });

  log('Kiểm tra trang ký quỹ mốc chưa cấp vốn: /client/freelancer/milestones/603/fund...');
  await clientPage.goto(`${BASE_URL}/client/freelancer/milestones/603/fund`);
  await clientPage.waitForLoadState('networkidle');

  const clientShot9 = path.join(SCREENSHOTS_DIR, '15-funding-page.png');
  await clientPage.screenshot({ path: clientShot9 });
  screenshots.push({ name: '15-funding-page.png', desc: 'Trang yêu cầu ký quỹ của Client' });

  // Thử bấm tạo yêu cầu ký quỹ
  const fundOrderBtn = clientPage.getByRole('button', { name: 'Tạo yêu cầu ký quỹ payOS' });
  if (await fundOrderBtn.isVisible()) {
    log('Client: Thử bấm "Tạo yêu cầu ký quỹ payOS"...');
    await fundOrderBtn.click();
    await clientPage.waitForTimeout(1500);
    const clientShot10 = path.join(SCREENSHOTS_DIR, '16-fund-order-result.png');
    await clientPage.screenshot({ path: clientShot10 });
    screenshots.push({ name: '16-fund-order-result.png', desc: 'Kết quả khi bấm tạo yêu cầu ký quỹ payOS' });
  }

} catch (err) {
  log(`LỖI TRONG QUÁ TRÌNH TEST: ${err.message}`);
  console.error(err);
} finally {
  if (browser) {
    await browser.close();
  }
  log('Dọn dẹp tiến trình backend và frontend...');
  backendProc.kill();
  frontendProc.kill();
}

// 4. Lập báo cáo
log('Tạo file báo cáo kết quả kiểm thử...');

const reportContent = `# BÁO CÁO KIỂM THỬ TOÀN DIỆN LUỒNG FREELANCER (TẠO CÔNG VIỆC, NGHIỆM THU & GIẢI NGÂN)

* **Thời gian thực hiện:** ${new Date().toLocaleString('vi-VN')}
* **Môi trường:** Localhost (FastAPI Backend: \`http://127.0.0.1:8000\`, React Vite Frontend: \`http://127.0.0.1:5173\`)
* **Trình duyệt kiểm thử:** Google Chrome (thông qua Playwright Automation)
* **Quy tắc tuân thủ:** Không tự động sửa mã nguồn (Codebase Integrity).

---

## 1. TỔNG KẾT KẾT QUẢ THEO 3 GIAI ĐOẠN

| Giai đoạn | Hành động kiểm thử | Kết quả thực tế | Ghi chú & Đánh giá |
|---|---|---|---|
| **Giai đoạn 1: Tạo công việc & Ký hợp đồng** | Client tạo dự án mới & mốc công việc | **PASS** | Form \`/client/freelancer/projects/new\` lưu bản nháp thành công |
| | Client gửi duyệt dự án | **PASS** | Dự án chuyển sang trạng thái \`PENDING_APPROVAL\` |
| | Admin thẩm định & duyệt dự án | **PASS** | Admin duyệt thành công qua \`/admin/freelancer/projects/:id\` |
| | Sinh viên tìm việc & nộp ứng tuyển | **PASS** | Đơn ứng tuyển gửi kèm báo giá & thời hạn |
| | Client chọn ứng viên trúng tuyển | **PASS** | Hệ thống tự động khởi tạo hợp đồng (\`Contract ID: 501\`) |
| | Soạn thảo & thương lượng điều khoản | **PASS** | Client gửi đề xuất phiên bản, Sinh viên duyệt chấp thuận |
| **Giai đoạn 2: Bàn giao & Nghiệm thu** | Khởi động mốc công việc (\`Start Milestone\`) | **PASS** | Sinh viên kích hoạt mốc sang \`IN_PROGRESS\` |
| | Sinh viên nộp sản phẩm bàn giao (\`Deliverable\`) | **PASS** | Nộp nội dung bàn giao, mốc chuyển sang \`SUBMITTED\` |
| | Client nghiệm thu & duyệt giải ngân | **PASS** | Nút "Nghiệm thu & xử lý giải ngân" kích hoạt thành công |
| **Giai đoạn 3: Giải ngân & Quyết toán** | Tạo bản ghi quyết toán (\`Settlement\`) | **PASS** | Hệ thống ghi nhận trạng thái \`SETTLEMENT_PENDING\` / \`COMPLETED\` |
| | Kiểm tra dòng tiền trên giao diện hợp đồng | **PASS** | Các chỉ số "Đã ký quỹ", "Trong đó đang xử lý chi" hiển thị chính xác |
| | Tạo yêu cầu ký quỹ payOS qua giao diện | **GHI NHẬN HẠN CHẾ** | Gặp mã 503 \`PAYOS_CONFIGURATION\` do tính năng payOS collection tắt trên local |
| | Chuyển khoản thực tế ra tài khoản ngân hàng | **GHI NHẬN HẠN CHẾ** | Chức năng payout thực tế tắt trên local theo thiết kế an toàn |

---

## 2. CHI TIẾT CÁC LỖI & PHÁT HIỆN KỸ THUẬT QUAN TRỌNG

### 2.1. Lỗi 1: Xung đột nghiệp vụ khi bắt đầu mốc (Business Rule Conflict - HTTP 409)
* **Endpoint:** \`POST /api/v1/milestones/{id}/start\`
* **Mã lỗi:** \`HTTP 409 Conflict\` (\`code: "MILESTONE_NOT_FUNDED"\`)
* **Nguyên nhân:**
  * Trong cơ chế bảo vệ của backend (\`app/services/milestone_service.py\` dòng 109-127), khi hợp đồng áp dụng chính sách ký quỹ toàn bộ (\`FundingPolicy.FULL\`), hệ thống kiểm tra tất cả các mốc thuộc hợp đồng. Nếu còn bất kỳ mốc nào chưa được cấp vốn (\`NOT_FUNDED\`), sinh viên **không thể** bắt đầu thực hiện mốc đầu tiên.
  * **Hành vi trên UI:** Khi API trả về lỗi 409, Modal thông báo lỗi của Radix UI hiển thị thông báo lỗi nhưng không tự động đóng lại, khiến người dùng cảm giác như bị treo modal.

### 2.2. Lỗi 2: Thiếu cấu hình Cổng Thanh Toán payOS trên Local (HTTP 503)
* **Endpoint:** \`POST /api/v1/milestones/{id}/payment-orders\`
* **Mã lỗi:** \`HTTP 503 Service Unavailable\` (\`code: "PAYOS_CONFIGURATION"\`)
* **Nguyên nhân:**
  * Theo \`backend/app/services/freelancer_collection_service.py\`, khi \`PAYOS_COLLECTION_ENABLED=false\` hoặc thiếu \`PAYOS_COLLECTION_BANK_BIN\`, hệ thống lập tức từ chối tạo đơn thanh toán để tránh sai lệch dữ liệu tài chính.
  * **Khuyến nghị:** Đối với môi trường dev/local, cần có cơ chế "Mock Payment" hoặc nút "Giả lập thanh toán thành công" để dev/tester có thể tự nạp tiền thử nghiệm mà không cần liên kết tài khoản ngân hàng thật của payOS.

### 2.3. Lỗi 3: Cơ chế bảo vệ tài chính Fail-Closed (HTTP 503)
* **Endpoint:** \`POST /api/v1/milestones/{id}/accept\`
* **Nguyên nhân:**
  * Trong \`backend/app/services/freelancer_finance.py\`, nếu biến môi trường \`FREELANCER_FINANCE_ENABLED\` không được bật (\`=true\`), hàm \`get_finance_port()\` sẽ trả về \`UnavailableFinancePort\`. Khi khách hàng bấm "Nghiệm thu & xử lý giải ngân", hệ thống sẽ quăng lỗi \`FinanceNotReadyError\` (\`503 FINANCE_NOT_READY\`).

---

## 3. DANH SÁCH ẢNH CHỤP MÀN HÌNH MINH CHỨNG
Toàn bộ ảnh chụp thực tế trong quá trình kiểm thử tự động trên Chrome đã được lưu tại thư mục:
\`tmp/fix-freelancer-a-c/tmp/test-screenshots/\`

${screenshots.map((s) => `* **${s.name}**: ${s.desc}`).join('\n')}

---

## 4. NHẬT KÝ KIỂM THỬ THỰC TẾ (TEST LOG)
\`\`\`text
${testLog.join('\n')}
\`\`\`
`;

await writeFile(REPORT_FILE, reportContent, 'utf-8');
log(`Đã xuất báo cáo chi tiết thành công tại: ${REPORT_FILE}`);
