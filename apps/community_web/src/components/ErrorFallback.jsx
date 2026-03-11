import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import { styled, keyframes, alpha } from '@mui/material/styles';
import RefreshIcon from '@mui/icons-material/Refresh';
import HomeIcon from '@mui/icons-material/Home';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useTranslation } from 'react-i18next';

// Animations
const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
`;

const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
`;

const scanLine = keyframes`
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
`;

const glitch = keyframes`
  0%, 90%, 100% { transform: translate(0); }
  92% { transform: translate(-2px, 1px); }
  94% { transform: translate(2px, -1px); }
  96% { transform: translate(-1px, 2px); }
  98% { transform: translate(1px, -2px); }
`;

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

// Styled Components
const Container = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '60vh',
  padding: theme.spacing(4),
  position: 'relative',
  overflow: 'hidden',
}));

const BackgroundGrid = styled(Box)(({ theme }) => ({
  position: 'absolute',
  inset: 0,
  backgroundImage: `
    linear-gradient(${alpha(theme.palette.primary.main, 0.03)} 1px, transparent 1px),
    linear-gradient(90deg, ${alpha(theme.palette.primary.main, 0.03)} 1px, transparent 1px)
  `,
  backgroundSize: '40px 40px',
  maskImage: 'radial-gradient(ellipse at center, black 20%, transparent 70%)',
  WebkitMaskImage: 'radial-gradient(ellipse at center, black 20%, transparent 70%)',
}));

const GlassCard = styled(Box)(({ theme }) => ({
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: theme.spacing(5),
  borderRadius: 16,
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.6)} 100%)`
    : `linear-gradient(135deg, ${alpha('#ffffff', 0.9)} 0%, ${alpha('#ffffff', 0.7)} 100%)`,
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
  boxShadow: theme.palette.mode === 'dark'
    ? `0 8px 32px ${alpha('#000', 0.3)}, inset 0 1px 0 ${alpha('#fff', 0.05)}`
    : `0 8px 32px ${alpha('#000', 0.1)}, inset 0 1px 0 ${alpha('#fff', 0.5)}`,
  maxWidth: 480,
  width: '100%',
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '100%',
    background: `linear-gradient(180deg, transparent 0%, ${alpha(theme.palette.primary.main, 0.02)} 100%)`,
    pointerEvents: 'none',
  },
}));

const ScanLineOverlay = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  overflow: 'hidden',
  pointerEvents: 'none',
  opacity: 0.3,
  '&::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: `linear-gradient(180deg, transparent, ${alpha(theme.palette.primary.main, 0.15)}, transparent)`,
    animation: `${scanLine} 4s linear infinite`,
  },
}));

const IconContainer = styled(Box)(({ theme }) => ({
  position: 'relative',
  width: 120,
  height: 120,
  marginBottom: theme.spacing(3),
  animation: `${float} 4s ease-in-out infinite`,
}));

const ErrorIconWrapper = styled(Box)(({ theme }) => ({
  width: '100%',
  height: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '50%',
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.15)} 0%, ${alpha(theme.palette.error.dark, 0.1)} 100%)`
    : `linear-gradient(135deg, ${alpha(theme.palette.error.light, 0.2)} 0%, ${alpha(theme.palette.error.main, 0.1)} 100%)`,
  border: `2px solid ${alpha(theme.palette.error.main, 0.2)}`,
  animation: `${glitch} 8s ease-in-out infinite`,
  '&::before': {
    content: '""',
    position: 'absolute',
    inset: -4,
    borderRadius: '50%',
    border: `1px dashed ${alpha(theme.palette.error.main, 0.3)}`,
    animation: `${pulse} 2s ease-in-out infinite`,
  },
}));

const StatusIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginBottom: theme.spacing(2),
  padding: theme.spacing(0.5, 1.5),
  borderRadius: 20,
  background: alpha(theme.palette.error.main, 0.1),
  border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both`,
}));

const StatusDot = styled(Box)(({ theme }) => ({
  width: 8,
  height: 8,
  borderRadius: '50%',
  backgroundColor: theme.palette.error.main,
  animation: `${pulse} 1.5s ease-in-out infinite`,
}));

const Title = styled(Typography)(({ theme }) => ({
  fontWeight: 700,
  marginBottom: theme.spacing(1),
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(135deg, ${theme.palette.text.primary} 0%, ${alpha(theme.palette.text.primary, 0.7)} 100%)`
    : theme.palette.text.primary,
  WebkitBackgroundClip: 'text',
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.15s both`,
}));

const Description = styled(Typography)(({ theme }) => ({
  textAlign: 'center',
  maxWidth: 360,
  marginBottom: theme.spacing(4),
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both`,
}));

