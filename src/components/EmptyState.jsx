import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { styled, alpha, keyframes } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';

// Animations
const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const float = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.7; }
`;

const dash = keyframes`
  to { stroke-dashoffset: 0; }
`;

// Styled Components
const Container = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(6, 3),
  textAlign: 'center',
  animation: `${fadeInUp} 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
}));

const GlassCard = styled(Box)(({ theme, $compact }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: $compact ? theme.spacing(4, 3) : theme.spacing(5, 4),
  borderRadius: 16,
  background: theme.palette.mode === 'dark'
    ? `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.6)} 0%, ${alpha(theme.palette.background.paper, 0.4)} 100%)`
    : `linear-gradient(135deg, ${alpha('#ffffff', 0.8)} 0%, ${alpha('#ffffff', 0.6)} 100%)`,
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: `1px solid ${alpha(theme.palette.divider, 0.15)}`,
  boxShadow: theme.palette.mode === 'dark'
    ? `0 4px 24px ${alpha('#000', 0.2)}`
    : `0 4px 24px ${alpha('#000', 0.06)}`,
  maxWidth: 400,
  width: '100%',
}));

const IllustrationContainer = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  animation: `${float} 4s ease-in-out infinite`,
  '& svg': {
    width: 120,
    height: 120,
    [theme.breakpoints.down('sm')]: {
      width: 100,
      height: 100,
    },
  },
}));

const Title = styled(Typography)(({ theme }) => ({
  fontWeight: 600,
  marginBottom: theme.spacing(1),
  color: theme.palette.text.primary,
}));

const Description = styled(Typography)(({ theme }) => ({
  maxWidth: 320,
  marginBottom: theme.spacing(3),
  color: theme.palette.text.secondary,
  lineHeight: 1.6,
}));

const ActionButton = styled(Button)(({ theme }) => ({
  borderRadius: 10,
  padding: theme.spacing(1.25, 3),
  fontWeight: 600,
  textTransform: 'none',
  transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
  '&:hover': {
    transform: 'translateY(-2px)',
  },
}));

// SVG Illustrations
function NoDataIllustration({ color }) {
  return <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Background circle */}
    <circle cx="60" cy="60" r="50" fill={alpha(color, 0.06)} />
    <circle
      cx="60"
      cy="60"
      r="50"
      stroke={alpha(color, 0.15)}
      strokeWidth="1"
      strokeDasharray="4 4"
      style={{ animation: `${pulse} 2s ease-in-out infinite` }}
    />

    {/* Empty box */}
    <rect
      x="35"
      y="40"
      width="50"
      height="40"
      rx="4"
      stroke={color}
      strokeWidth="2"
      fill={alpha(color, 0.05)}
    />

    {/* Box flap */}
    <path
      d="M35 45L60 32L85 45"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />

    {/* Dashed lines representing missing data */}
    <line
      x1="45"
      y1="55"
      x2="75"
      y2="55"
      stroke={alpha(color, 0.3)}
      strokeWidth="2"
      strokeLinecap="round"
      strokeDasharray="6 4"
    />
    <line
      x1="45"
      y1="65"
      x2="65"
      y2="65"
      stroke={alpha(color, 0.2)}
      strokeWidth="2"
      strokeLinecap="round"
      strokeDasharray="6 4"
    />

    {/* Floating particles */}
    <circle cx="30" cy="35" r="2" fill={alpha(color, 0.3)} />
    <circle cx="90" cy="45" r="1.5" fill={alpha(color, 0.25)} />
    <circle cx="25" cy="70" r="1" fill={alpha(color, 0.2)} />
  </svg>
}

function NoResultsIllustration({ color }) {
  return <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Background */}
    <circle cx="60" cy="60" r="50" fill={alpha(color, 0.06)} />

    {/* Magnifying glass */}
    <circle
      cx="52"
      cy="52"
      r="22"
      stroke={color}
      strokeWidth="2.5"
      fill={alpha(color, 0.05)}
    />
    <line
      x1="68"
      y1="68"
      x2="85"
      y2="85"
      stroke={color}
      strokeWidth="3"
      strokeLinecap="round"
    />

    {/* X mark inside lens */}
    <path
      d="M44 44L60 60M60 44L44 60"
      stroke={alpha(color, 0.5)}
      strokeWidth="2"
      strokeLinecap="round"
    />

    {/* Search rays */}
    <path
      d="M35 30L30 25"
      stroke={alpha(color, 0.3)}
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <path
      d="M52 25L52 18"
      stroke={alpha(color, 0.3)}
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <path
      d="M69 30L74 25"
      stroke={alpha(color, 0.3)}
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
}

function ConnectionErrorIllustration({ color }) {
  return <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Background */}
    <circle cx="60" cy="60" r="50" fill={alpha(color, 0.06)} />

    {/* Signal waves with break */}
    <path
      d="M40 55C40 55 50 45 60 45C70 45 80 55 80 55"
      stroke={alpha(color, 0.3)}
      strokeWidth="2"
      strokeLinecap="round"
      fill="none"
    />
    <path
      d="M35 48C35 48 47 35 60 35C73 35 85 48 85 48"
      stroke={alpha(color, 0.2)}
      strokeWidth="2"
      strokeLinecap="round"
      fill="none"
    />

    {/* Disconnected plug */}
    <rect
      x="45"
      y="60"
      width="12"
      height="20"
      rx="2"
      stroke={color}
      strokeWidth="2"
      fill={alpha(color, 0.05)}
    />
    <rect
      x="63"
      y="60"
      width="12"
      height="20"
      rx="2"
      stroke={color}
      strokeWidth="2"
      fill={alpha(color, 0.05)}
    />

    {/* Plug prongs */}
    <line x1="48" y1="60" x2="48" y2="55" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="54" y1="60" x2="54" y2="55" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="66" y1="60" x2="66" y2="55" stroke={color} strokeWidth="2" strokeLinecap="round" />
    <line x1="72" y1="60" x2="72" y2="55" stroke={color} strokeWidth="2" strokeLinecap="round" />

    {/* Break indicator */}
    <path
      d="M57 68L63 72M57 72L63 68"
      stroke={alpha(color, 0.5)}
      strokeWidth="1.5"
      strokeLinecap="round"
    />

    {/* Spark effect */}
    <circle cx="60" cy="52" r="2" fill={color} opacity="0.6" />
    <path d="M55 48L52 44" stroke={color} strokeWidth="1" strokeLinecap="round" opacity="0.4" />
    <path d="M65 48L68 44" stroke={color} strokeWidth="1" strokeLinecap="round" opacity="0.4" />
  </svg>
}

