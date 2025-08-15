import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error);
    console.error('Error info:', errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#121212' }}>
          <div className="border border-red-500 rounded-lg p-6 max-w-md" style={{ backgroundColor: '#121212' }}>
            <div className="text-red-400 text-4xl mb-4 text-center">⚠️</div>
            <h1 className="text-white text-xl font-bold mb-4 text-center">
              Something went wrong
            </h1>
            <p className="text-gray-300 text-sm mb-4 text-center">
              The application encountered an error. Please refresh the page to continue.
            </p>
            <div className="text-center">
              <button
                onClick={() => window.location.reload()}
                className="bg-orange-500 text-white px-6 py-2 rounded-lg hover:bg-orange-600 transition-all"
              >
                Refresh Page
              </button>
            </div>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 text-xs text-gray-400">
                <summary className="cursor-pointer">Error Details</summary>
                <pre className="mt-2 p-2 bg-gray-700 rounded overflow-auto">
                  {this.state.error.toString()}
                </pre>
                <pre className="mt-2 p-2 bg-gray-700 rounded overflow-auto">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

