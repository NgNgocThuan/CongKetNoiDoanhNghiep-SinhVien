import { http } from '@/lib/http'
import type { Page } from '@/types/api'
export interface Assignment {id:number;term:{id:number;name:string;semester:string;academic_year:string;start_date:string;end_date:string;status:string};lecturer:{id:number;full_name:string;email:string|null;phone:string|null}|null}
export interface TermJob {id:number;title:string;position:string;company_id:number;status:string;deadline:string}
export const internshipsApi={
 list:async(signal?:AbortSignal)=>(await http.get<Assignment[]>('/students/me/internship',{signal})).data,
 jobs:async(termId:number,page:number,signal?:AbortSignal)=>(await http.get<Page<TermJob>>('/internship-terms/'+termId+'/jobs',{params:{page,size:12},signal})).data,
}

