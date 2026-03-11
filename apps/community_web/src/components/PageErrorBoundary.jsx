import React, { Component } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import { styled, alpha, keyframes } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

// Subtle fade animation
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const Container = styled(Paper)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(6, 4),
  margin: theme.spacing(4, 'auto'),
  maxWidth: 500,
  textAlign: 'center',
  borderRadius: 12,
  background: theme.palette.mode === 'dark'
    ? alpha(theme.palette.background.paper, 0.8)
    : theme.palette.background.paper,
  border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
  animation: `${fadeIn} 0.4s ease-out`,
}));

const IconWrapper = styled(Box)(({ theme }) => ({
  width: 64,
  height: 64,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: theme.spacing(2),
  borderRadius: '50%',
  background: alpha(theme.palette.warning.main, 0.1),
  color: theme.palette.warning.main,
}));

function WarningIcon() {
  return <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
}

// Standalone function - doesn't need class context
const handleGoBack = () => {
  window.history.back();
};

/**
 * Lightweight error boundary for individual pages.
 * Shows error within the page content area without affecting the overall layout.
 */
class PageErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.error('Page Error:', error);
      // eslint-disable-next-line no-console
      console.error('Component Stack:', errorInfo?.componentStack);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    const { hasError, error } = this.state;
    const { children } = this.props;

    if (hasError) {
      return (
        <Container elevation={0}>
          <IconWrapper>
            <WarningIcon />
          </IconWrapper>

          <Typography variant="h6" fontWeight={600} gutterBottom>
            Page failed to load
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 3, maxWidth: 320 }}
          >
            This page encountered an error. Try refreshing or go back to the previous page.
          </Typography>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={this.handleRetry}
              disableElevation
            >
              Retry
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<ArrowBackIcon />}
              onClick={handleGoBack}
            >
              Go Back
            </Button>
          </Box>

          {process.env.NODE_ENV === 'development' && error && (
            <Typography
              variant="caption"
              component="pre"
              sx={{
                mt: 3,
                p: 2,
                width: '100%',
                borderRadius: 1,
                bgcolor: 'action.hover',
                color: 'error.main',
                overflow: 'auto',
                textAlign: 'left',
                fontFamily: 'monospace',
                fontSize: '0.7rem',
              }}
            >
              {error.message}
            </Typography>
          )}
        </Container>
      );
    }

    return children;
  }
}

export default PageErrorBoundary;
