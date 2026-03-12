import React from 'react';
import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import { styled, alpha, keyframes , useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

// Shimmer animation overlay
const shimmer = keyframes`
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
`;

// Cell type configurations
const CELL_TYPES = {
  icon: { width: 32, height: 32, variant: 'circular' },
  iconSmall: { width: 24, height: 24, variant: 'circular' },
  text: { width: '80%', height: 16, variant: 'text' },
  textShort: { width: '50%', height: 16, variant: 'text' },
  textLong: { width: '90%', height: 16, variant: 'text' },
  number: { width: 60, height: 16, variant: 'text' },
  numberLarge: { width: 80, height: 18, variant: 'text' },
  small: { width: 40, height: 14, variant: 'text' },
  medium: { width: 70, height: 16, variant: 'text' },
  large: { width: 100, height: 18, variant: 'text' },
  badge: { width: 48, height: 22, variant: 'rounded' },
  chart: { width: 60, height: 24, variant: 'rectangular' },
};

// Default column configuration for crypto tables
const DEFAULT_COLUMNS = [
  { type: 'icon', align: 'center' },
  { type: 'text', align: 'left' },
  { type: 'numberLarge', align: 'right' },
  { type: 'number', align: 'right' },
  { type: 'number', align: 'right' },
  { type: 'small', align: 'right' },
];

// Styled Components
const SkeletonContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  overflow: 'hidden',
  borderRadius: 6,
  border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
  backgroundColor: theme.palette.background.paper,
}));

const SkeletonTable = styled('table')({
  width: '100%',
  borderCollapse: 'collapse',
  tableLayout: 'fixed',
});

const SkeletonHeaderRow = styled('tr')(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark'
    ? alpha(theme.palette.background.paper, 0.8)
    : theme.palette.grey[50],
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
}));

const SkeletonHeaderCell = styled('th')(({ theme }) => ({
  padding: theme.spacing(1.5),
  textAlign: 'center',
  [theme.breakpoints.down('md')]: {
    padding: theme.spacing(1, 0.5),
  },
}));

const SkeletonRow = styled('tr')(({ theme, $isEven }) => ({
  backgroundColor: $isEven
    ? alpha(theme.palette.action.hover, 0.02)
    : 'transparent',
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
  transition: 'background-color 0.15s ease',
  '&:last-child': {
    borderBottom: 'none',
  },
}));

const SkeletonCell = styled('td')(({ theme, $align }) => ({
  padding: theme.spacing(1.25, 1.5),
  textAlign: $align || 'center',
  verticalAlign: 'middle',
  [theme.breakpoints.down('md')]: {
    padding: theme.spacing(0.75, 0.5),
  },
}));

// Helper to determine justify-content based on alignment
const getJustifyContent = (align) => {
  if (align === 'left') return 'flex-start';
  if (align === 'right') return 'flex-end';
  return 'center';
};

const CellContent = styled(Box)(({ $align }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: getJustifyContent($align),
  gap: 8,
}));

const StyledSkeleton = styled(Skeleton)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark'
    ? alpha(theme.palette.primary.main, 0.08)
    : alpha(theme.palette.primary.main, 0.06),
  '&::after': {
    background: `linear-gradient(
      90deg,
      transparent,
      ${alpha(theme.palette.primary.main, 0.08)},
      transparent
    )`,
    animation: `${shimmer} 1.5s ease-in-out infinite`,
  },
}));

const HeaderSkeleton = styled(Skeleton)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark'
    ? alpha(theme.palette.text.primary, 0.1)
    : alpha(theme.palette.text.primary, 0.08),
  '&::after': {
    background: `linear-gradient(
      90deg,
      transparent,
      ${alpha(theme.palette.text.primary, 0.05)},
      transparent
    )`,
  },
}));

// Asset cell with icon and text
function AssetCellSkeleton({ isMobile }) {
  return <CellContent $align="left">
    <StyledSkeleton
      variant="circular"
      width={isMobile ? 24 : 32}
      height={isMobile ? 24 : 32}
      animation="wave"
    />
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <StyledSkeleton
        variant="text"
        width={isMobile ? 50 : 70}
        height={isMobile ? 14 : 16}
        animation="wave"
      />
      <StyledSkeleton
        variant="text"
        width={isMobile ? 35 : 45}
        height={isMobile ? 10 : 12}
        animation="wave"
        sx={{ opacity: 0.6 }}
      />
    </Box>
  </CellContent>
}

