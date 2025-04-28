import React, { useMemo, useState } from 'react';

import Box from '@mui/material/Box';

import ExpandCircleDownIcon from '@mui/icons-material/ExpandCircleDown';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';
import {
  useGetFuturesPositionQuery,
  useGetSpotPositionQuery,
} from 'redux/api/drf/tradecore';

import { useTranslation } from 'react-i18next';

import ReactTableUI from 'components/ReactTableUI';

import renderAssetIconCell from 'components/tables/common/renderAssetIconCell';
import renderColoredSignedNumberCell from 'components/tables/common/renderColoredSignedNumberCell';

import renderHedgeStatus from 'components/tables/position/renderHedgeStatus';
import renderMarketCodeHeader from 'components/tables/position/renderMarketCodeHeader';
import renderPositionCell from 'components/tables/position/renderPositionCell';

const ERROR_RATE = 0.5;

export default function PositionTable({ marketCodeCombination }) {
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 50 });

  const { data: assetsData } = useGetAssetsQuery();

  const { target, origin, tradeConfigUuid } = marketCodeCombination;

  const { data: targetSpotData, ...targetSpotResults } =
    useGetSpotPositionQuery(
      { marketCode: target?.value, tradeConfigUuid },
      { skip: !target || !target.isSpot }
    );

  const { data: originSpotData, ...originSpotResults } =
    useGetSpotPositionQuery(
      { marketCode: origin?.value, tradeConfigUuid },
      { skip: !origin || !origin.isSpot }
    );

  const { data: targetFuturesData, ...targetFuturesResults } =
    useGetFuturesPositionQuery(
      { marketCode: target?.value, tradeConfigUuid },
      { skip: !target || target.isSpot }
    );

  const { data: originFuturesData, ...originFuturesResults } =
    useGetFuturesPositionQuery(
      { marketCode: origin?.value, tradeConfigUuid },
      { skip: !origin || origin.isSpot }
    );

  const gapColor = theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100';

  const columns = useMemo(
    () => [
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 5,
        header: <span />,
        cell: renderAssetIconCell,
      },
      {
        accessorKey: 'asset',
        header: t('Asset'),
        props: { sx: { textAlign: 'left' } },
        size: 35,
      },
      {
        accessorKey: 'hedge_status',
        header: t('Hedge Status'),
        cell: renderHedgeStatus,
        size: isMobile ? 40 : 80,
      },
      {
        accessorKey: 'gap_left',
        enableSorting: false,
        header: <span />,
        maxSize: 1,
        props: {
          sx: { borderRight: 1.5, borderColor: gapColor, width: '1px' },
        },
      },
      {
        accessorKey: 'target',
        header: renderMarketCodeHeader,
        props: { sx: { bgcolor: 'background.default' } },
        columns: [
          {
            accessorKey: 'target_market_pos',
            size: isMobile ? 40 : 90,
            header: t('market.Position'),
            cell: renderPositionCell,
            slotProps: { header: { sx: { bgcolor: 'background.default' } } },
          },
          ...(marketCodeCombination.target.isSpot
            ? []
            : [
                {
                  accessorKey: 'target_market_roi',
                  size: isMobile ? 40 : 90,
                  header: `${t('ROI')}(%)`,
                  cell: renderColoredSignedNumberCell,
                },
                {
                  accessorKey: 'target_market_entry_price',
                  size: isMobile ? 40 : 90,
                  header: t('Entry Price'),
                },
                {
                  accessorKey: 'target_market_liquidation_price',
                  size: isMobile ? 40 : 90,
                  header: t('Liquidation Price'),
                },
                {
                  accessorKey: 'target_market_margin_type',
                  size: isMobile ? 40 : 90,
                  header: t('Margin Type'),
                },
              ]),
        ],
      },
      {
        accessorKey: 'gap_right',
        enableSorting: false,
        header: <span />,
        maxSize: 1,
        props: { sx: { borderLeft: 1.5, borderColor: gapColor, width: '1px' } },
      },
      {
        accessorKey: 'origin',
        header: renderMarketCodeHeader,
        columns: [
          {
            accessorKey: 'origin_market_pos',
            size: isMobile ? 40 : 90,
            header: t('market.Position'),
            cell: renderPositionCell,
          },
          ...(marketCodeCombination.origin.isSpot
            ? []
            : [
                {
                  accessorKey: 'origin_market_roi',
                  size: isMobile ? 40 : 90,
                  header: `${t('ROI')}(%)`,
                  cell: renderColoredSignedNumberCell,
                },
                {
                  accessorKey: 'origin_market_entry_price',
                  size: isMobile ? 40 : 90,
                  header: t('Entry Price'),
                },
                {
                  accessorKey: 'origin_market_liquidation_price',
                  size: isMobile ? 40 : 90,
                  header: t('Liquidation Price'),
                },
                {
                  accessorKey: 'origin_market_margin_type',
                  size: isMobile ? 40 : 90,
                  header: t('Margin Type'),
                },
              ]),
        ],
      },
    ],
    [i18n.language, marketCodeCombination, gapColor, isMobile]
  );

  const tableData = useMemo(() => {
    const isTargetSpot = marketCodeCombination.target.isSpot;
    const isOriginSpot = marketCodeCombination.origin.isSpot;

    const targetData = (isTargetSpot ? targetSpotData : targetFuturesData) || [];
    const originData = (isOriginSpot ? originSpotData : originFuturesData) || [];
    
    // Create a map of assets
    const assetsMap = {};
    
    // Process target market data
    targetData.forEach(item => {
      const assetKey = item.asset || item.base_asset;
      if (assetKey && assetKey !== 'KRW') {
        if (!assetsMap[assetKey]) assetsMap[assetKey] = {};
        assetsMap[assetKey].target = item;
      }
    });
    
    // Process origin market data
    originData.forEach(item => {
      const assetKey = item.asset || item.base_asset;
      if (assetKey && assetKey !== 'KRW') {
        if (!assetsMap[assetKey]) assetsMap[assetKey] = {};
        assetsMap[assetKey].origin = item;
      }
    });

    return Object.keys(assetsMap)
      .map((key) => {
        const targetItem = assetsMap[key].target || {};
        const originItem = assetsMap[key].origin || {};
        
        const data = {
          asset: key,
          icon: assetsData?.[key]?.icon,
          target_market_pos: isTargetSpot 
            ? Number(targetItem.free || 0)
            : Number(parseFloat(targetItem.qty || 0).toFixed(3)),
          target_market_roi: Number(parseFloat(targetItem.ROI || 0).toFixed(3)),
          target_market_entry_price: Number(parseFloat(targetItem.entry_price || 0).toFixed(3)),
          target_market_liquidation_price: Number(parseFloat(targetItem.liquidation_price || 0).toFixed(3)),
          target_market_margin_type: targetItem.margin_type,
          origin_market_pos: isOriginSpot 
            ? Number(originItem.free || 0)
            : Number(parseFloat(originItem.qty || 0).toFixed(3)),
          origin_market_roi: Number(parseFloat(originItem.ROI || 0).toFixed(3)),
          origin_market_entry_price: Number(parseFloat(originItem.entry_price || 0).toFixed(3)),
          origin_market_liquidation_price: Number(parseFloat(originItem.liquidation_price || 0).toFixed(3)),
          origin_market_margin_type: originItem.margin_type,
        };
        const hedge = Math.abs(Number(data.target_market_pos) + Number(data.origin_market_pos));
        return {
          hedge_status: parseFloat((hedge || 0).toFixed(5)) <= ERROR_RATE,
          ...data,
        };
      });
  }, [
    assetsData,
    marketCodeCombination,
    targetFuturesData,
    targetSpotData,
    originFuturesData,
    originSpotData,
  ]);

  const isLoading =
    targetSpotResults.isFetching ||
    targetFuturesResults.isFetching ||
    originSpotResults.isFetching ||
    originFuturesResults.isFetching;

  return (
    <Box sx={{ mx: { xs: 0, md: 1 }, p: { xs: 0, md: 1 }, overflowX: 'auto' }}>
      <ReactTableUI
        enableTablePaginationUI
        // ref={tableRef}
        columns={columns}
        data={tableData}
        options={{
          enableRowSelection: true,
          state: { pagination },
          onPaginationChange: setPagination,
          meta: {
            marketCodes: marketCodeCombination,
            expandIcon: ExpandCircleDownIcon,
          },
        }}
        getCellProps={(cell) => ({
          sx: {
            py: 0.5,
            textAlign: 'center',
            ...(cell?.column.id.startsWith('target')
              ? { bgcolor: 'background.default' }
              : {}),
          },
        })}
        getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
        showProgressBar={isLoading}
        isLoading={isLoading}
      />
    </Box>
  );
}
