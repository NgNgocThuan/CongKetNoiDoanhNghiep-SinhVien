/** Các cột file import sinh viên (khớp backend) và file CSV mẫu tải về từ trình duyệt. */
export const IMPORT_COLUMNS = [
  { name: 'student_code', label: 'Mã sinh viên', required: true, note: 'Duy nhất. Trùng mã sẽ cập nhật sinh viên cũ' },
  { name: 'full_name', label: 'Họ và tên', required: true, note: '' },
  { name: 'email', label: 'Email', required: true, note: 'Dùng để gửi liên kết kích hoạt tài khoản' },
  { name: 'faculty', label: 'Khoa', required: true, note: 'Mã hoặc tên khoa có trong Danh mục' },
  { name: 'major', label: 'Ngành', required: true, note: 'Mã hoặc tên ngành, phải thuộc khoa đã ghi' },
  { name: 'cohort', label: 'Khóa học', required: true, note: 'Ví dụ K65' },
  { name: 'date_of_birth', label: 'Ngày sinh', required: false, note: 'dd/mm/yyyy hoặc yyyy-mm-dd' },
  { name: 'class_name', label: 'Lớp', required: false, note: '' },
  { name: 'gpa', label: 'GPA', required: false, note: 'Thang 4, từ 0 đến 4' },
  { name: 'academic_result', label: 'Xếp loại', required: false, note: '' },
  { name: 'phone', label: 'Điện thoại', required: false, note: '' },
] as const

export const MAX_IMPORT_MB = 10

export function buildTemplateCsv(): string {
  const header = IMPORT_COLUMNS.map((c) => c.name).join(',')
  const sample = ['SV001', 'Nguyễn Văn A', 'sv001@school.edu.vn', 'CNTT', 'KTPM', 'K65', '15/05/2003', 'K65A', '3.2', 'Khá', '0900000000']
  // BOM giúp Excel mở đúng tiếng Việt
  return '﻿' + header + '\n' + sample.join(',') + '\n'
}

export function downloadTemplate(): void {
  const blob = new Blob([buildTemplateCsv()], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'mau-import-sinh-vien.csv'
  a.click()
  URL.revokeObjectURL(url)
}

/** Kiểm tra file phía trình duyệt trước khi gửi; trả thông báo lỗi hoặc null nếu hợp lệ. */
export function validateImportFile(file: { name: string; size: number }): string | null {
  const lower = file.name.toLowerCase()
  if (!lower.endsWith('.xlsx') && !lower.endsWith('.csv')) return 'Chỉ hỗ trợ file .xlsx hoặc .csv'
  if (file.size > MAX_IMPORT_MB * 1024 * 1024) return `File vượt quá ${MAX_IMPORT_MB}MB`
  if (file.size === 0) return 'File rỗng'
  return null
}
