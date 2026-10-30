import { describe, expect, it } from 'vitest'
import { getNotificationTargetUrl } from './notification-navigation'

describe('notification-navigation smart routing', () => {
  it('routes APPLICATION notifications correctly based on role', () => {
    expect(getNotificationTargetUrl({ ref_type: 'APPLICATION', ref_id: 12 }, 'STUDENT')).toBe('/student/applications')
    expect(getNotificationTargetUrl({ ref_type: 'APP_SUBMITTED', ref_id: 12 }, 'COMPANY')).toBe('/company/applications')
    expect(getNotificationTargetUrl({ ref_type: 'APPLICATION', ref_id: 12 }, 'ADMIN')).toBe('/admin/students')
  })

  it('routes COMPANY / MOU notifications correctly based on role', () => {
    expect(getNotificationTargetUrl({ ref_type: 'COMPANY_REGISTRATION', ref_id: 5 }, 'ADMIN')).toBe('/admin/companies')
    expect(getNotificationTargetUrl({ ref_type: 'MOU_VERIFIED', ref_id: 5 }, 'COMPANY')).toBe('/company/profile')
    expect(getNotificationTargetUrl({ ref_type: 'COMPANY', ref_id: 5 }, 'STUDENT')).toBe('/student/companies/5')
  })

  it('routes JOB notifications with ref_id correctly', () => {
    expect(getNotificationTargetUrl({ ref_type: 'JOB_APPROVED', ref_id: 42 }, 'STUDENT')).toBe('/student/jobs/42')
    expect(getNotificationTargetUrl({ ref_type: 'JOB_REJECTED', ref_id: 42 }, 'COMPANY')).toBe('/company/jobs/42')
    expect(getNotificationTargetUrl({ ref_type: 'JOB_PENDING_APPROVAL', ref_id: 42 }, 'ADMIN')).toBe('/admin/jobs')
  })

  it('routes INVITATION / INTERVIEW notifications correctly', () => {
    expect(getNotificationTargetUrl({ ref_type: 'INVITATION', ref_id: 8 }, 'STUDENT')).toBe('/student/invitations')
    expect(getNotificationTargetUrl({ ref_type: 'INTERVIEW_SCHEDULED', ref_id: 8 }, 'STUDENT')).toBe('/student/invitations')
    expect(getNotificationTargetUrl({ ref_type: 'INVITATION_ACCEPTED', ref_id: 8 }, 'COMPANY')).toBe('/company/invitations')
  })

  it('routes INTERNSHIP / TERM notifications correctly', () => {
    expect(getNotificationTargetUrl({ ref_type: 'INTERNSHIP_TERM_OPEN', ref_id: 1 }, 'STUDENT')).toBe('/student/internships')
    expect(getNotificationTargetUrl({ ref_type: 'TERM_EVALUATION', ref_id: 1 }, 'ADMIN')).toBe('/admin/internships')
  })

  it('falls back to /login when role is absent', () => {
    expect(getNotificationTargetUrl({ ref_type: 'APPLICATION', ref_id: 1 }, null)).toBe('/login')
  })
})
