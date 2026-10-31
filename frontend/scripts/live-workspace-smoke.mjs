import { chromium, expect } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'

// Only the dedicated local demo is used. No requests are mocked.
const origin = 'http://127.0.0.1:5173'
const api = 'http://127.0.0.1:8000/api/v1'
const stamp = Date.now().toString()
const password = 'Password@123'
const output = path.resolve('../tmp/local-runtime/completion')
await mkdir(output, { recursive: true })
const browser = await chromium.launch({
  channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
  headless: true,
})
const pageErrors = []
const failures = []
async function request(endpoint, method = 'GET', data, token) {
  const response = await fetch(api + endpoint, {
    method,
    headers: {
      ...(data ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
    ...(data ? { body: JSON.stringify(data) } : {}),
  })
  if (!response.ok)
    throw new Error(
      method +
        ' ' +
        endpoint +
        ': HTTP ' +
        response.status +
        ' ' +
        (await response.text()),
    )
  return response.status === 204 ? null : response.json()
}
async function login(email, role) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  })
  const page = await context.newPage()
  page.on('pageerror', (error) => pageErrors.push(error.message))
  page.on('response', (response) => {
    if (
      response.url().includes('/api/v1/') &&
      response.status() >= 400 &&
      !response.url().endsWith('/analyze')
    )
      failures.push(response.status() + ' ' + response.url())
  })
  await page.goto(origin + '/login')
  await page.locator('#email').fill(email)
  await page.locator('#password').fill(password)
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL(origin + '/' + role)
  return { page, context }
}
async function completeAction(page, title) {
  const dialog = page.getByRole('dialog', { name: title, exact: true })
  await dialog.getByRole('button', { name: 'Xác nhận', exact: true }).click()
  await expect(dialog).toBeHidden()
}
try {
  const companyToken = (
    await request('/auth/login', 'POST', { email: 'hr@acme.vn', password })
  ).access_token
  const jobTypes = await request(
    '/catalog/job-types?size=100',
    'GET',
    undefined,
    companyToken,
  )
  const registered = await request('/auth/register-company', 'POST', {
    email: 'demo-' + stamp + '@example.com',
    password,
    company_name: 'Doanh nghiệp kiểm tra ' + stamp,
    tax_code: stamp,
  })
  const draft = await request(
    '/jobs',
    'POST',
    {
      title: 'Cơ hội kiểm tra ' + stamp,
      position: 'Frontend Developer',
      job_type_id: jobTypes.items[0].id,
      description: 'Công việc kiểm tra tích hợp trên cơ sở dữ liệu demo local.',
      deadline: '2027-12-31',
    },
    companyToken,
  )
  await request(
    '/jobs/' + draft.id + '/submit',
    'POST',
    undefined,
    companyToken,
  )

  const admin = await login('admin@school.edu.vn', 'admin')
  let page = admin.page
  for (const route of [
    'analytics',
    'users',
    'companies',
    'jobs',
    'reports',
    'email-logs',
    'students',
    'lecturers',
    'catalog',
    'internships',
  ]) {
    await page.goto(origin + '/admin/' + route)
    await expect(page.locator('main')).not.toContainText(
      'Tính năng đang được phát triển',
    )
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
    await expect(page.getByText('Đang tải…', { exact: true })).toHaveCount(0)
  }
  await page.goto(origin + '/admin/companies?q=' + stamp)
  await page
    .getByRole('row')
    .filter({ hasText: 'Doanh nghiệp kiểm tra ' + stamp })
    .getByRole('button', { name: 'Chi tiết' })
    .click()
  await page.getByRole('button', { name: 'Phê duyệt', exact: true }).click()
  await completeAction(page, 'Phê duyệt')
  await expect(page.getByRole('row').filter({ hasText: stamp })).toContainText(
    'Đã duyệt',
  )
  await page.goto(origin + '/admin/jobs?q=' + stamp)
  await page
    .getByRole('row')
    .filter({ hasText: stamp })
    .getByRole('button', { name: 'Chi tiết' })
    .click()
  await page.getByRole('button', { name: 'Phê duyệt', exact: true }).click()
  await completeAction(page, 'Phê duyệt')
  await expect(page.getByRole('row').filter({ hasText: stamp })).toHaveCount(0)
  await page.goto(origin + '/admin/users?q=demo-' + stamp)
  await page.getByRole('button', { name: 'Chi tiết', exact: true }).click()
  await page
    .getByRole('button', { name: 'Khóa tài khoản', exact: true })
    .click()
  await page
    .getByLabel('Lý do khóa')
    .fill('Kiểm tra khóa/mở khóa trên dữ liệu demo.')
  await completeAction(page, 'Khóa tài khoản')
  await expect(page.getByRole('row').filter({ hasText: stamp })).toContainText(
    'Đã khóa',
  )
  await page.getByRole('button', { name: 'Chi tiết', exact: true }).click()
  await page
    .getByRole('button', { name: 'Mở khóa tài khoản', exact: true })
    .click()
  await completeAction(page, 'Mở khóa tài khoản')
  await expect(page.getByRole('row').filter({ hasText: stamp })).toContainText(
    'Hoạt động',
  )
  await page.goto(origin + '/admin/analytics')
  await expect(
    page.getByRole('heading', { name: 'Khoảng thiếu kỹ năng', exact: true }),
  ).toBeVisible()
  const exportResponse = page.waitForResponse((r) =>
    r.url().includes('/admin/exports/dashboard.pdf'),
  )
  await page.getByRole('button', { name: 'Tải báo cáo', exact: true }).click()
  expect((await exportResponse).status()).toBe(200)
  await page.evaluate(() => scrollTo(0, 0))
  await page.screenshot({
    path: path.join(output, 'admin-dashboard.png'),
    fullPage: true,
  })
  console.log(
    'PASS admin: all menus, company/job approval, user lock/unlock, dashboard and real PDF export',
  )

  const student = await login('sv001@school.edu.vn', 'student')
  page = student.page
  for (const route of [
    'jobs',
    'profile',
    'cvs',
    'saved-jobs',
    'applications',
    'invitations',
    'internships',
  ]) {
    await page.goto(origin + '/student/' + route)
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
  }
  await page.goto(origin + '/student/profile')
  await page
    .getByLabel('Giới thiệu bản thân', { exact: true })
    .fill('Hồ sơ kiểm tra ' + stamp)
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click()
  await expect(
    page.getByText('Đã lưu thông tin và quyền riêng tư.', { exact: true }),
  ).toBeVisible()
  await page.reload()
  await expect(
    page.getByLabel('Giới thiệu bản thân', { exact: true }),
  ).toHaveValue('Hồ sơ kiểm tra ' + stamp)
  await page.goto(origin + '/student/cvs')
  await page.getByRole('button', { name: 'Tạo CV online', exact: true }).click()
  await expect(page.locator('input[type="file"]')).toHaveCount(0)
  await page.getByLabel('Tên CV').fill('CV kiểm tra ' + stamp)
  await page
    .getByLabel('Giới thiệu bản thân')
    .fill('Ứng tuyển vị trí phát triển phần mềm.')
  await page
    .getByLabel('Kỹ năng (phân cách bằng dấu phẩy)')
    .fill('React, TypeScript')
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Lưu CV online', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'CV kiểm tra ' + stamp, exact: true }),
  ).toBeVisible()
  const cvCard = page
    .locator('section.ws-panel')
    .filter({
      has: page.getByRole('heading', {
        name: 'CV kiểm tra ' + stamp,
        exact: true,
      }),
    })
  await cvCard
    .getByRole('button', { name: 'Đặt mặc định', exact: true })
    .click()
  await completeAction(page, 'Đặt CV mặc định')
  await expect(cvCard).toContainText('Mặc định')
  await cvCard
    .getByRole('button', { name: 'Phân tích CV', exact: true })
    .click()
  await expect(cvCard.getByRole('alert')).toBeVisible({ timeout: 30000 }) // AI deliberately unconfigured on this local demo.
  await page.goto(origin + '/student/jobs?q=' + stamp)
  await page.getByRole('link', { name: 'Xem chi tiết', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: draft.title, exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Ứng tuyển', exact: true }).click()
  await page
    .getByLabel('Thư giới thiệu')
    .fill('Ứng tuyển từ giao diện với CV mới.')
  await page
    .getByRole('button', { name: 'Gửi đơn ứng tuyển', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Đã gửi đơn ứng tuyển' }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Hoàn tất', exact: true }).click()
  await page
    .getByRole('button', { name: 'Báo cáo tin tuyển dụng', exact: true })
    .click()
  await page.getByLabel('Nội dung phản ánh').fill('Báo cáo kiểm tra ' + stamp)
  await completeAction(page, 'Báo cáo vi phạm')
  await page.goto(origin + '/student/applications')
  await page
    .locator('section.ws-panel')
    .filter({ hasText: draft.title })
    .getByRole('link', { name: 'Chi tiết & lịch sử →' })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Lịch sử xử lý', exact: true }),
  ).toBeVisible()
  await page.screenshot({
    path: path.join(output, 'student-application.png'),
    fullPage: true,
  })
  console.log(
    'PASS student: all menus, persisted profile, online CV/default, AI error, job search/application and report',
  )

  const company = await login('hr@acme.vn', 'company')
  page = company.page
  await page.goto(origin + '/company/profile')
  await page
    .getByLabel('Địa chỉ', { exact: true })
    .fill('Hà Nội · kiểm tra ' + stamp)
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click()
  await expect(page.getByText('Đã lưu hồ sơ.', { exact: true })).toBeVisible()
  await page.goto(origin + '/company/jobs')
  await page
    .getByRole('button', { name: 'Tạo tin tuyển dụng', exact: true })
    .click()
  await page.getByLabel('Tiêu đề').fill('Tin từ giao diện ' + stamp)
  await page.getByLabel('Vị trí', { exact: false }).fill('Backend Developer')
  await page
    .getByLabel('Loại hình', { exact: false })
    .first()
    .selectOption(String(jobTypes.items[0].id))
  await page.getByLabel('Hạn nộp').fill('2027-12-31')
  await page
    .getByLabel('Mô tả công việc')
    .fill('Tin được tạo và sửa qua giao diện thật.')
  await page.getByRole('button', { name: 'Lưu nháp', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  const createdRow = page
    .getByRole('row')
    .filter({ hasText: 'Tin từ giao diện ' + stamp })
  await createdRow
    .getByRole('button', { name: 'Chỉnh sửa', exact: true })
    .click()
  await page.getByLabel('Tiêu đề').fill('Tin đã sửa ' + stamp)
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Lưu thay đổi', exact: true })
    .click()
  await expect(
    page.getByRole('row').filter({ hasText: 'Tin đã sửa ' + stamp }),
  ).toBeVisible()
  await page.goto(origin + '/company/jobs/' + draft.id + '/stats')
  await expect(
    page.getByRole('heading', { name: 'Đơn theo trạng thái', exact: true }),
  ).toBeVisible()
  await page.goto(origin + '/company/applications?job_id=' + draft.id)
  await page
    .getByRole('button', { name: 'Chi tiết & xử lý', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Lịch sử xử lý', exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Sơ loại', exact: true }).click()
  await page
    .getByRole('button', { name: 'Xác nhận chuyển trạng thái', exact: true })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Trạng thái: Sơ loại', exact: true }),
  ).toBeVisible()
  const cvResponse = page.waitForResponse((r) =>
    /\/company\/applications\/\d+\/cv/.test(r.url()),
  )
  await page.getByRole('button', { name: 'Tải CV đã nộp', exact: true }).click()
  expect((await cvResponse).status()).toBe(200)
  await page.getByRole('button', { name: 'Đóng', exact: true }).click()
  await page.getByRole('button', { name: 'Kanban', exact: true }).click()
  await expect(
    page.locator('.ws-kanban-column').filter({ hasText: 'Sơ loại' }),
  ).toContainText('Nguyễn Văn A')
  await page.screenshot({
    path: path.join(output, 'company-kanban.png'),
    fullPage: true,
  })
  console.log(
    'PASS company: full profile, create/edit job, statistics, real applicant history/status and snapshot CV, Kanban',
  )

  page = admin.page
  await page.goto(origin + '/admin/reports')
  await page
    .getByRole('row')
    .filter({ hasText: 'Báo cáo kiểm tra ' + stamp })
    .getByRole('button', { name: 'Chi tiết' })
    .click()
  await page.getByRole('button', { name: 'Xử lý báo cáo', exact: true }).click()
  await page.getByLabel('Kết quả', { exact: false }).selectOption('REJECTED')
  await page
    .getByLabel('Ghi chú xử lý')
    .fill('Báo cáo dùng kiểm thử local, không phải vi phạm thật.')
  await completeAction(page, 'Xử lý báo cáo')
  await expect(
    page.getByRole('row').filter({ hasText: 'Báo cáo kiểm tra ' + stamp }),
  ).toContainText('Đã từ chối')
  for (const [session, route] of [
    [student, '/student/jobs'],
    [company, '/company/applications?job_id=' + draft.id],
    [admin, '/admin/analytics'],
  ]) {
    await session.page.setViewportSize({ width: 390, height: 844 })
    await session.page.goto(origin + route)
    await expect(
      session.page.getByRole('heading', { level: 1 }).first(),
    ).toBeVisible()
    await session.page.waitForTimeout(400)
    expect(
      await session.page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true)
    await session.page.screenshot({
      path: path.join(output, route.split('/')[1] + '-mobile.png'),
      fullPage: true,
    })
  }
  expect(pageErrors).toEqual([])
  expect(failures).toEqual([])
  console.log(
    'PASS report resolution, mobile layouts for three roles; no unexpected API or JavaScript errors',
  )
  console.log('Screenshots: ' + output)
  console.log('Synthetic company ID: ' + registered.company_id)
  await admin.context.close()
  await student.context.close()
  await company.context.close()
} finally {
  await browser.close()
}
