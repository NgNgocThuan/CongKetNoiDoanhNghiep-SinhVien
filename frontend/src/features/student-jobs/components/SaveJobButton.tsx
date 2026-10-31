import { SaveJobButton as SharedSaveJobButton } from '@/features/matching'
export function SaveJobButton({ jobId }: { jobId: number; saved?: boolean }) {
  return <SharedSaveJobButton jobId={jobId} />
}
