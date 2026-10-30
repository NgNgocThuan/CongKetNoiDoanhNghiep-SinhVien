import { Component } from 'react'
import type { ReactNode } from 'react'
import { ErrorState } from './States'

export class AppErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    return this.state.failed ? <main className="center-page"><ErrorState title="Trang đang gặp sự cố" message="Dữ liệu đã lưu vẫn được giữ nguyên. Vui lòng tải lại trang." onRetry={() => window.location.reload()} /></main> : this.props.children
  }
}
