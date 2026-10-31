import { vi, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProfileForm } from './components/ProfileForm'
import { http } from '@/lib/http'
import type { Profile } from './types'
vi.mock('@/lib/http', () => ({
  http: { put: vi.fn().mockResolvedValue({ data: {} }) },
}))
it('saves only self-declared fields and explicit privacy flags', async () => {
  const profile: Profile = {
    student_id: 1,
    avatar_url: null,
    bio: 'Backend',
    career_goal: null,
    contact_email: null,
    contact_phone: null,
    address: null,
    linkedin_url: null,
    github_url: null,
    is_open_to_work: false,
    show_gpa: false,
    show_contact: false,
    show_achievements: true,
    updated_at: '2026-10-31T00:00:00',
  }
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ProfileForm profile={profile} />
    </QueryClientProvider>,
  )
  await userEvent.click(screen.getByRole('checkbox', { name: /Sẵn sàng tìm việc/ }))
  await userEvent.click(screen.getByRole('button', { name: 'Lưu thông tin & quyền riêng tư' }))
  await waitFor(() => expect(http.put).toHaveBeenCalled())
  const payload = vi.mocked(http.put).mock.calls[0][1] as Record<string, unknown>
  expect(payload.is_open_to_work).toBe(true)
  expect(payload.show_gpa).toBe(false)
  expect(payload).not.toHaveProperty('student_id')
  expect(payload).not.toHaveProperty('gpa')
  expect(payload).not.toHaveProperty('official')
})
