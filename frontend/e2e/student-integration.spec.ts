import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const job = { id: 11, title: 'Cơ hội React', position: 'Developer', term_id: null, location: 'Hà Nội', work_mode: 'ONSITE', quantity: 1, salary_min: null, salary_max: null, is_salary_negotiable: true, deadline: '2027-12-31', status: 'APPROVED', created_at: '2026-10-31T00:00:00', company: { id: 3, name: 'Công ty thử' }, job_type: { id: 1, name: 'Thực tập' }, description: 'Mô tả', skills: [], majors: [] }
const paged = (items: unknown[]) => ({ items, total: items.length, page: 1, size: 12, pages: items.length ? 1 : 0 })
async function setup(page: Page) {
  let saved = false
  const calls: { path: string; method: string; data: unknown }[] = []
  const application = { id: 99, job_id: 11, cv_id: 7, current_status: 'APPLIED', applied_at: '2026-10-31T00:00:00', job, cv: { id: 7, title: 'CV online' }, status_logs: [], cover_letter: null }
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '')
    calls.push({ path, method: request.method(), data: request.postDataJSON() })
    let data: unknown
    if (path === '/auth/login' || path === '/auth/refresh') data = { access_token: 'a', refresh_token: 'r', token_type: 'bearer' }
    else if (path === '/auth/me') data = { id: 1, email: 'test@example.com', role: 'STUDENT', status: 'ACTIVE', student: { id: 1, full_name: 'Sinh viên thử' } }
    else if (path === '/notifications/unread-count') data = { unread_count: 0 }
    else if (path.startsWith('/catalog/')) data = paged([])
    else if (path === '/jobs') data = paged([job])
    else if (path === '/jobs/11') data = job
    else if (path === '/saved-jobs') data = paged(saved ? [{ job, saved_at: '2026-10-31' }] : [])
    else if (path === '/saved-jobs/11') { saved = request.method() === 'POST'; data = { job } }
    else if (path === '/invitations/me') data = paged([{ id: 21, job_id: 11, company_id: 3, student_id: 1, status: 'PENDING', message: 'Lời mời thử', created_at: '2026-10-31T00:00:00' }])
    else if (path === '/companies/3') data = { id: 3, name: 'Công ty thử' }
    else if (path === '/cvs/me') data = [{ id: 8, type: 'UPLOADED', title: 'CV tải lên', is_default: true }, { id: 7, type: 'ONLINE', title: 'CV online', is_default: false }]
    else if (path === '/applications' || path === '/applications/99') data = application
    else throw new Error('Unexpected API request ' + request.method() + ' ' + path)
    await route.fulfill({ json: data })
  })
  await page.goto('/login')
  await page.locator('#email').fill('test@example.com')
  await page.locator('#password').fill('Password@123')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL('/student')
  return calls
}

test('Viet Anh job cards share save state and can immediately unsave', async ({ page }) => {
  const calls = await setup(page)
  await page.goto('/student/jobs')
  await page.getByRole('button', { name: 'Lưu việc làm', exact: true }).click()
  await page.getByRole('button', { name: 'Bỏ lưu việc làm', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Lưu việc làm', exact: true })).toBeVisible()
  expect(calls.filter(call => call.path === '/saved-jobs/11').map(call => call.method)).toEqual(['POST', 'DELETE'])
})

test('invitations do not count job views and application uses only online CV with invitation ID', async ({ page }) => {
  const calls = await setup(page)
  await page.goto('/student/invitations')
  await expect(page.getByText('Lời mời thử', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Ứng tuyển theo lời mời', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Nộp đơn ứng tuyển', exact: true })
  await expect(dialog.getByLabel('CV ứng tuyển')).toHaveValue('7')
  await expect(dialog.getByRole('option', { name: 'CV tải lên' })).toHaveCount(0)
  expect(calls.filter(call => call.path.startsWith('/jobs/'))).toHaveLength(0)
  await dialog.getByRole('button', { name: 'Gửi đơn ứng tuyển', exact: true }).click()
  await expect(page).toHaveURL('/student/applications/99')
  expect(calls.find(call => call.path === '/applications' && call.method === 'POST')?.data).toEqual({ job_id: 11, cv_id: 7, invitation_id: 21 })
})
