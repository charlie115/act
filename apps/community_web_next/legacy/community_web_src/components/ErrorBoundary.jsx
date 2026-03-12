import React, { Component } from 'react';
import ErrorFallback from './ErrorFallback';

/**
 * Error Boundary component that catches JavaScript errors anywhere in the child
 * component tree, logs those errors, and displays a fallback UI.
 *
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 *
 * Or with custom fallback:
 * <ErrorBoundary fallback={(error, resetErrorBoundary) => <CustomError />}>
 *   <YourComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    const { onError } = this.props;

    // Log the error to console in development
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.group('🚨 Error Boundary Caught an Error');
      // eslint-disable-next-line no-console
      console.error('Error:', error);
      // eslint-disable-next-line no-console
      console.error('Component Stack:', errorInfo?.componentStack);
      // eslint-disable-next-line no-console
      console.groupEnd();
    }

    // Call optional error handler prop
    if (onError) {
      onError(error, errorInfo);
    }
  }

  resetErrorBoundary = () => {
    const { onReset } = this.props;

    // Reset the error boundary state
    this.setState({
      hasError: false,
      error: null,
    });

    // Call optional reset handler
    if (onReset) {
      onReset();
    }
  };

  render() {
    const { hasError, error } = this.state;
    const { children, fallback, FallbackComponent, title, description } = this.props;

    if (hasError) {
      // Custom render function fallback
      if (typeof fallback === 'function') {
        return fallback(error, this.resetErrorBoundary);
      }

      // Custom fallback component
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={error}
            resetErrorBoundary={this.resetErrorBoundary}
            title={title}
            description={description}
          />
        );
      }

      // Default fallback UI
      return (
        <ErrorFallback
          error={error}
          resetErrorBoundary={this.resetErrorBoundary}
          title={title}
          description={description}
        />
      );
    }

    return children;
  }
}

export default ErrorBoundary;