// Price cell with main price and change
function PriceCellSkeleton({ isMobile }) {
  return <CellContent $align="right">
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.25 }}>
      <StyledSkeleton
        variant="text"
        width={isMobile ? 55 : 75}
        height={isMobile ? 14 : 16}
        animation="wave"
      />
      <StyledSkeleton
        variant="text"
        width={isMobile ? 35 : 45}
        height={isMobile ? 10 : 12}
        animation="wave"
        sx={{ opacity: 0.6 }}
      />
    </Box>
  </CellContent>
}

/**
 * TableSkeleton - Loading skeleton for data tables
 *
 * @param {number} rows - Number of skeleton rows to display (default: 10)
 * @param {Array} columns - Column configuration array with { type, align } objects
 * @param {boolean} showHeader - Whether to show header skeleton (default: true)
 * @param {string} variant - Preset variant: 'premium', 'simple', 'compact'
 */
function TableSkeleton({
  rows = 10,
  columns = DEFAULT_COLUMNS,
  showHeader = true,
  variant = 'default',
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Adjust rows for mobile
  const displayRows = isMobile ? Math.min(rows, 8) : rows;

  // Get column config based on variant
  const getColumns = () => {
    if (variant === 'premium') {
      return [
        { type: 'asset', align: 'left' },
        { type: 'price', align: 'right' },
        { type: 'number', align: 'right' },
        { type: 'number', align: 'right' },
        { type: 'small', align: 'right' },
        { type: 'badge', align: 'center' },
      ];
    }
    if (variant === 'compact') {
      return [
        { type: 'iconSmall', align: 'center' },
        { type: 'textShort', align: 'left' },
        { type: 'number', align: 'right' },
        { type: 'small', align: 'right' },
      ];
    }
    if (variant === 'simple') {
      return [
        { type: 'text', align: 'left' },
        { type: 'number', align: 'right' },
        { type: 'number', align: 'right' },
      ];
    }
    return columns;
  };

  const columnConfig = getColumns();

  // Filter columns for mobile
  const visibleColumns = isMobile
    ? columnConfig.slice(0, Math.min(columnConfig.length, 4))
    : columnConfig;

  const renderCell = (col, rowIndex) => {
    const cellType = CELL_TYPES[col.type];

    // Special cell types
    if (col.type === 'asset') {
      return <AssetCellSkeleton isMobile={isMobile} />;
    }
    if (col.type === 'price') {
      return <PriceCellSkeleton isMobile={isMobile} />;
    }

    if (!cellType) {
      return (
        <StyledSkeleton
          variant="text"
          width={60}
          height={16}
          animation="wave"
        />
      );
    }

    // Scale down for mobile
    const width = isMobile && typeof cellType.width === 'number'
      ? cellType.width * 0.75
      : cellType.width;
    const height = isMobile ? cellType.height * 0.85 : cellType.height;

    return (
      <CellContent $align={col.align}>
        <StyledSkeleton
          variant={cellType.variant}
          width={width}
          height={height}
          animation="wave"
          sx={{
            // Stagger animation delay for visual interest
            animationDelay: `${(rowIndex * 0.05)}s`,
          }}
        />
      </CellContent>
    );
  };

  /* eslint-disable react/no-array-index-key -- Skeleton placeholders don't have unique IDs */
  return (
    <SkeletonContainer>
      <SkeletonTable>
        {showHeader && (
          <thead>
            <SkeletonHeaderRow>
              {visibleColumns.map((col, index) => (
                <SkeletonHeaderCell key={`header-${index}`}>
                  <CellContent $align={col.align}>
                    <HeaderSkeleton
                      variant="text"
                      width={isMobile ? 40 : 60}
                      height={isMobile ? 12 : 14}
                      animation="wave"
                    />
                  </CellContent>
                </SkeletonHeaderCell>
              ))}
            </SkeletonHeaderRow>
          </thead>
        )}
        <tbody>
          {[...Array(displayRows)].map((_, rowIndex) => (
            <SkeletonRow key={`row-${rowIndex}`} $isEven={rowIndex % 2 === 0}>
              {visibleColumns.map((col, colIndex) => (
                <SkeletonCell key={`cell-${rowIndex}-${colIndex}`} $align={col.align}>
                  {renderCell(col, rowIndex)}
                </SkeletonCell>
              ))}
            </SkeletonRow>
          ))}
        </tbody>
      </SkeletonTable>
    </SkeletonContainer>
  );
  /* eslint-enable react/no-array-index-key */
}

export default TableSkeleton;
