import { z } from 'zod'
import type { Field } from './Workspace'

export function formSchema(fields: Field[]) {
  return z.record(z.string(), z.unknown()).superRefine((values, context) => {
    for (const field of fields) {
      const value = values[field.name]
      const text =
        typeof value === 'string'
          ? value.trim()
          : value == null
            ? ''
            : String(value)
      let message = ''
      if (field.required && field.type !== 'checkbox' && !text)
        message = 'Vui lòng nhập ' + field.label.toLowerCase() + '.'
      else if (text && field.maxLength && text.length > field.maxLength)
        message = 'Tối đa ' + field.maxLength + ' ký tự.'
      else if (text && field.minLength && text.length < field.minLength)
        message = 'Cần ít nhất ' + field.minLength + ' ký tự.'
      else if (
        text &&
        field.type === 'number' &&
        (!Number.isFinite(Number(text)) ||
          (field.min !== undefined && Number(text) < field.min) ||
          (field.max !== undefined && Number(text) > field.max))
      )
        message = 'Giá trị nằm ngoài khoảng cho phép.'
      if (message)
        context.addIssue({ code: 'custom', path: [field.name], message })
    }
  })
}
