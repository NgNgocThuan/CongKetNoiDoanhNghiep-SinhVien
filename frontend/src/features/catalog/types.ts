export interface Faculty {
  id: number
  code: string
  name: string
  is_active: boolean
}

export interface Major {
  id: number
  faculty_id: number
  code: string
  name: string
  is_active: boolean
}

export interface Industry {
  id: number
  name: string
  is_active: boolean
}

export interface JobType {
  id: number
  code: string
  name: string
  is_active: boolean
}

export interface Skill {
  id: number
  name: string
  category: string | null
  is_active: boolean
}

export interface SkillAlias {
  id: number
  skill_id: number
  alias: string
}

export type CatalogResource = 'faculties' | 'majors' | 'industries' | 'job-types' | 'skills'

export interface CatalogItemMap {
  faculties: Faculty
  majors: Major
  industries: Industry
  'job-types': JobType
  skills: Skill
}

/** Tham số lọc/phân trang chung của các API danh mục. */
export interface CatalogListParams {
  page?: number
  size?: number
  q?: string
  include_inactive?: boolean
  faculty_id?: number
  category?: string
}
