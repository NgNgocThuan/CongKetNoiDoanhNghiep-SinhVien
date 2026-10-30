import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
const academic = (id = 1) => ({
  id, user_id: id + 10, student_code: 'SV00' + id, full_name: 'Sinh viên ' + id, email: 'sv' + id + '@example.com', account_status: 'ACTIVE',
  date_of_birth: null, class_name: 'CNTT1', faculty_id: 1, faculty_name: 'Công nghệ thông tin', major_id: 1, major_name: 'Kỹ thuật phần mềm', cohort: 'K65', gpa: '3.20', academic_result: null, phone: null, synced_at: null,
})
const term = { id: 1, name: 'Thực tập HK1', semester: 'HK1', academic_year: '2026-2027', start_date: '2026-09-01', end_date: '2027-01-31', status: 'ONGOING', created_by: 1, created_at: '2026-09-01T00:00:00', student_count: 2 }
const result = (id: number) => ({
  id, term_id: 1, term_student_id: id, student_id: id, student_code: 'SV00' + id, student_name: 'Sinh viên ' + id,
  lecturer_id: null, lecturer_name: null, company_id: null, company_name: null, application_id: null,
  company_evaluation: null, company_score: null, evaluated_at: null,
  lecturer_comment: 'Nhận xét của sinh viên ' + id, lecturer_score: id === 1 ? '8.00' : '5.00', result: 'PENDING', confirmed_by: null, confirmed_at: null,
})
const paged = (items: unknown[]) => ({ items, total: items.length, page: 1, size: 20, pages: items.length ? 1 : 0 })
async function login(page: Page, role = 'ADMIN', expired = false) {
  const writes: { path: string; body: unknown }[] = [], reads: string[] = []
  let refreshes = 0
  const faculties = [{ id: 1, code: 'CNTT', name: 'Công nghệ thông tin', is_active: true }]
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    const method = route.request().method()
    if (method === 'GET') reads.push(path)
    if (['POST', 'PUT'].includes(method) && !path.startsWith('/auth')) writes.push({ path, body: route.request().postDataJSON() })
    const send = (data: unknown, status = 200) => route.fulfill({ status, json: data })
    if (path === '/auth/login' || path === '/auth/refresh') {
      if (path.endsWith('refresh')) refreshes++
      return send({ access_token: 'access-' + refreshes, refresh_token: 'refresh-' + refreshes, token_type: 'bearer' })
    }
    if (path === '/auth/me') return send({ id: 1, email: 'review@example.com', role, status: 'ACTIVE', admin: role === 'ADMIN' ? { id: 1, full_name: 'Quản trị' } : null, student: role === 'STUDENT' ? { id: 1, full_name: 'Sinh viên' } : null, company: role === 'COMPANY' ? { id: 1, name: 'Công ty' } : null })
    if (path === '/notifications/unread-count') return send({ unread_count: 0 })
    if (path === '/catalog/faculties' && method === 'POST') { const body = route.request().postDataJSON(); faculties.push({ id: 2, ...body, is_active: true }); return send(faculties[1], 201) }
    if (path === '/catalog/faculties') return send(paged(faculties))
    if (path === '/catalog/majors') return send(paged([{ id: 1, faculty_id: 1, code: 'SE', name: 'Kỹ thuật phần mềm', is_active: true }]))
    if (path.startsWith('/catalog/')) return send(paged([]))
    if (path === '/admin/students') {
      if (expired && refreshes === 0) return send({ error: { code: 'UNAUTHORIZED', message: 'Hết hạn phiên' } }, 401)
      return send(paged([academic(1), academic(2)]))
    }
    if (path === '/admin/students/1') return send({ official: { academic: academic(1), achievements: [], school_certificates: [] }, self_declared: { profile: null, skills: [], experiences: [], projects: [], certificates: [] } })
    if (path === '/admin/students/999') return send({ error: { code: 'NOT_FOUND', message: 'Không tìm thấy sinh viên' } }, 404)
    if (path === '/admin/students/imports') return send(paged([]))
    if (path === '/admin/lecturers') return send(paged([{ id: 1, code: 'GV01', full_name: 'Giảng viên mẫu', faculty_id: 1, email: null, phone: null, is_active: true }]))
    if (path === '/internship-terms') return send(paged([term]))
    if (path === '/internship-terms/1') return send(term)
    if (path === '/internship-terms/1/results') return send(paged([result(1), result(2)]))
    if (path.endsWith('/lecturer-review')) return send(result(2))
    if (path.startsWith('/internship-terms/1/')) return send(paged([]))
    return send({ error: { code: 'UNMOCKED', message: path } }, 404)
  })
  await page.goto('/login')
  await page.getByLabel('Địa chỉ email', { exact: true }).fill('review@example.com')
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Password@123')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL('/' + role.toLowerCase())
  return { writes, reads, refreshes: () => refreshes }
}
test('school screens use the shared Admin shell and real feature routes', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message))
  await login(page)
  const nav = page.getByRole('navigation', { name: 'Điều hướng chính' })
  await nav.getByRole('link', { name: 'Sinh viên', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Quản lý sinh viên', exact: true })).toBeVisible()
  await expect(page.getByRole('row').filter({ hasText: 'SV001' })).toContainText('Sinh viên 1')
  await expect(page.locator('.app-header')).toHaveCount(1)
  await expect(page.getByRole('main')).toHaveCount(1)
  await page.getByRole('row').filter({ hasText: 'SV001' }).getByRole('button', { name: 'Xem chi tiết' }).click()
  await expect(page).toHaveURL('/admin/students/1')
  await expect(page.locator('.header-breadcrumb strong')).toHaveText('Sinh viên')
  await expect(page.getByRole('tab', { name: 'Dữ liệu nhà trường' })).toBeVisible()
  await nav.getByRole('link', { name: 'Giảng viên', exact: true }).click()
  await expect(page.getByRole('cell', { name: 'Giảng viên mẫu' })).toBeVisible()
  await page.screenshot({ path: 'test-results/phong-shared-lecturers.png', fullPage: true })
  await nav.getByRole('link', { name: 'Đợt thực tập', exact: true }).click()
  await expect(page).toHaveURL('/admin/internships')
  await expect(page.getByRole('cell', { name: 'Thực tập HK1', exact: true })).toBeVisible()
  expect(errors).toEqual([])
})
test('catalog CRUD is inside the shared frame and uses the current API', async ({ page }) => {
  const { writes } = await login(page)
  await page.goto('/admin/catalog')
  await page.getByRole('button', { name: /Thêm khoa$/ }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('Mã khoa', { exact: true }).fill('KT')
  await dialog.getByLabel('Tên khoa', { exact: true }).fill('Kinh tế')
  await dialog.getByRole('button', { name: 'Lưu', exact: true }).click()
  await expect(page.getByRole('cell', { name: 'Kinh tế', exact: true })).toBeVisible()
  expect(writes).toContainEqual({ path: '/catalog/faculties', body: { code: 'KT', name: 'Kinh tế' } })
})
test('switching internship students submits only the selected student review', async ({ page }) => {
  const { writes } = await login(page)
  await page.goto('/admin/internships/1')
  await page.getByRole('tab', { name: 'Kết quả & đánh giá' }).click()
  await page.getByRole('row').filter({ hasText: 'SV001' }).getByRole('button', { name: 'Xử lý' }).click()
  await expect(page.getByRole('textbox', { name: 'Nhận xét', exact: true })).toHaveValue('Nhận xét của sinh viên 1')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('textbox', { name: 'Nhận xét', exact: true })).toHaveCount(0)
  await page.getByRole('row').filter({ hasText: 'SV002' }).getByRole('button', { name: 'Xử lý' }).click()
  await expect(page.getByRole('textbox', { name: 'Nhận xét', exact: true })).toHaveValue('Nhận xét của sinh viên 2')
  await page.getByRole('button', { name: 'Lưu nhận xét', exact: true }).click()
  await expect.poll(() => writes.some(item => item.path === '/internship-terms/results/2/lecturer-review')).toBe(true)
  expect(writes.find(item => item.path.endsWith('/lecturer-review'))?.body).toEqual({ comment: 'Nhận xét của sinh viên 2', score: '5.00' })
  await page.screenshot({ path: 'test-results/phong-shared-results.png', fullPage: true })
})
test('old internship URLs redirect to the current menu route', async ({ page }) => {
  await login(page)
  await page.goto('/admin/internship-terms/1')
  await expect(page).toHaveURL('/admin/internships/1')
  await expect(page.getByRole('heading', { name: 'Thực tập HK1', exact: true })).toBeVisible()
})
test('school requests share the existing refresh-token flow', async ({ page }) => {
  const state = await login(page, 'ADMIN', true)
  await page.goto('/admin/students')
  await expect(page.getByRole('cell', { name: 'SV001', exact: true })).toBeVisible()
  expect(state.refreshes()).toBeGreaterThanOrEqual(1)
  await expect(page).toHaveURL('/admin/students')
})
for (const role of ['STUDENT', 'COMPANY']) test('school routes reject ' + role, async ({ page }) => {
  const { reads } = await login(page, role)
  await page.goto('/admin/students')
  await expect(page.getByRole('heading', { name: 'Bạn không có quyền truy cập' })).toBeVisible()
  expect(reads.includes('/admin/students')).toBe(false)
})
test('school tables stay inside the shared mobile layout', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await login(page)
  await page.goto('/admin/students')
  await expect(page.getByRole('heading', { name: 'Quản lý sinh viên', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('button', { name: 'Mở điều hướng' }).click()
  await page.getByRole('dialog', { name: 'Điều hướng' }).getByRole('link', { name: 'Giảng viên', exact: true }).click()
  await expect(page.getByRole('cell', { name: 'Giảng viên mẫu' })).toBeVisible()
  await expect(page.locator('.app-header')).toHaveCount(1)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: 'test-results/phong-shared-mobile.png', fullPage: true })
})
test('school detail errors use shared normalized errors and can return to the list', async ({ page }) => {
  await login(page)
  await page.goto('/admin/students/999')
  await expect(page.getByText('Không tìm thấy sinh viên', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Về danh sách', exact: true }).click()
  await expect(page).toHaveURL('/admin/students')
})
