import type { Dayjs } from 'dayjs'
import type { StudentAcademicUpdate } from './types'

export interface FormValues {
  full_name: string
  date_of_birth: Dayjs | null
  class_name: string
  faculty_id: number
  major_id: number
  cohort: string
  gpa: number | null
  academic_result: string
  phone: string
}

export function toUpdateBody(values: FormValues): StudentAcademicUpdate {
  return {
    full_name: values.full_name.trim(),
    date_of_birth: values.date_of_birth ? values.date_of_birth.format('YYYY-MM-DD') : null,
    class_name: values.class_name?.trim() || null,
    faculty_id: values.faculty_id,
    major_id: values.major_id,
    cohort: values.cohort.trim(),
    gpa: values.gpa === null || values.gpa === undefined ? null : values.gpa.toFixed(2),
    academic_result: values.academic_result?.trim() || null,
    phone: values.phone?.trim() || null,
  }
}
