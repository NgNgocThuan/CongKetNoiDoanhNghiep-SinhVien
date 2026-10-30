import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { ConfirmDialog } from './ConfirmDialog'

it('keeps a failed confirmation open and displays the error', async () => {
  const confirm = vi.fn(async () => { throw new Error('offline') })
  function Example() {
    const [open, setOpen] = useState(true)
    return <ConfirmDialog open={open} onOpenChange={setOpen} title="Ngừng hoạt động?" description="Bạn có thể mở lại sau." onConfirm={confirm} />
  }
  render(<Example />)
  await userEvent.click(screen.getByRole('button', { name: 'Xác nhận' }))
  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.getByRole('dialog')).toBeInTheDocument()
  expect(confirm).toHaveBeenCalledTimes(1)
})
