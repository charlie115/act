import React, { useMemo, useEffect } from 'react';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import {
  useGetDollarQuery,
  useGetUsdtQuery
} from 'redux/api/drf/infocore';
import { useGetCapitalQuery } from 'redux/api/drf/tradecore';
import { useTranslation } from 'react-i18next';

import ReactTableUI from 'components/ReactTableUI';
import renderColoredSignedNumberCell from 'components/tables/common/renderColoredSignedNumberCell';
import renderMarketCodeHeader from 'components/tables/position/renderMarketCodeHeader';
import renderPositionCell from 'components/tables/position/renderPositionCell';

export default function CapitalTable({ marketCodeCombination }) {
  const { i18n, t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const { target, origin, tradeConfigUuid } = marketCodeCombination;

  const { data: targetCapitalData, isFetching: isTargetLoading } = useGetCapitalQuery(
    { marketCode: target?.value, tradeConfigUuid },
    { skip: !target?.value || !tradeConfigUuid }
  );

  const { data: originCapitalData, isFetching: isOriginLoading } = useGetCapitalQuery(
    { marketCode: origin?.value, tradeConfigUuid },
    { skip: !origin?.value || !tradeConfigUuid }
  );

  // Fetch dollar and USDT prices
  const { data: dollarInfo } = useGetDollarQuery();
  const { data: usdtInfo } = useGetUsdtQuery();

  const gapColor = theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100';

  const metrics = [
    { key: 'currency', label: t('Currency')},
    { key: 'free', label: t('Free')},
    { key: 'locked', label: t('Locked')},
    { key: 'before_pnl', label: t('Before PnL')},
    { key: 'pnl', label: t('PnL'), isColored: true},
    { key: 'after_pnl', label: t('After PnL') },
    // Add the new metrics with a flag indicating total rows
    { key: 'total_before_pnl_by_dollar', label: t('Total before PnL (USD/KRW applied)'), isTotalRow: true },
    { key: 'total_after_pnl_by_dollar', label: t("Total after PnL (USD/KRW applied)"), isTotalRow: true },
    { key: 'total_before_pnl_by_usdt', label: t("Total before PnL (USDT/KRW applied)"), isTotalRow: true },
    { key: 'total_after_pnl_by_usdt', label: t("Total after PnL (USDT/KRW applied)"), isTotalRow: true },
  ];

  const columns = useMemo(
    () => [
      {
        accessorKey: 'metric',
        header: '',
        size: 50,
      },
      {
        accessorKey: 'gap_left',
        enableSorting: false,
        header: <span />,
        maxSize: 1,
        props: { sx: { borderRight: 1.5, borderColor: gapColor, width: '1px' } },
      },
      {
        accessorKey: 'target',
        header: renderMarketCodeHeader,
        props: { sx: { bgcolor: 'background.default', textAlign: 'center' } },
        cell: ({ cell, row, column }) => {
          const value = cell.getValue();
          if (row.original.isTotalRow) {
            return renderPositionCell({ cell });
          }
          if (value !== undefined && row.index !== 0) {
            return renderPositionCell({ cell });
          }
          return value;
        },
      },
      {
        accessorKey: 'origin',
        header: renderMarketCodeHeader,
        cell: ({ cell, row, column }) => {
          const value = cell.getValue();
          if (row.original.isTotalRow) {
            return null; // Will be hidden via colSpan
          }
          if (value !== undefined && row.index !== 0) {
            return renderPositionCell({ cell });
          }
          return value;
        },
      },
    ],
    [i18n.language, gapColor, isMobile, targetCapitalData, originCapitalData]
  );

  const tableData = useMemo(() =>
    metrics.map(({ key, label, isColored, isTotalRow }) => {
      const row = { metric: label, isTotalRow };

      if (isTotalRow) {
        // Initialize total value
        let totalValue = 0;

        // Determine the key for PnL values
        const pnlKey = key.includes('before') ? 'before_pnl' : 'after_pnl';

        // Get target market values
        const targetCurrency = targetCapitalData?.currency;
        const targetPnlValue = targetCapitalData?.[pnlKey] || 0;

        // Adjust target PnL value
        let adjustedTargetValue = targetPnlValue;
        if (key.includes('by_dollar')) {
          if (targetCurrency === 'USDT') {
            adjustedTargetValue = targetPnlValue * (dollarInfo?.price || 0);
          }
        } else if (key.includes('by_usdt')) {
          if (targetCurrency === 'USDT') {
            adjustedTargetValue = targetPnlValue * (usdtInfo?.price || 0);
          }
        }

        // Get origin market values
        const originCurrency = originCapitalData?.currency;
        const originPnlValue = originCapitalData?.[pnlKey] || 0;

        // Adjust origin PnL value
        let adjustedOriginValue = originPnlValue;
        if (key.includes('by_dollar')) {
          if (originCurrency === 'USDT') {
            adjustedOriginValue = originPnlValue * (dollarInfo?.price || 0);
          }
        } else if (key.includes('by_usdt')) {
          if (originCurrency === 'USDT') {
            adjustedOriginValue = originPnlValue * (usdtInfo?.price || 0);
          }
        }

        // Sum up the adjusted values
        totalValue = Number(adjustedTargetValue) + Number(adjustedOriginValue);

        // Set the total value in the target cell and leave origin cell empty
        // row.target = totalValue.toFixed(2); // Format as needed
        row.target = totalValue;
        row.origin = '';
      } else {
        // Existing data handling
        const targetValue = targetCapitalData?.[key];
        const originValue = originCapitalData?.[key];

        row.target = targetValue !== undefined ? targetValue : '';
        row.origin = originValue !== undefined ? originValue : '';
      }

      return row;
    }), [metrics, targetCapitalData, originCapitalData, dollarInfo, usdtInfo]);

  const isLoading = isTargetLoading || isOriginLoading;

  return (
    <Box sx={{ mx: { xs: 0, md: 1 }, p: { xs: 0, md: 1 }, overflowX: 'auto' }}>
      <ReactTableUI
        columns={columns}
        data={tableData}
        options={{
          meta: {
            marketCodes: marketCodeCombination,
          },
        }}

        getCellProps={(cell) => {
          if (!cell?.row?.original) {
            return {
              sx: {
                py: 0.5,
                textAlign: 'center',
              },
            };
          }
        
          const { isTotalRow } = cell.row.original;
          const { id: columnId } = cell.column;
        
          let colSpan = 1;
          let display = 'table-cell';
        
          if (isTotalRow) {
            if (columnId === 'metric') {
              colSpan = 1;
            } else if (columnId === 'gap_left') {
              colSpan = 0;
              display = 'none';
            } else if (columnId === 'target') {
              colSpan = 2; // Adjust according to your needs
            } else if (columnId === 'origin') {
              colSpan = 0;
              display = 'none';
            }
          }
        
          return {
            colSpan,
            sx: {
              py: 0.5,
              textAlign: 'center',
              display, // Hide cell when not needed
              ...(columnId === 'target' ? { bgcolor: 'background.default' } : {}),
            },
          };
        }}

        getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
        showProgressBar={isLoading}
        isLoading={isLoading}
      />
    </Box>
  );
}