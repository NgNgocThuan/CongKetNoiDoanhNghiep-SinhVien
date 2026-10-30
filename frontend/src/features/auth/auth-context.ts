import { createContext } from 'react'
import type { LoginInput, User } from './types/auth.types'

export interface AuthContextValue {
  user: User | null
  status: 'loading' | 'authenticated' | 'anonymous' | 'error'
  error: Error | null
  login: (input: LoginInput) => Promise<User>
  logout: () => Promise<void>
  retry: () => Promise<void>
}
export const AuthContext = createContext<AuthContextValue | null>(null)
