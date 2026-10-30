/**
 * Hook đọc danh mục dùng chung (Việt Anh, Khôi, Thuận cũng dùng): mọi user đăng nhập đều đọc được.
 * Danh sách chọn lấy tối đa 100 dòng (giới hạn của API); danh mục khoa/ngành/lĩnh vực/loại hình nằm trong mức này.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  addSkillAlias,
  createCatalogItem,
  deactivateCatalogItem,
  deleteSkillAlias,
  listCatalog,
  listSkillAliases,
  searchSkills,
  updateCatalogItem,
} from './api'
import type { CatalogListParams, CatalogResource } from './types'

export const catalogKeys = {
  all: ['catalog'] as const,
  list: (resource: CatalogResource, params: CatalogListParams) => ['catalog', resource, 'list', params] as const,
  search: (q: string) => ['catalog', 'skills', 'search', q] as const,
  aliases: (skillId: number) => ['catalog', 'skills', skillId, 'aliases'] as const,
}

export function useCatalogList<R extends CatalogResource>(resource: R, params: CatalogListParams) {
  return useQuery({
    queryKey: catalogKeys.list(resource, params),
    queryFn: () => listCatalog(resource, params),
    placeholderData: (previous) => previous,
  })
}

const OPTIONS = { size: 100 }

export const useFaculties = () => useCatalogList('faculties', OPTIONS)
export const useMajors = (facultyId?: number) =>
  useQuery({
    queryKey: catalogKeys.list('majors', { ...OPTIONS, faculty_id: facultyId }),
    queryFn: () => listCatalog('majors', { ...OPTIONS, faculty_id: facultyId }),
  })
export const useIndustries = () => useCatalogList('industries', OPTIONS)
export const useJobTypes = () => useCatalogList('job-types', OPTIONS)

export function useSkillSearch(q: string) {
  return useQuery({
    queryKey: catalogKeys.search(q),
    queryFn: () => searchSkills(q, 20),
    enabled: q.trim().length > 0,
  })
}

export function useSkillAliases(skillId: number | null) {
  return useQuery({
    queryKey: catalogKeys.aliases(skillId ?? 0),
    queryFn: () => listSkillAliases(skillId as number),
    enabled: skillId !== null,
  })
}

// ---- Mutations (đều làm mới toàn bộ cache danh mục để selector ở nơi khác cập nhật theo)
export function useSaveCatalogItem(resource: CatalogResource) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id?: number; body: Record<string, unknown> }) =>
      id === undefined ? createCatalogItem(resource, body) : updateCatalogItem(resource, id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: catalogKeys.all }),
  })
}

export function useDeactivateCatalogItem(resource: CatalogResource) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deactivateCatalogItem(resource, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: catalogKeys.all }),
  })
}

export function useAddAlias(skillId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (alias: string) => addSkillAlias(skillId, alias),
    onSuccess: () => qc.invalidateQueries({ queryKey: catalogKeys.aliases(skillId) }),
  })
}

export function useDeleteAlias(skillId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (aliasId: number) => deleteSkillAlias(skillId, aliasId),
    onSuccess: () => qc.invalidateQueries({ queryKey: catalogKeys.aliases(skillId) }),
  })
}