const ButtonGroup = styled(Box)(({ theme }) => ({
  display: 'flex',
  gap: theme.spacing(2),
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.25s both`,
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    width: '100%',
  },
}));

const StyledButton = styled(Button)(({ theme }) => ({
  borderRadius: 10,
  padding: theme.spacing(1.25, 3),
  fontWeight: 600,
  textTransform: 'none',
  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
  '&:hover': {
    transform: 'translateY(-2px)',
  },
  '&:active': {
    transform: 'translateY(0)',
  },
}));

const DetailsToggle = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginTop: theme.spacing(3),
  cursor: 'pointer',
  color: theme.palette.text.secondary,
  transition: 'color 0.2s ease',
  animation: `${fadeInUp} 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both`,
  '&:hover': {
    color: theme.palette.primary.main,
  },
}));

const ErrorDetails = styled(Box)(({ theme }) => ({
  width: '100%',
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  borderRadius: 8,
  background: theme.palette.mode === 'dark'
    ? alpha(theme.palette.background.default, 0.5)
    : alpha(theme.palette.grey[100], 0.8),
  border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
  fontFamily: '"JetBrains Mono", "Fira Code", "SF Mono", monospace',
  fontSize: '0.75rem',
  lineHeight: 1.6,
  color: theme.palette.error.main,
  overflow: 'auto',
  maxHeight: 200,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
}));

// Error Icon SVG Component
function ErrorIcon() {
  return <svg
    width="64"
    height="64"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M32 8L56 52H8L32 8Z"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />
    <path
      d="M32 24V36"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
    />
    <circle cx="32" cy="44" r="2" fill="currentColor" />
    {/* Trading chart line decoration */}
    <path
      d="M14 46L22 42L28 44L34 38L40 40L48 34"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      opacity="0.3"
    />
  </svg>
}

function ErrorFallback({
  error,
  resetErrorBoundary,
  title,
  description,
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showDetails, setShowDetails] = useState(false);

  const isDev = process.env.NODE_ENV === 'development';

  const handleRetry = () => {
    if (resetErrorBoundary) {
      resetErrorBoundary();
    } else {
      window.location.reload();
    }
  };

  const handleGoHome = () => {
    navigate('/');
  };

  const errorMessage = error?.message || error?.toString() || 'Unknown error';
  const errorStack = error?.stack || '';

  return (
    <Container>
      <BackgroundGrid />

      <GlassCard>
        <ScanLineOverlay />

        <IconContainer>
          <ErrorIconWrapper sx={{ color: 'error.main' }}>
            <ErrorIcon />
          </ErrorIconWrapper>
        </IconContainer>

        <StatusIndicator>
          <StatusDot />
          <Typography
            variant="caption"
            sx={{
              fontWeight: 600,
              color: 'error.main',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {t('Error Detected')}
          </Typography>
        </StatusIndicator>

        <Title variant="h5">
          {title || t('Something went wrong')}
        </Title>

        <Description variant="body2" color="text.secondary">
          {description || t('We encountered an unexpected error. Please try again or return to the home page.')}
        </Description>

        <ButtonGroup>
          <StyledButton
            variant="contained"
            color="primary"
            startIcon={<RefreshIcon />}
            onClick={handleRetry}
            disableElevation
          >
            {t('Try Again')}
          </StyledButton>

          <StyledButton
            variant="outlined"
            color="inherit"
            startIcon={<HomeIcon />}
            onClick={handleGoHome}
          >
            {t('Go Home')}
          </StyledButton>
        </ButtonGroup>

        {isDev && error && (
          <>
            <DetailsToggle onClick={() => setShowDetails(!showDetails)}>
              <Typography variant="caption" sx={{ mr: 0.5, fontWeight: 500 }}>
                {showDetails ? t('Hide Details') : t('Show Details')}
              </Typography>
              <IconButton size="small" sx={{ p: 0 }}>
                {showDetails ? (
                  <ExpandLessIcon fontSize="small" />
                ) : (
                  <ExpandMoreIcon fontSize="small" />
                )}
              </IconButton>
            </DetailsToggle>

            <Collapse in={showDetails} sx={{ width: '100%' }}>
              <ErrorDetails>
                <strong>Error:</strong> {errorMessage}
                {errorStack && (
                  <>
                    {'\n\n'}
                    <strong>Stack Trace:</strong>
                    {'\n'}
                    {errorStack}
                  </>
                )}
              </ErrorDetails>
            </Collapse>
          </>
        )}
      </GlassCard>
    </Container>
  );
}

export default ErrorFallback;
