import { http } from '@/lib/http'
import type { Page } from '@/lib/types'
import type { CatalogItemMap, CatalogListParams, CatalogResource, Skill, SkillAlias } from './types'

const BASE = '/catalog'

/** Bỏ tham số rỗng để URL gọn và không gửi q="" lên backend. */
function clean<T extends object>(params: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  ) as Partial<T>
}

export async function listCatalog<R extends CatalogResource>(
  resource: R,
  params: CatalogListParams = {},
): Promise<Page<CatalogItemMap[R]>> {
  const { data } = await http.get<Page<CatalogItemMap[R]>>(`${BASE}/${resource}`, { params: clean(params) })
  return data
}

export async function createCatalogItem<R extends CatalogResource>(
  resource: R,
  body: Record<string, unknown>,
): Promise<CatalogItemMap[R]> {
  const { data } = await http.post<CatalogItemMap[R]>(`${BASE}/${resource}`, body)
  return data
}

export async function updateCatalogItem<R extends CatalogResource>(
  resource: R,
  id: number,
  body: Record<string, unknown>,
): Promise<CatalogItemMap[R]> {
  const { data } = await http.put<CatalogItemMap[R]>(`${BASE}/${resource}/${id}`, body)
  return data
}

/** Xóa mềm: backend đặt is_active=false. */
export async function deactivateCatalogItem(resource: CatalogResource, id: number): Promise<void> {
  await http.delete(`${BASE}/${resource}/${id}`)
}

// ---- Kỹ năng
export async function searchSkills(q: string, limit = 10): Promise<Skill[]> {
  const { data } = await http.get<Skill[]>(`${BASE}/skills/search`, { params: { q, limit } })
  return data
}

export async function listSkillAliases(skillId: number): Promise<SkillAlias[]> {
  const { data } = await http.get<SkillAlias[]>(`${BASE}/skills/${skillId}/aliases`)
  return data
}

export async function addSkillAlias(skillId: number, alias: string): Promise<SkillAlias> {
  const { data } = await http.post<SkillAlias>(`${BASE}/skills/${skillId}/aliases`, { alias })
  return data
}

export async function deleteSkillAlias(skillId: number, aliasId: number): Promise<void> {
  await http.delete(`${BASE}/skills/${skillId}/aliases/${aliasId}`)
}
