import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="min-h-[300px] flex items-center justify-center">
          <div className="text-center p-8 bg-red-50 rounded-lg max-w-md">
            <h2 className="text-lg font-semibold text-red-800 mb-2">
              오류가 발생했습니다
            </h2>
            <p className="text-red-600 text-sm mb-4">
              {this.state.error?.message || '알 수 없는 오류'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
            >
              다시 시도
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
