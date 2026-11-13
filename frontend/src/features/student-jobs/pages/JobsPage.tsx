import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { MapPin, Search, SlidersHorizontal, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState } from '@/components/common/States'
import { jobsApi } from '../api'
import { JobCard } from '../components/JobCard'
import { StudentPage, QueryState } from '../components/StudentUI'
import type { JobFilters } from '../types'

const formId = 'student-job-search'
const filterKeys = ['position', 'work_mode', 'major_id', 'industry_id', 'job_type_id', 'salary_from', 'salary_to', 'skill_ids']

export default function JobsPage() {
  const [search, setSearch] = useSearchParams()
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [filterError, setFilterError] = useState('')
  const page = Math.max(1, Number(search.get('page')) || 1)
  const activeCount = filterKeys.reduce((count, key) => count + search.getAll(key).filter(Boolean).length, 0)
  const filters: JobFilters = {
    ...Object.fromEntries([...search].filter(([key]) => !['flow', 'term_id'].includes(key))), page, size: 12,
    skill_ids: search.getAll('skill_ids'),
  }
  const query = useQuery({
    queryKey: ['student-jobs', filters],
    queryFn: ({ signal }) => jobsApi.search(filters, signal),
  })
  function resetFilters() {
    const next = new URLSearchParams()
    for (const key of ['q', 'location']) {
      const value = search.get(key)
      if (value) next.set(key, value)
    }
    setFilterError('')
    setSearch(next)
  }
  return (
    <StudentPage title="Tìm cơ hội. Bắt đầu hành trình." description="Khám phá việc làm và cơ hội thực tập đã được nhà trường kiểm duyệt.">
      <div key={search.toString()} className="job-discovery">
        <form id={formId} className="job-search-bar" onSubmit={(event) => {
          event.preventDefault()
          const data = new FormData(event.currentTarget)
          const min = String(data.get('salary_from') || '')
          const max = String(data.get('salary_to') || '')
          if (min && max && Number(min) > Number(max)) {
            setFilterError('Mức lương từ phải nhỏ hơn hoặc bằng mức lương đến.')
            setFiltersOpen(true)
            return
          }
          const params = new URLSearchParams()
          data.forEach((value, key) => {
            const trimmed = String(value).trim()
            if (trimmed) params.append(key, trimmed)
          })
          setFilterError('')
          setSearch(params)
          setFiltersOpen(false)
        }}>
          <label className="job-search-field">
            <Search size={20} aria-hidden="true" />
            <span className="sr-only">Từ khóa</span>
            <input name="q" defaultValue={search.get('q') || ''} placeholder="Tên công việc, kỹ năng hoặc công nghệ…" />
          </label>
          <label className="job-search-field job-search-field--location">
            <MapPin size={19} aria-hidden="true" />
            <span className="sr-only">Địa điểm</span>
            <input name="location" defaultValue={search.get('location') || ''} placeholder="Tỉnh, thành phố…" />
          </label>
          <Button type="submit"><Search size={16} />Tìm việc</Button>
        </form>

        <div className="job-discovery-toolbar">
          <div>
            <h2>{query.data ? <><strong>{query.data.total.toLocaleString('vi-VN')}</strong> cơ hội việc làm</> : 'Khám phá cơ hội việc làm'}</h2>
            <p>{activeCount ? `Đang áp dụng ${activeCount} điều kiện lọc` : 'Tìm công việc phù hợp và kết nối với nhà tuyển dụng.'}</p>
          </div>
          <Button className="job-mobile-filter-toggle" variant="secondary" aria-expanded={filtersOpen} aria-controls="job-filter-panel" onClick={() => setFiltersOpen(!filtersOpen)}>
            <SlidersHorizontal size={16} />Bộ lọc{activeCount > 0 && <span className="job-filter-count">{activeCount}</span>}
          </Button>
        </div>

        <div className="job-discovery-layout">
          <aside id="job-filter-panel" className={'job-filter-panel' + (filtersOpen ? ' is-open' : '')} aria-label="Lọc việc làm">
            <div className="job-filter-heading">
              <h2><SlidersHorizontal size={17} />Bộ lọc tìm kiếm</h2>
              <button type="button" className="job-filter-close" aria-label="Đóng bộ lọc" onClick={() => setFiltersOpen(false)}><X size={18} /></button>
            </div>
            <div className="job-filter-fields">
              <label>Vị trí chuyên môn<input form={formId} name="position" defaultValue={search.get('position') || ''} placeholder="Ví dụ: Backend Developer" /></label>
              <label>Hình thức làm việc<select form={formId} name="work_mode" defaultValue={search.get('work_mode') || ''}>
                <option value="">Mọi hình thức</option><option value="ONSITE">Trực tiếp</option><option value="REMOTE">Từ xa</option><option value="HYBRID">Kết hợp</option>
              </select></label>
              <CatalogFilter name="job_type_id" catalog="job-types" label="Loại hình công việc" value={search.get('job_type_id') || ''} />
              <CatalogFilter name="industry_id" catalog="industries" label="Lĩnh vực" value={search.get('industry_id') || ''} />
              <details className="job-filter-advanced" open={Boolean(search.get('major_id'))}>
                <summary>Điều kiện bổ sung</summary>
                <div>
                  <CatalogFilter name="major_id" catalog="majors" label="Ngành học" value={search.get('major_id') || ''} />
                </div>
              </details>
              <fieldset className="job-salary-filter">
                <legend>Mức lương (VND)</legend>
                <div>
                  <label><span>Từ</span><input form={formId} name="salary_from" type="number" min="0" defaultValue={search.get('salary_from') || ''} placeholder="Không giới hạn" /></label>
                  <label><span>Đến</span><input form={formId} name="salary_to" type="number" min="0" defaultValue={search.get('salary_to') || ''} placeholder="Không giới hạn" /></label>
                </div>
              </fieldset>
              <details className="job-filter-advanced" open={Boolean(search.getAll('skill_ids').length)}>
                <summary>Kỹ năng{search.getAll('skill_ids').length > 0 && ` (${search.getAll('skill_ids').length})`}</summary>
                <SkillFilter values={search.getAll('skill_ids')} />
              </details>
              {filterError && <p className="student-form-error" role="alert">{filterError}</p>}
            </div>
            <div className="job-filter-footer">
              <Button form={formId} type="submit">Áp dụng bộ lọc</Button>
              <Button variant="ghost" onClick={resetFilters}>Xóa bộ lọc</Button>
            </div>
          </aside>

          <section className="job-discovery-results" aria-label="Kết quả tìm việc" aria-busy={query.isFetching}>
            <QueryState query={query} />
            {query.data && <>
              {query.data.items.length ? <div className="student-grid">{query.data.items.map(job => <JobCard key={job.id} job={job} />)}</div> :
                <EmptyState title="Chưa tìm thấy cơ hội phù hợp" description="Thử thay đổi từ khóa hoặc giảm bớt bộ lọc." action={<Button variant="secondary" onClick={() => { setSearch({}); setFilterError('') }}>Xóa tất cả điều kiện</Button>} />}
              <Pagination {...query.data} onChange={value => { const next = new URLSearchParams(search); next.set('page', String(value)); setSearch(next) }} />
            </>}
          </section>
        </div>
      </div>
    </StudentPage>
  )
}

