import { vi, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SaveJobButton } from './components/SaveJobButton'
import { http } from '@/lib/http'
vi.mock('@/lib/http', () => ({http:{get:vi.fn(),post:vi.fn(),delete:vi.fn()}}))
it('recognizes saved jobs beyond the first page and unsaves rather than saves again',async()=>{
 vi.mocked(http.get).mockImplementation(async (_url, config) => ({data:(config?.params as {page:number})?.page===1 ? {pages:2,items:[{job:{id:1}}]} : {pages:2,items:[{job:{id:101}}]}}))
 vi.mocked(http.delete).mockResolvedValue({data:undefined})
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><SaveJobButton jobId={101}/></QueryClientProvider>)
 const button=await screen.findByRole('button',{name:'Bỏ lưu việc làm'})
 await userEvent.click(button)
 await waitFor(()=>expect(http.delete).toHaveBeenCalledWith('/saved-jobs/101'))
 expect(http.post).not.toHaveBeenCalled()
})
