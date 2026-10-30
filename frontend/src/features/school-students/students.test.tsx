import { render, screen, within } from '@testing-library/react'
import dayjs from 'dayjs'
import { describe, expect, it } from 'vitest'
import { toUpdateBody } from './EditAcademicModal'
import ImportReport from './ImportReport'
import { buildTemplateCsv, IMPORT_COLUMNS, validateImportFile } from './importTemplate'
import type { ImportBatchDetail } from './types'

const batch = (over: Partial<ImportBatchDetail>): ImportBatchDetail => ({
  id: 1,
  type: 'STUDENTS',
  file_name: 'sv.csv',
  total_rows: 6,
  success_rows: 2,
  failed_rows: 4,
  imported_by: 1,
  created_at: '2026-10-30T12:00:00',
  errors: [],
  ...over,
})

describe('ImportReport', () => {
  it('giữ lại dòng thành công và liệt kê từng dòng lỗi kèm số dòng và lý do', () => {
    render(
      <ImportReport
        batch={batch({
          errors: [
            { row: 4, key: 'SV012', message: 'GPA 9.9 ngoài khoảng 0-4' },
            { row: 7, key: null, message: 'Thiếu mã sinh viên' },
          ],
        })}
      />,
    )
    expect(screen.getByText(/2 dòng đã được lưu, 4 dòng bị bỏ qua do lỗi/)).toBeInTheDocument()
    expect(screen.getByText('SV012')).toBeInTheDocument()
    expect(screen.getByText('GPA 9.9 ngoài khoảng 0-4')).toBeInTheDocument()
    expect(screen.getByText('Thiếu mã sinh viên')).toBeInTheDocument()
    // Số dòng trong file nằm cùng hàng với mã sinh viên và lý do lỗi
    const row = screen.getByText('SV012').closest('tr') as HTMLElement
    expect(within(row).getByText('4')).toBeInTheDocument()
  })

  it('toàn bộ thành công thì không có bảng lỗi', () => {
    render(<ImportReport batch={batch({ success_rows: 6, failed_rows: 0 })} />)
    expect(screen.getByText('Import thành công toàn bộ 6 dòng')).toBeInTheDocument()
    expect(screen.queryByText('Lý do lỗi')).not.toBeInTheDocument()
  })

  it('không dòng nào được lưu thì báo lỗi rõ ràng', () => {
    render(<ImportReport batch={batch({ success_rows: 0, failed_rows: 6, errors: [{ row: 2, key: 'A', message: 'x' }] })} />)
    expect(screen.getByText(/Không có dòng nào được import/)).toBeInTheDocument()
  })
})

describe('validateImportFile', () => {
  it('chỉ nhận .xlsx/.csv, không rỗng, không quá 10MB', () => {
    expect(validateImportFile({ name: 'a.csv', size: 10 })).toBeNull()
    expect(validateImportFile({ name: 'A.XLSX', size: 10 })).toBeNull()
    expect(validateImportFile({ name: 'a.txt', size: 10 })).toMatch(/\.xlsx hoặc \.csv/)
    expect(validateImportFile({ name: 'a.csv', size: 0 })).toMatch(/rỗng/)
    expect(validateImportFile({ name: 'a.csv', size: 11 * 1024 * 1024 })).toMatch(/10MB/)
  })
})

describe('file CSV mẫu', () => {
  it('có BOM UTF-8 và đủ các cột bắt buộc của backend', () => {
    const csv = buildTemplateCsv()
    expect(csv.startsWith('﻿')).toBe(true)
    const header = csv.replace('﻿', '').split('\n')[0].split(',')
    for (const required of ['student_code', 'full_name', 'email', 'faculty', 'major', 'cohort']) {
      expect(header).toContain(required)
    }
    expect(IMPORT_COLUMNS.filter((c) => c.required).map((c) => c.name)).toEqual([
      'student_code',
      'full_name',
      'email',
      'faculty',
      'major',
      'cohort',
    ])
  })
})

describe('toUpdateBody', () => {
  const values = {
    full_name: '  Nguyễn Văn A ',
    date_of_birth: dayjs('2003-05-15'),
    class_name: '',
    faculty_id: 1,
    major_id: 2,
    cohort: ' K65 ',
    gpa: 3.5,
    academic_result: '',
    phone: '',
  }

  it('cắt khoảng trắng, đổi ô trống thành null để xóa giá trị, GPA 2 chữ số thập phân', () => {
    expect(toUpdateBody(values)).toEqual({
      full_name: 'Nguyễn Văn A',
      date_of_birth: '2003-05-15',
      class_name: null,
      faculty_id: 1,
      major_id: 2,
      cohort: 'K65',
      gpa: '3.50',
      academic_result: null,
      phone: null,
    })
  })

  it('GPA trống gửi null chứ không phải 0', () => {
    expect(toUpdateBody({ ...values, gpa: null }).gpa).toBeNull()
    expect(toUpdateBody({ ...values, date_of_birth: null }).date_of_birth).toBeNull()
  })
})
