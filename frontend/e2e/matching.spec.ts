import { expect, test } from '@playwright/test'
import type { Page, Route } from '@playwright/test'

const match = (jobId = 11, studentId = 31) => ({
  id: jobId + studentId, student_id: studentId, job_id: jobId, cv_id: 7, passed_rules: true,
  score: '86.50', skill_score: '90.00', experience_score: null, semantic_score: '65.00',
  matched_skills: ['Python', 'FastAPI'], missing_skills: ['Docker'],
  explanation: 'Kỹ năng Python phù hợp với yêu cầu của tin.', computed_at: '2026-10-30T08:00:00Z',
})
const job = (id = 11) => ({
  id, title: id === 11 ? 'Thực tập sinh Backend Python' : 'Frontend React Developer',
  position: 'Developer', location: 'Hà Nội', work_mode: 'HYBRID', quantity: 3,
  salary_min: 0, salary_max: 9000000, is_salary_negotiable: false, deadline: '2027-12-31',
  status: 'APPROVED', term_id: null, company: { id: 2, name: 'Công ty Kết Nối', logo_url: null },
  job_type: { id: 1, code: 'INTERN', name: 'Thực tập' }, description: 'Tham gia phát triển phần mềm.',
  requirements: 'Có kỹ năng Python.', benefits: null, min_gpa: null, min_experience_months: null,
  skills: [{ skill_id: 1, is_required: true, skill: { id: 1, name: 'Python' } }],
})
const candidate = (jobId = 11, id = 31) => ({
  student_id: id, full_name: jobId === 11 ? 'Nguyễn Minh Anh' : 'Trần Ngọc Mai', major_id: 1,
  gpa: null, contact_email: null, contact_phone: null, achievements: [], match: match(jobId, id),
})
const paged = <T,>(items: T[], page = 1, pages = 1, total = items.length) => ({ items, total, page, size: 6, pages })
type Handler = (route: Route, url: URL) => Promise<boolean>
async function setup(page: Page, role: 'STUDENT' | 'COMPANY', handler?: Handler) {
  let saved = false
  const mutations: { path: string; method: string; body: unknown }[] = []
  const reads: string[] = []
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url()), path = url.pathname.replace('/api/v1', '')
    const send = async (data: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) })
    if (route.request().method() === 'GET') reads.push(path + url.search)
    if (['POST', 'DELETE'].includes(route.request().method()) && !path.startsWith('/auth')) mutations.push({ path, method: route.request().method(), body: route.request().postDataJSON() })
    if (handler && await handler(route, url)) return
    if (path === '/auth/login' || path === '/auth/refresh') return send({ access_token: 'a', refresh_token: 'r', token_type: 'bearer' })
    if (path === '/auth/me') return send({ id: 1, email: 'demo@test.com', role, status: 'ACTIVE', student: role === 'STUDENT' ? { id: 31, full_name: 'Nguyễn Minh Anh' } : null, company: role === 'COMPANY' ? { id: 2, name: 'Công ty Kết Nối' } : null, admin: null })
    if (path === '/notifications/unread-count') return send({ unread_count: 0 })
    if (path === '/matching/jobs/recommended') return send(paged([{ job_id: 11, title: job().title, company_id: 2, match: match() }]))
    if (path === '/companies/2') return send(job().company)
    if (path === '/jobs/me') return send(paged([job(), job(12)]))
    if (/^\/jobs\/\d+$/.test(path)) return send(job(Number(path.split('/')[2])))
    if (/^\/matching\/jobs\/\d+\/candidates$/.test(path)) { const id = Number(path.split('/')[3]); return send(paged([candidate(id)])) }
    if (path === '/catalog/majors/1') return send({ id: 1, name: 'Kỹ thuật phần mềm' })
    if (path === '/saved-jobs') return send(paged(saved ? [{ job: job(), saved_at: '2026-10-30T08:00:00Z' }] : []))
    if (path === '/saved-jobs/11') { saved = route.request().method() === 'POST'; return saved ? send({ job: job(), saved_at: '2026-10-30T08:00:00Z' }, 201) : route.fulfill({ status: 204 }) }
    if (path === '/cvs/me') return send([{ id: 6, title: 'CV cũ', is_default: false, type: 'ONLINE' }, { id: 7, title: 'CV Backend', is_default: true, type: 'ONLINE' }, { id: 8, title: 'CV tải lên trước đây', is_default: false, type: 'UPLOADED' }])
    if (path === '/applications' || path === '/invitations') return send({ id: 90 }, 201)
    return send({ error: { code: 'UNMOCKED', message: path } }, 404)
  })
  await page.goto('/login')
  await page.getByLabel('Địa chỉ email', { exact: true }).fill('demo@test.com')
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Password@123')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL(role === 'STUDENT' ? '/student' : '/company')
  return { mutations, reads }
}
const studentUrl = '/student/recommended', companyUrl = '/company/candidates'
test('student renders actual matching fields, saves/unsaves and submits the chosen CV', async ({ page }) => {
  const { mutations } = await setup(page, 'STUDENT')
  await page.goto(studentUrl)
  const card = page.locator('article.match-card').first()
  await expect(card.getByText('Phù hợp 86,5%')).toBeVisible()
  await expect(card.getByText('Công ty Kết Nối')).toBeVisible()
  await expect(page.locator('.match-desktop-panel').getByText('Kinh nghiệm', { exact: true })).toBeVisible()
  await card.getByRole('button', { name: 'Lưu việc làm', exact: true }).click()
  await expect(card.getByRole('button', { name: 'Bỏ lưu việc làm', exact: true })).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: 'Bỏ lưu việc làm', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Lưu việc làm', exact: true })).toBeVisible()
  await page.locator('article.match-card').getByRole('button', { name: 'Ứng tuyển', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Ứng tuyển', exact: true })
  await expect(dialog.getByLabel('CV ứng tuyển')).toHaveValue('7')
  await expect(dialog.getByRole('option', { name: 'CV tải lên trước đây' })).toHaveCount(0)
  await dialog.getByLabel('Thư giới thiệu').fill('  Tôi quan tâm vị trí này.  ')
  await dialog.getByRole('button', { name: 'Gửi đơn ứng tuyển' }).click()
  await expect(dialog.getByRole('heading', { name: 'Đã gửi đơn ứng tuyển' })).toBeVisible()
  expect(mutations.filter(item => item.path === '/applications')).toEqual([{ path: '/applications', method: 'POST', body: { job_id: 11, cv_id: 7, cover_letter: 'Tôi quan tâm vị trí này.' } }])
  expect(mutations.filter(item => item.path === '/saved-jobs/11').map(item => item.method)).toEqual(['POST', 'DELETE'])
  await dialog.getByRole('button', { name: 'Hoàn tất' }).click()
  await expect(page.locator('article.match-card').getByRole('button', { name: 'Ứng tuyển', exact: true })).toBeFocused()
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: 'test-results/matching-student-desktop.png', fullPage: true })
})
test('student can inspect original job without routing into an unfinished page', async ({ page }) => {
  const { reads } = await setup(page, 'STUDENT'); await page.goto(studentUrl)
  await expect(page.locator('article.match-card')).toBeVisible()
  expect(reads.some(path => path === '/jobs/11')).toBe(false)
  await page.locator('article.match-card').getByRole('button', { name: 'Xem tin', exact: true }).click()
  await expect(page.getByRole('dialog', { name: 'Chi tiết tin tuyển dụng' }).getByText('Tham gia phát triển phần mềm.')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
})
test('company requires selecting a job, preserves privacy and sends an invitation for that job', async ({ page }) => {
  const { reads, mutations } = await setup(page, 'COMPANY')
  await page.goto(companyUrl)
  await expect(page.getByRole('heading', { name: 'Chưa chọn tin tuyển dụng' })).toBeVisible()
  expect(reads.some(path => path.includes('/candidates'))).toBe(false)
  await page.getByLabel('Chọn tin tuyển dụng', { exact: true }).selectOption('11')
  await expect(page.locator('article.match-card').getByRole('heading', { name: 'Nguyễn Minh Anh' })).toBeVisible()
  const panel = page.locator('.match-desktop-panel')
  await expect(panel.getByText('Không chia sẻ', { exact: true })).toHaveCount(3)
  await expect(panel.getByText('Kỹ thuật phần mềm', { exact: true })).toBeVisible()
  await page.screenshot({ path: 'test-results/matching-company-desktop.png', fullPage: true })
  await page.getByLabel('Chọn tin tuyển dụng', { exact: true }).selectOption('12')
  await expect(page.locator('article.match-card').getByRole('heading', { name: 'Trần Ngọc Mai' })).toBeVisible()
  await expect(page.locator('article.match-card').getByRole('heading', { name: 'Nguyễn Minh Anh' })).toHaveCount(0)
  await page.locator('article.match-card').getByRole('button', { name: 'Mời ứng tuyển', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Mời ứng tuyển', exact: true })
  await expect(dialog.getByText('Frontend React Developer', { exact: true })).toBeVisible()
  await dialog.getByLabel('Lời nhắn').fill(' Mời bạn tham gia ứng tuyển. ')
  await dialog.getByRole('button', { name: 'Gửi lời mời', exact: true }).click()
  await expect(dialog.getByRole('heading', { name: 'Đã gửi lời mời' })).toBeVisible()
  expect(mutations.filter(item => item.path === '/invitations')).toEqual([{ path: '/invitations', method: 'POST', body: { job_id: 12, student_id: 31, message: 'Mời bạn tham gia ứng tuyển.' } }])
  await dialog.getByRole('button', { name: 'Hoàn tất' }).click()
  await expect(page.locator('article.match-card').getByRole('button', { name: 'Đã gửi lời mời' })).toBeDisabled()
  await page.reload()
  await expect(page.getByLabel('Chọn tin tuyển dụng', { exact: true })).toHaveValue('12')
})
test('backend duplicate invitation error stays visible and prevents resubmission', async ({ page }) => {
  const { mutations } = await setup(page, 'COMPANY', async (route, url) => {
    if (url.pathname.endsWith('/invitations')) { await route.fulfill({ status: 409, json: { error: { code: 'DUPLICATE_INVITATION', message: 'Đã gửi lời mời cho sinh viên này với tin tuyển dụng này rồi' } } }); return true } return false
  })
  await page.goto(companyUrl + '?job_id=11')
  await page.locator('article.match-card').getByRole('button', { name: 'Mời ứng tuyển', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Mời ứng tuyển', exact: true })
  await dialog.getByRole('button', { name: 'Gửi lời mời' }).click()
  await expect(dialog.getByRole('alert')).toContainText('Đã gửi lời mời')
  await expect(dialog.getByRole('button', { name: 'Gửi lời mời' })).toBeDisabled()
  expect(mutations.filter(item => item.path === '/invitations')).toHaveLength(1)
})
test('no CV and duplicate application are handled without a false success', async ({ page }) => {
  let empty = true
  await setup(page, 'STUDENT', async (route, url) => {
    if (url.pathname.endsWith('/cvs/me') && empty) { await route.fulfill({ json: [] }); return true }
    if (url.pathname.endsWith('/applications')) { await route.fulfill({ status: 409, json: { error: { code: 'DUPLICATE_APPLICATION', message: 'Bạn đã ứng tuyển tin này' } } }); return true } return false
  })
  await page.goto(studentUrl)
  await page.locator('article.match-card').getByRole('button', { name: 'Ứng tuyển', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Bạn chưa có CV' })).toBeVisible()
  empty = false; await page.reload()
  await page.locator('article.match-card').getByRole('button', { name: 'Ứng tuyển', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Ứng tuyển', exact: true })
  await dialog.getByRole('button', { name: 'Gửi đơn ứng tuyển' }).click()
  await expect(dialog.getByRole('alert')).toHaveText('Bạn đã ứng tuyển tin này')
  await expect(dialog.getByRole('button', { name: 'Gửi đơn ứng tuyển' })).toBeDisabled()
})
test('matching errors can be retried and empty results are not fabricated', async ({ page }) => {
  let failed = true
  await setup(page, 'STUDENT', async (route, url) => {
    if (url.pathname.endsWith('/matching/jobs/recommended')) {
      await route.fulfill(failed ? { status: 400, json: { error: { code: 'AI_UNAVAILABLE', message: 'Không thể phân tích dữ liệu AI' } } } : { json: paged([], 1, 0) }); return true
    } return false
  })
  await page.goto(studentUrl)
  await expect(page.getByRole('alert')).toContainText('Không thể phân tích dữ liệu AI')
  failed = false
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Chưa có việc làm phù hợp' })).toBeVisible()
  await expect(page.locator('article.match-card')).toHaveCount(0)
})
test('pagination is server-side and browser back restores the selected job', async ({ page }) => {
  const { reads } = await setup(page, 'COMPANY', async (route, url) => {
    if (url.pathname.endsWith('/candidates') && url.pathname.includes('/11/')) {
      const current = Number(url.searchParams.get('page'))
      await route.fulfill({ json: paged([candidate(11, current === 1 ? 31 : 32)], current, 2, 7) }); return true
    } return false
  })
  await page.goto(companyUrl + '?job_id=11')
  await page.getByRole('button', { name: 'Trang sau', exact: true }).click()
  await expect(page).toHaveURL(/job_id=11&page=2/)
  await expect.poll(() => reads.some(path => path.includes('/11/candidates?page=2&size=6'))).toBe(true)
  await page.getByLabel('Chọn tin tuyển dụng', { exact: true }).selectOption('12')
  await expect(page).toHaveURL(/job_id=12$/)
  await page.goBack()
  await expect(page.getByLabel('Chọn tin tuyển dụng', { exact: true })).toHaveValue('11')
  await expect(page).toHaveURL(/page=2/)
})
for (const role of ['STUDENT', 'COMPANY'] as const) {
  test('mobile matching details and actions: ' + role, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await setup(page, role)
    await page.goto(role === 'STUDENT' ? studentUrl : companyUrl + '?job_id=11')
    const card = page.locator('article.match-card')
    await card.getByRole('button', { name: role === 'STUDENT' ? 'Vì sao được gợi ý?' : 'Xem mức độ phù hợp', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog.getByRole('heading', { name: 'Điểm thành phần' })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: 'test-results/matching-' + role.toLowerCase() + '-mobile-detail.png', fullPage: true })
    await page.keyboard.press('Escape')
    await expect(dialog).toHaveCount(0)
    await expect(card.getByRole('button', { name: role === 'STUDENT' ? 'Vì sao được gợi ý?' : 'Xem mức độ phù hợp', exact: true })).toBeFocused()
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.screenshot({ path: 'test-results/matching-' + role.toLowerCase() + '-mobile.png', fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  })
}
test('a forbidden job never starts candidate matching', async ({ page }) => {
  const { reads } = await setup(page, 'COMPANY', async (route, url) => {
    if (url.pathname.endsWith('/jobs/999')) { await route.fulfill({ status: 404, json: { error: { code: 'NOT_FOUND', message: 'Không tìm thấy tin tuyển dụng' } } }); return true } return false
  })
  await page.goto(companyUrl + '?job_id=999')
  await expect(page.getByRole('alert')).toContainText('Không tìm thấy tin tuyển dụng')
  expect(reads.some(path => path.includes('/999/candidates'))).toBe(false)
  await page.goto(companyUrl + '?job_id=-1')
  await expect(page.getByRole('heading', { name: 'Chưa chọn tin tuyển dụng' })).toBeVisible()
})
