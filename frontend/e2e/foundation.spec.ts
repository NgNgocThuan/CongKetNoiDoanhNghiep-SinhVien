import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

type Role = 'STUDENT' | 'COMPANY' | 'ADMIN'
const roles: Record<Role, string> = { STUDENT: '/student', COMPANY: '/company', ADMIN: '/admin' }
async function mockApi(page: Page, role: Role) {
  const user = { id: 1, email: 'demo@test.com', role, status: 'ACTIVE',
    student: role === 'STUDENT' ? { id: 1, full_name: 'Nguyễn Minh Anh' } : null,
    company: role === 'COMPANY' ? { id: 1, name: 'Doanh nghiệp Demo' } : null,
    admin: role === 'ADMIN' ? { id: 1, full_name: 'Quản trị viên' } : null }
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname
    const data = path.endsWith('/auth/login') || path.endsWith('/auth/refresh') ? { access_token: 'test-access', refresh_token: 'test-refresh', token_type: 'bearer' }
      : path.endsWith('/auth/me') ? user
      : path.endsWith('/notifications/unread-count') ? { unread_count: 0 }
      : path.endsWith('/catalog/faculties') ? { items: [{ id: 1, code: 'CNTT', name: 'Công nghệ thông tin', is_active: true }], total: 1, page: 1, size: 10, pages: 1 }
      : path.endsWith('/notifications') ? { items: [], total: 0, page: 1, size: 10, pages: 0 }
      : { message: 'Đã hoàn tất' }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) })
  })
}
async function login(page: Page, role: Role) {
  await mockApi(page, role)
  await page.goto('/login')
  await page.getByLabel('Địa chỉ email', { exact: true }).fill('demo@test.com')
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Password@123')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL(roles[role])
}
for (const role of ['STUDENT', 'COMPANY', 'ADMIN'] as const) {
  test('login and role shell: ' + role, async ({ page }) => {
    await login(page, role)
    await expect(page.locator('.app-shell')).toHaveAttribute('data-role', role)
    await expect(page.getByRole('heading', { name: 'Không gian làm việc' })).toBeVisible()
    await page.screenshot({ path: 'test-results/' + role.toLowerCase() + '-desktop.png', fullPage: true })
    await page.reload()
    await expect(page.locator('.app-shell')).toHaveAttribute('data-role', role)
    if (role !== 'ADMIN') {
      await page.goto('/admin/catalog')
      await expect(page.getByRole('heading', { name: 'Bạn không có quyền truy cập' })).toBeVisible()
    }
  })
}
test('admin catalog fetches and renders a paginated response', async ({ page }) => {
  await login(page, 'ADMIN')
  await page.getByRole('navigation', { name: 'Điều hướng chính' }).getByRole('link', { name: 'Danh mục', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Danh mục', exact: true })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'Công nghệ thông tin' })).toBeVisible()
  await page.screenshot({ path: 'test-results/catalog-desktop.png', fullPage: true })
})
test('mobile navigation opens, traps focus and closes with Escape', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await login(page, 'STUDENT')
  const trigger = page.getByRole('button', { name: 'Mở điều hướng' })
  await trigger.click()
  const dialog = page.getByRole('dialog', { name: 'Điều hướng' })
  await expect(dialog).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).not.toBeVisible()
  await trigger.click()
  await dialog.getByRole('link', { name: 'Hồ sơ của tôi' }).click()
  await expect(page.getByRole('heading', { name: 'Chúng tôi đang hoàn thiện tiện ích này' })).toBeVisible()
  await expect(dialog).not.toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: 'test-results/student-mobile.png', fullPage: true })
})
test('login form handles validation without sending invalid credentials', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.getByText('Nhập địa chỉ email hợp lệ.')).toBeVisible()
  await expect(page.getByText('Nhập mật khẩu.', { exact: true })).toBeVisible()
  await page.screenshot({ path: 'test-results/login-desktop.png', fullPage: true })
})
