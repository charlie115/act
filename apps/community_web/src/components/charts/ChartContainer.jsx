import React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Skeleton from '@mui/material/Skeleton';
import { styled, alpha, useTheme } from '@mui/material/styles';

// Modern chart container with enhanced styling
const StyledChartCard = styled(Card)(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  border: `1px solid ${theme.palette.divider}`,
  overflow: 'hidden',
  backgroundColor: theme.palette.background.paper,
  transition: theme.transitions.create(['box-shadow', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    boxShadow: theme.shadows[3],
    transform: 'translateY(-1px)',
  },
}));

// Chart header with title and controls
const ChartHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderBottom: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  backgroundColor: theme.palette.mode === 'dark' 
    ? theme.palette.background.paper 
    : alpha(theme.palette.grey[50], 0.5),
}));

// Chart body container
const ChartBody = styled(Box)(({ theme }) => ({
  position: 'relative',
  padding: theme.spacing(2),
  minHeight: 300,
  display: 'flex',
  flexDirection: 'column',
  '& canvas': {
    borderRadius: theme.spacing(1),
  },
}));

// Loading overlay
const LoadingOverlay = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: alpha(theme.palette.background.paper, 0.8),
  zIndex: 1,
  borderRadius: theme.shape.borderRadius,
}));

// Empty state
const EmptyState = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: 250,
  color: theme.palette.text.secondary,
  gap: theme.spacing(2),
}));

export default function ChartContainer({
  title,
  subtitle,
  actions,
  children,
  loading = false,
  error = null,
  empty = false,
  height = 300,
  showHeader = true,
  ...props
}) {

  return (
    <StyledChartCard elevation={0} {...props}>
      {showHeader && (title || subtitle || actions) && (
        <ChartHeader>
          <Box>
            {title && (
              <Typography variant="h6" component="h3" gutterBottom={!!subtitle}>
                {title}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          {actions && <Box>{actions}</Box>}
        </ChartHeader>
      )}
      
      <ChartBody sx={{ minHeight: height }}>
        {loading && (
          <LoadingOverlay>
            <Box sx={{ width: '100%', px: 4 }}>
              <LinearProgress />
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mt: 2, textAlign: 'center' }}
              >
                Loading chart data...
              </Typography>
            </Box>
          </LoadingOverlay>
        )}
        
        {!loading && empty && (
          <EmptyState>
            <Typography variant="body1">No data available</Typography>
            <Typography variant="body2" color="text.secondary">
              Check back later for updated information
            </Typography>
          </EmptyState>
        )}
        
        {!loading && error && (
          <EmptyState>
            <Typography variant="body1" color="error">
              Error loading chart
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {error.message || 'Please try again later'}
            </Typography>
          </EmptyState>
        )}
        
        {!loading && !empty && !error && children}
      </ChartBody>
    </StyledChartCard>
  );
}

// Chart skeleton loader
export function ChartSkeleton({ height = 300, showHeader = true }) {
  return (
    <StyledChartCard elevation={0}>
      {showHeader && (
        <ChartHeader>
          <Box>
            <Skeleton variant="text" width={150} height={32} />
            <Skeleton variant="text" width={200} height={20} />
          </Box>
        </ChartHeader>
      )}
      <ChartBody sx={{ minHeight: height }}>
        <Skeleton 
          variant="rectangular" 
          width="100%" 
          height={height - 32} 
          sx={{ borderRadius: 1 }}
        />
      </ChartBody>
    </StyledChartCard>
  );
}

// Mini chart container for dashboards
export function MiniChartContainer({ title, value, chart, trend, ...props }) {
  const theme = useTheme();
  const isPositive = trend > 0;
  
  return (
    <StyledChartCard elevation={0} {...props}>
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 2 }}>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
          {trend !== undefined && (
            <Typography
              variant="body2"
              sx={{
                color: isPositive ? theme.palette.success.main : theme.palette.error.main,
                fontWeight: 'medium',
              }}
            >
              {isPositive ? '+' : ''}{trend}%
            </Typography>
          )}
        </Box>
        <Box sx={{ height: 80, mx: -1 }}>
          {chart}
        </Box>
      </Box>
    </StyledChartCard>
  );
}