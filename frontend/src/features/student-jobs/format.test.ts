import { it, expect } from 'vitest'
import { salaryText } from './format'
it('does not turn undisclosed salary into zero', () =>
  expect(
    salaryText({
      is_salary_negotiable: false,
      salary_min: null,
      salary_max: null,
    }),
  ).toBe('Chưa công bố'))
it('preserves negotiable salary', () =>
  expect(
    salaryText({
      is_salary_negotiable: true,
      salary_min: null,
      salary_max: null,
    }),
  ).toBe('Lương thỏa thuận'))
