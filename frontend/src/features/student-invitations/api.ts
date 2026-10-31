import { http } from '@/lib/http'
import type { Page } from '@/types/api'
export interface Invitation { id:number; job_id:number; company_id:number; message:string|null;status:string;created_at:string }
export const invitationsApi={
 list:async(page:number,signal?:AbortSignal)=>(await http.get<Page<Invitation>>('/invitations/me',{params:{page,size:12},signal})).data,
 decline:async(id:number)=>{await http.post('/invitations/'+id+'/decline')},
}

