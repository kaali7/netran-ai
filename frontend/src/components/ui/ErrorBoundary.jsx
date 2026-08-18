import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';
import Card from './Card';
import Button from './Button';

/**
 * Global Error Boundary to catch UI rendering crashes and display a fallback glassmorphic UI.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service if needed
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    // Hard reload the application
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div
          style={{
            minHeight: '100vh',
            width: '100vw',
            background: 'linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            fontFamily: 'var(--font-family, system-ui, sans-serif)',
          }}
        >
          <Card
            style={{
              padding: '40px',
              maxWidth: '520px',
              width: '100%',
              textAlign: 'center',
              background: '#ffffff',
              borderRadius: '24px',
              boxShadow: '0 20px 50px rgba(101, 89, 123, 0.08)',
              border: '1px solid rgba(229, 231, 235, 0.8)',
            }}
            className="animate-entrance"
          >
            <div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: '#fee2e2',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px auto',
              }}
            >
              <AlertTriangle size={40} style={{ color: '#dc2626' }} />
            </div>

            <h1
              style={{
                fontSize: '22px',
                fontWeight: '800',
                color: '#111827',
                marginBottom: '12px',
                letterSpacing: '-0.02em',
              }}
            >
              Something went wrong.
            </h1>

            <p
              style={{
                fontSize: '14px',
                color: '#6b7280',
                marginBottom: '28px',
                lineHeight: '1.6',
              }}
            >
              We encountered an unexpected error while rendering this page.
              Don't worry, your data is safe.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="primary"
                onClick={this.handleReload}
                icon={RotateCcw}
                style={{
                  background: '#65597b',
                  color: '#ffffff',
                }}
              >
                Reload Application
              </Button>
            </div>

            {/* Dev details - conditionally visible or kept minimal */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div
                style={{
                  marginTop: '24px',
                  padding: '16px',
                  background: '#f9fafb',
                  borderRadius: '12px',
                  border: '1px solid #e5e7eb',
                  textAlign: 'left',
                  overflowX: 'auto',
                }}
              >
                <p style={{ fontSize: '12px', color: '#dc2626', fontWeight: '700', margin: '0 0 8px 0' }}>
                  {this.state.error.toString()}
                </p>
                <pre style={{ fontSize: '10px', color: '#6b7280', margin: 0 }}>
                  {this.state.errorInfo?.componentStack}
                </pre>
              </div>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