function CatalogFilter({ name, catalog, label, value }: { name: string; catalog: string; label: string; value: string }) {
  const query = useQuery({
    queryKey: ['student-catalog', catalog, ''],
    queryFn: () => jobsApi.catalog(catalog),
  })
  return <label>{label}
    <select form={formId} name={name} defaultValue={value} disabled={query.isPending}>
      <option value="">{query.isPending ? 'Đang tải…' : 'Tất cả'}</option>
      {query.data?.items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select>
    {query.error && <span role="alert">{query.error.message}</span>}
  </label>
}

function SkillFilter({ values }: { values: string[] }) {
  const [keyword, setKeyword] = useState('')
  const query = useQuery({ queryKey: ['student-catalog', 'skills', ''], queryFn: () => jobsApi.catalog('skills') })
  return <div className="job-skill-filter">
    <label>Tìm kỹ năng<input value={keyword} onChange={event => setKeyword(event.target.value)} placeholder="Lọc kỹ năng theo tên…" /></label>
    <div className="job-skill-options">
      {query.data?.items.map(item => <label key={item.id} className="job-skill-option" hidden={!item.name.toLocaleLowerCase('vi').includes(keyword.toLocaleLowerCase('vi'))}>
        <input form={formId} type="checkbox" name="skill_ids" value={item.id} defaultChecked={values.includes(String(item.id))} />{item.name}
      </label>)}
    </div>
    {query.error && <p role="alert">{query.error.message}</p>}
  </div>
}
