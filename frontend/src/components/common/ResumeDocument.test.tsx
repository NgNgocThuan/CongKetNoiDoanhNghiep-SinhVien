import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ResumeDocument } from './ResumeDocument'

describe('professional CV document', () => {
  it('renders identity, skills and readable sections instead of raw JSON', () => {
    render(<ResumeDocument title="Frontend CV" content={{ official: { full_name: 'Nguyễn Minh Anh', major_name: 'Kỹ thuật phần mềm', cohort: 'K65' }, skills: ['React', 'TypeScript'], summary: 'Phát triển giao diện web', experience: 'Frontend tại TechCorp', projects: [{ name: 'Student Connect', description: 'Cổng kết nối việc làm', id: 99 }] }} />)
    expect(screen.getByRole('heading', { level: 1, name: 'Nguyễn Minh Anh' })).toBeInTheDocument()
    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Kinh nghiệm làm việc' })).toBeInTheDocument()
    expect(screen.getByText('Student Connect')).toBeInTheDocument()
    expect(screen.queryByText('99')).not.toBeInTheDocument()
  })
  it('renders CV text safely and handles a missing profile', () => {
    const { container } = render(<ResumeDocument title="CV mới" content={{ summary: '<script>unsafe()</script>' }} />)
    expect(screen.getByText('<script>unsafe()</script>')).toBeInTheDocument()
    expect(container.querySelector('script')).toBeNull()
    expect(screen.getByText('Chưa cập nhật kỹ năng trong hồ sơ.')).toBeInTheDocument()
  })
})
