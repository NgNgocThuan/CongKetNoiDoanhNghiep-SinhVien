import { expect, test } from '@playwright/test'

test('CV uses read-only school data, only permits online creation and preserves additional information', async ({
  page,
}) => {
  const official = {
    student_code: 'SV001',
    full_name: 'Nguyễn Minh Anh',
    gpa: 0,
    cohort: 'K65',
    faculty: { id: 1, name: 'Công nghệ thông tin' },
    major: { id: 2, name: 'Kỹ thuật phần mềm' },
  }
  const profile = {
    official,
    self_declared: {
      profile: {
        bio: 'Giới thiệu từ hồ sơ',
        career_goal: 'Lập trình viên',
        contact_email: 'student@example.com',
      },
      skills: [{ name: 'React' }],
      experiences: [],
      projects: [],
    },
  }
  const cvs: Record<string, unknown>[] = [
    { id: 9, type: 'UPLOADED', title: 'CV tệp cũ', is_default: true },
  ]
  const created: Record<string, unknown>[] = []
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname.replace('/api/v1', '')
    let data: unknown
    if (path === '/auth/login' || path === '/auth/refresh')
      data = {
        access_token: 'access',
        refresh_token: 'refresh',
        token_type: 'bearer',
      }
    else if (path === '/auth/me')
      data = {
        id: 1,
        email: 'student@example.com',
        role: 'STUDENT',
        status: 'ACTIVE',
        student: { id: 1, full_name: official.full_name },
      }
    else if (path === '/notifications/unread-count') data = { unread_count: 0 }
    else if (path === '/students/me') data = profile
    else if (path === '/cvs/me') data = cvs
    else if (path === '/cvs/online' && request.method() === 'POST') {
      const body = request.postDataJSON() as Record<string, unknown>
      created.push(body)
      const cv = {
        ...body,
        id: 10,
        type: 'ONLINE',
        is_default: false,
        parsed_json: null,
        content_json: { ...(body.content_json as object), official },
      }
      cvs.push(cv)
      data = cv
    } else
      throw new Error(
        'Unexpected API request: ' + request.method() + ' ' + path,
      )
    await route.fulfill({ json: data })
  })
  await page.goto('/login')
  await page.locator('#email').fill('student@example.com')
  await page.locator('#password').fill('Password@123')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page).toHaveURL('/student')
  await page.goto('/student/cvs')
  await expect(page.getByText('CV tệp cũ', { exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Tạo CV online', exact: true }).click()
  const dialog = page.getByRole('dialog', {
    name: 'Tạo CV online',
    exact: true,
  })
  await expect(dialog.getByText('SV001', { exact: true })).toBeVisible()
  await expect(
    dialog.getByText('Kỹ thuật phần mềm', { exact: true }),
  ).toBeVisible()
  await expect(
    dialog.locator(
      'input[name="gpa"],input[name="full_name"],input[type="file"]',
    ),
  ).toHaveCount(0)
  await expect(dialog.getByLabel('Giới thiệu bản thân')).toHaveValue(
    'Giới thiệu từ hồ sơ',
  )
  await expect(
    dialog.getByLabel('Kỹ năng (phân cách bằng dấu phẩy)'),
  ).toHaveValue('React')
  await dialog.getByLabel('Tên CV').fill('CV ứng tuyển React')
  await dialog
    .getByLabel('Dự án', { exact: true })
    .fill('Ứng dụng quản lý thực tập')
  await dialog.getByRole('button', { name: 'Lưu CV online' }).click()
  await expect(dialog).toBeHidden()
  expect(created).toHaveLength(1)
  expect(created[0]).toMatchObject({
    title: 'CV ứng tuyển React',
    content_json: { skills: ['React'], projects: 'Ứng dụng quản lý thực tập' },
  })
  expect(created[0].content_json).not.toHaveProperty('official')
  await page.getByRole('button', { name: 'Xem CV', exact: true }).click()
  const preview = page.getByRole('dialog', {
    name: 'CV ứng tuyển React',
    exact: true,
  })
  await expect(
    preview.getByText('Nguyễn Minh Anh', { exact: true }),
  ).toBeVisible()
  await expect(preview.getByText('0', { exact: true })).toBeVisible()
  await expect(
    preview.getByText('Ứng dụng quản lý thực tập', { exact: true }),
  ).toBeVisible()
})
