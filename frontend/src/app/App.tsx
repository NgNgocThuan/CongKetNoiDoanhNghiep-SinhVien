import { App as AntApp, ConfigProvider } from 'antd'
import viVN from 'antd/locale/vi_VN'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import dayjs from 'dayjs'
import 'dayjs/locale/vi'
import { AuthProvider } from '@/features/auth/AuthProvider'
import { theme } from '@/styles/theme'
import { router } from './router'

dayjs.locale('vi')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
})

export default function App() {
  return (
    <ConfigProvider theme={theme} locale={viVN}>
      <AntApp>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <RouterProvider router={router} />
          </AuthProvider>
        </QueryClientProvider>
      </AntApp>
    </ConfigProvider>
  )
}
