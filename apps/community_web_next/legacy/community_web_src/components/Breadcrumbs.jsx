import React, { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import MuiBreadcrumbs from '@mui/material/Breadcrumbs';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { styled, alpha } from '@mui/material/styles';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HomeIcon from '@mui/icons-material/Home';
import { useTranslation } from 'react-i18next';

import { routes } from 'configs/navigation';

// Styled Components
const BreadcrumbsContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(1.5, 0),
  marginBottom: theme.spacing(2),
}));

const StyledBreadcrumbs = styled(MuiBreadcrumbs)(({ theme }) => ({
  '& .MuiBreadcrumbs-separator': {
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    color: theme.palette.text.disabled,
  },
  '& .MuiBreadcrumbs-ol': {
    flexWrap: 'nowrap',
  },
}));

const BreadcrumbLink = styled(Link)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.75),
  color: theme.palette.text.secondary,
  textDecoration: 'none',
  fontSize: '0.8125rem',
  fontWeight: 500,
  padding: theme.spacing(0.5, 1),
  borderRadius: 6,
  transition: 'all 0.2s ease',
  whiteSpace: 'nowrap',
  '&:hover': {
    color: theme.palette.primary.main,
    backgroundColor: alpha(theme.palette.primary.main, 0.08),
  },
}));

const CurrentPage = styled(Typography)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.75),
  color: theme.palette.text.primary,
  fontSize: '0.8125rem',
  fontWeight: 600,
  padding: theme.spacing(0.5, 1),
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: 200,
}));

const HomeIconStyled = styled(HomeIcon)(() => ({
  fontSize: 16,
  color: 'inherit',
}));

const Separator = styled(NavigateNextIcon)(({ theme }) => ({
  fontSize: 16,
  color: theme.palette.text.disabled,
}));

// Route name mappings for child routes
const ROUTE_LABELS = {
  // Bot routes
  triggers: 'Triggers',
  scanner: 'Scanner',
  position: 'Position',
  capital: 'Capital',
  'pnl-history': 'P&L History',
  settings: 'Settings',
  'api-key': 'API Key',
  deposit: 'Deposit',
  // Arbitrage routes
  'funding-rate': 'Funding Rate',
  diff: 'Difference',
  avg: 'Average',
  // Community routes
  post: 'Post',
  new: 'New Post',
  // Affiliate routes
  dashboard: 'Dashboard',
  'commission-history': 'Commission History',
};

/**
 * Find route in route list by path
 */
const findRouteByPath = (routeList, path) => {
  // eslint-disable-next-line no-restricted-syntax
  for (const route of routeList) {
    if (route.path === path) return route;
    if (route.children) {
      const childRoute = findRouteByPath(route.children, path);
      if (childRoute) return childRoute;
    }
    // Check for dynamic routes
    if (route.path && route.path.includes(':')) {
      const routePattern = route.path.replace(/:[^/]+/g, '[^/]+');
      const regex = new RegExp(`^${routePattern}$`);
      if (regex.test(path)) return route;
    }
  }
  return null;
};

/**
 * Get breadcrumb items from current path
 */
const useBreadcrumbs = (dynamicTitle) => {
  const location = useLocation();
  const { t } = useTranslation();

  return useMemo(() => {
    const pathSegments = location.pathname.split('/').filter(Boolean);

    // Always start with Home
    const breadcrumbs = [
      {
        label: t('Home'),
        path: '/',
        icon: HomeIconStyled,
      },
    ];

    // Build breadcrumbs from path segments using reduce
    pathSegments.reduce((acc, segment) => {
      const newPath = `${acc}/${segment}`;

      // Skip dynamic params like :postId
      if (segment.startsWith(':')) {
        return newPath;
      }

      // Check if this is a dynamic param value (like a post ID)
      const isParamValue = /^\d+$/.test(segment);

      const route = findRouteByPath(routes, newPath);

      let label;
      if (route && route.getTitle) {
        label = route.getTitle();
      } else if (isParamValue && dynamicTitle) {
        // Use dynamic title for param values (e.g., post title)
        label = dynamicTitle;
      } else if (ROUTE_LABELS[segment]) {
        label = t(ROUTE_LABELS[segment]);
      } else {
        // Capitalize and format segment
        label = segment
          .split('-')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      }

      // Don't add duplicate entries
      const exists = breadcrumbs.some((b) => b.path === newPath);
      if (!exists) {
        breadcrumbs.push({
          label,
          path: newPath,
        });
      }

      return newPath;
    }, '');

    return breadcrumbs;
  }, [location.pathname, dynamicTitle, t]);
};

/**
 * Breadcrumbs - Navigation breadcrumb component
 *
 * @param {string} dynamicTitle - Dynamic title for pages with params (e.g., post title)
 * @param {number} maxItems - Maximum items to show before collapsing
 */
function Breadcrumbs({ dynamicTitle, maxItems = 4 }) {
  const breadcrumbs = useBreadcrumbs(dynamicTitle);

  // Don't show breadcrumbs on home page or if only home
  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <BreadcrumbsContainer>
      <StyledBreadcrumbs
        separator={<Separator />}
        maxItems={maxItems}
        itemsBeforeCollapse={1}
        itemsAfterCollapse={2}
      >
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          const IconComponent = crumb.icon;

          if (isLast) {
            return (
              <CurrentPage key={crumb.path} component="span">
                {IconComponent && <IconComponent />}
                {crumb.label}
              </CurrentPage>
            );
          }

          return (
            <BreadcrumbLink key={crumb.path} to={crumb.path}>
              {IconComponent && <IconComponent />}
              {crumb.label}
            </BreadcrumbLink>
          );
        })}
      </StyledBreadcrumbs>
    </BreadcrumbsContainer>
  );
}

export default Breadcrumbs;