function ChartEmptyIllustration({ color }) {
  return <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Background */}
    <circle cx="60" cy="60" r="50" fill={alpha(color, 0.06)} />

    {/* Chart grid */}
    <line x1="30" y1="85" x2="90" y2="85" stroke={alpha(color, 0.2)} strokeWidth="1" />
    <line x1="30" y1="70" x2="90" y2="70" stroke={alpha(color, 0.1)} strokeWidth="1" strokeDasharray="2 2" />
    <line x1="30" y1="55" x2="90" y2="55" stroke={alpha(color, 0.1)} strokeWidth="1" strokeDasharray="2 2" />
    <line x1="30" y1="40" x2="90" y2="40" stroke={alpha(color, 0.1)} strokeWidth="1" strokeDasharray="2 2" />

    {/* Flat line (no activity) */}
    <path
      d="M35 65H85"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeDasharray="180"
      strokeDashoffset="180"
      style={{
        animation: `${dash} 1s ease-out forwards`,
        animationDelay: '0.3s',
      }}
    />

    {/* Data points */}
    <circle cx="35" cy="65" r="3" fill={color} />
    <circle cx="85" cy="65" r="3" fill={color} />

    {/* Question mark */}
    <path
      d="M57 45C57 42 59 40 62 40C65 40 67 42 67 45C67 48 64 49 62 51"
      stroke={alpha(color, 0.4)}
      strokeWidth="2"
      strokeLinecap="round"
      fill="none"
    />
    <circle cx="62" cy="56" r="1.5" fill={alpha(color, 0.4)} />
  </svg>
}

// Illustration variants
const ILLUSTRATIONS = {
  'no-data': NoDataIllustration,
  'no-results': NoResultsIllustration,
  'connection-error': ConnectionErrorIllustration,
  'chart-empty': ChartEmptyIllustration,
};

// Default messages for each variant
const DEFAULT_CONTENT = {
  'no-data': {
    title: 'No data available',
    description: 'There is no data to display at the moment. Check back later or try refreshing.',
  },
  'no-results': {
    title: 'No results found',
    description: 'We couldn\'t find anything matching your search. Try different keywords.',
  },
  'connection-error': {
    title: 'Connection lost',
    description: 'Unable to connect to the server. Please check your connection and try again.',
  },
  'chart-empty': {
    title: 'No chart data',
    description: 'There isn\'t enough data to display this chart yet.',
  },
};

/**
 * EmptyState - Displays a visual empty state with illustration
 *
 * @param {string} variant - Illustration variant: 'no-data', 'no-results', 'connection-error', 'chart-empty'
 * @param {string} title - Custom title text (overrides default)
 * @param {string} description - Custom description text (overrides default)
 * @param {string} actionLabel - Button label text
 * @param {function} onAction - Button click handler
 * @param {ReactNode} actionIcon - Button icon
 * @param {boolean} compact - Use compact sizing
 * @param {string} color - Custom illustration color (defaults to primary)
 */
function EmptyState({
  variant = 'no-data',
  title,
  description,
  actionLabel,
  onAction,
  actionIcon,
  compact = false,
  color,
  children,
}) {
  const { t } = useTranslation();

  const IllustrationComponent = ILLUSTRATIONS[variant] || ILLUSTRATIONS['no-data'];
  const defaultContent = DEFAULT_CONTENT[variant] || DEFAULT_CONTENT['no-data'];

  const displayTitle = title || t(defaultContent.title);
  const displayDescription = description || t(defaultContent.description);

  return (
    <Container>
      <GlassCard $compact={compact}>
        <IllustrationContainer
          sx={{
            color: (theme) => color || theme.palette.primary.main,
          }}
        >
          <IllustrationComponent color={color || '#007cff'} />
        </IllustrationContainer>

        <Title variant={compact ? 'subtitle1' : 'h6'}>
          {displayTitle}
        </Title>

        <Description variant="body2">
          {displayDescription}
        </Description>

        {actionLabel && onAction && (
          <ActionButton
            variant="contained"
            color="primary"
            onClick={onAction}
            startIcon={actionIcon}
            disableElevation
          >
            {actionLabel}
          </ActionButton>
        )}

        {children}
      </GlassCard>
    </Container>
  );
}

// Also export a simpler inline version for tables
export function InlineEmptyState({
  message,
  icon,
}) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        px: 2,
        textAlign: 'center',
        animation: `${fadeInUp} 0.4s ease-out`,
      }}
    >
      {icon && (
        <Box
          sx={{
            mb: 2,
            color: 'text.disabled',
            opacity: 0.6,
          }}
        >
          {icon}
        </Box>
      )}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ fontStyle: 'italic' }}
      >
        {message || t('No data to display')}
      </Typography>
    </Box>
  );
}

export default EmptyState;
