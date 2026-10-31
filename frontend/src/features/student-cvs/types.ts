export interface CV {
  id: number
  title: string
  type: 'ONLINE' | 'UPLOADED'
  is_default: boolean
  file_url: string | null
  content_json: Record<string, unknown> | null
  parsed_json: Record<string, unknown> | null
  parsed_at: string | null
  created_at: string
  updated_at: string
}
