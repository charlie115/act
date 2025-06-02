import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InsightsIcon from '@mui/icons-material/Insights';
import WalletIcon from '@mui/icons-material/Wallet';

import { useTheme } from '@mui/material/styles';

import { useDispatch, useSelector } from 'react-redux';

import {
  addLocalFavoriteAsset,
  removeLocalFavoriteAsset,
} from 'redux/reducers/home';
import {
  useGetAssetsQuery,
  useGetFundingRateQuery,
  useGetKlineVolatilityQuery,
  useGetWalletStatusQuery,
  usePostAssetMutation,
  useGetAiRankRecommendationQuery,
} from 'redux/api/drf/infocore';
import {
  useCreateFavoriteAssetMutation,
  useDeleteFavoriteAssetMutation,
  useGetFavoriteAssetsQuery,
} from 'redux/api/drf/user';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import { useTranslation } from 'react-i18next';

import { usePrevious } from '@uidotdev/usehooks';

import intersection from 'lodash/intersection';
import isEqual from 'lodash/isEqual';
import isFunction from 'lodash/isFunction';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';
import union from 'lodash/union';

import AssetTradeConfig from 'components/AssetTradeConfig';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI from 'components/ReactTableUI';

import { REGEX } from 'constants';

import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderFundingRateHeader from 'components/tables/common/renderFundingRateHeader';
import renderFundingRateCell from 'components/tables/common/renderFundingRateCell';

import renderNameCell from './renderNameCell';
import renderPremiumCell from './renderPremiumCell';
import renderPriceCell from './renderPriceCell';
import renderSpreadCell from './renderSpreadCell';
import renderStarCell from './renderStarCell';
import renderVolatilityCell from './renderVolatilityCell';
import renderVolumeCell from './renderVolumeCell';
import renderWalletStatusCell from './renderWalletStatusCell';

const DEFAULT_PAGE_SIZE = 50;

function PremiumTable({
  marketCodes,
  searchKeyword,
  loggedin,
  isKimpExchange,
  isTetherPriceView,
  isMobile,
  queryKey,
  onDisconnected,
}) {
  const dispatch = useDispatch();
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const premiumDataViewerRef = useRef();
  const timeoutRef = useRef();

  const [ready, setReady] = useState(false);

  const [assets, setAssets] = useState([]);
  const [assetsParam, setAssetsParam] = useState();
  const [marketCodesParam, setMarketCodesParam] = useState();

  const [klineInterval, setKlineInterval] = useState('1T');

  const [triggerConfig, setTriggerConfig] = useState();

  const localFavoriteAssets = useSelector(
    (state) =>
      state.home.favoriteAssets[
        `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`
      ]
  );

  const [connectionLost, setConnectionLost] = useState(false);
  const documentVisibilityRef = useRef(document.visibilityState);
  const reconnectingRef = useRef(false);

  const {
    data: realTimeData,
    isLoading: isRealTimeDataLoading,
    isSuccess,
  } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval: '1T', queryKey, component: 'premium-table' },
    { 
      skip: !marketCodes,
      refetchOnFocus: false,
      refetchOnReconnect: false
    }
  );

  const realTimeDataList = useMemo(() => {
    if (realTimeData?.disconnected || !realTimeData) return [];
    
    const dataArray = Array.isArray(realTimeData) 
      ? realTimeData 
      : Object.values(realTimeData).filter(item => typeof item === 'object' && item !== null);
      
    return orderBy(dataArray, 'atp24h', 'desc');
  }, [realTimeData]);

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery(undefined, { refetchOnFocus: false });
  const [postAsset] = usePostAssetMutation();

  const { data: favoriteAssets } = useGetFavoriteAssetsQuery(
    { marketCodes: Object.values(marketCodes ?? {}).join() },
    {
      skip: !(loggedin && marketCodes),
      refetchOnFocus: false
    }
  );

  const { data: targetFundingRate } = useGetFundingRateQuery(
    {
      baseAsset: assetsParam,
      marketCode: marketCodesParam?.targetMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !ready ||
        !assetsParam ||
        !marketCodesParam ||
        marketCodesParam?.targetMarketCode.includes('SPOT'),
      refetchOnFocus: false
    }
  );
  const { data: originFundingRate } = useGetFundingRateQuery(
    {
      baseAsset: assetsParam,
      marketCode: marketCodesParam?.originMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !ready ||
        !assetsParam ||
        !marketCodesParam ||
        marketCodesParam?.originMarketCode.includes('SPOT'),
      refetchOnFocus: false
    }
  );
  const { data: walletStatus, isSuccess: isWalletStatusSuccess } =
    useGetWalletStatusQuery(
      { baseAsset: assetsParam, ...marketCodesParam },
      {
        pollingInterval: 1000 * 60,
        skip:
          !ready ||
          !assetsParam ||
          !marketCodesParam ||
          !(
            marketCodesParam?.targetMarketCode.includes('SPOT') ||
            marketCodesParam?.originMarketCode.includes('SPOT')
          ),
        refetchOnFocus: false
      }
    );
  const lastMarketCodesRef = useRef();
  const [marketCodeChangeCounter, setMarketCodeChangeCounter] = useState(0);
  const { 
    data: aiRankRecommendations, 
    isError: isAiRecsError,
    error: aiRecsError
  } = useGetAiRankRecommendationQuery(
    { 
      target_market_code: marketCodesParam?.targetMarketCode,
      origin_market_code: marketCodesParam?.originMarketCode,
      _t: `${marketCodeChangeCounter}`,
    },
    { 
      pollingInterval: 1000 * 60,
      skip: !ready || !marketCodesParam,
      refetchOnMountOrArgChange: true,
      refetchOnFocus: false
    }
  );

  const { data: klineVolatilityData } = useGetKlineVolatilityQuery(
    { baseAsset: assetsParam, ...marketCodesParam },
    { 
      pollingInterval: 1000 * 60,
      skip: !ready || !assetsParam || !marketCodesParam,
      refetchOnFocus: false
    }
  );

  const [createFavoriteAsset, createFavoriteRes] =
    useCreateFavoriteAssetMutation();
  const [deleteFavoriteAsset, deleteFavoriteRes] =
    useDeleteFavoriteAssetMutation();

  const onAddFavoriteAsset = useCallback(
    (baseAsset) => {
      const marketCodeKey = `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`;
      if (loggedin) createFavoriteAsset({ baseAsset, ...marketCodes });
      else dispatch(addLocalFavoriteAsset({ marketCodeKey, baseAsset }));
    },
    [loggedin, marketCodes]
  );
  const onRemoveFavoriteAsset = useCallback(
    (id) => {
      const marketCodeKey = `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`;
      if (loggedin) deleteFavoriteAsset(id);
      else dispatch(removeLocalFavoriteAsset({ marketCodeKey, id }));
    },
    [loggedin, marketCodes]
  );

  const onTriggerConfigChange = useCallback(
    (value) => setTriggerConfig(value),
    []
  );

  const columns = useMemo(
    () => [
      {
        accessorKey: 'favoriteAssetId',
        enableGlobalFilter: false,
        enableSorting: false,
        maxSize: 18,
        header: <span />,
        cell: renderStarCell,
      },
      {
        accessorKey: 'name',
        enableGlobalFilter: true,
        size: isMobile ? 35 : 45,
        header: '',
        cell: renderNameCell,
      },
      ...(marketCodes?.targetMarketCode.includes('SPOT') ||
      marketCodes?.originMarketCode.includes('SPOT')
        ? [
            {
              accessorKey: 'walletStatus',
              enableGlobalFilter: false,
              enableSorting: false,
              size: isMobile ? 15 : 25,
              header: <WalletIcon fontSize={isMobile ? 'inherit' : 'small'} />,
              cell: renderWalletStatusCell,
            },
          ]
        : []),
      {
        accessorKey: 'tp',
        enableGlobalFilter: false,
        size: isMobile ? 50 : 65,
        header: t('Current Price'),
        cell: renderPriceCell,
      },
      {
        accessorKey: 'LS_close',
        enableGlobalFilter: false,
        size: isMobile ? 35 : 50,
        header: isKimpExchange
          ? [isTetherPriceView ? t('Enter Tether') : t('Enter KIMP')]
          : t('LS Premium'),
        cell: renderPremiumCell,
      },
      {
        accessorKey: 'SL_close',
        enableGlobalFilter: false,
        size: isMobile ? 35 : 50,
        header: isKimpExchange
          ? [isTetherPriceView ? t('Exit Tether') : t('Exit KIMP')]
          : t('SL Premium'),
        cell: renderPremiumCell,
      },
      {
        accessorKey: 'spread',
        enableGlobalFilter: false,
        size: 50,
        header: t('Spread'),
        cell: renderSpreadCell,
      },
      {
        accessorKey: 'volatility',
        enableGlobalFilter: false,
        size: isMobile ? 30 : 40,
        header: t('Volatility'),
        cell: renderVolatilityCell,
      },
      ...(!marketCodes?.targetMarketCode.includes('SPOT')
        ? [
            {
              accessorKey: 'targetFundingRate',
              enableGlobalFilter: false,
              size: isMobile ? 40 : 60,
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
            },
          ]
        : []),
      ...(!marketCodes?.originMarketCode.includes('SPOT')
        ? [
            {
              accessorKey: 'originFundingRate',
              enableGlobalFilter: false,
              size: isMobile ? 40 : 60,
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
            },
          ]
        : []),
      {
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        size: isMobile ? 45 : 55,
        header: t('Volume (24h)'),
        cell: renderVolumeCell,
      },
      {
        accessorKey: 'chart',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [i18n.language, loggedin, marketCodes, isTetherPriceView, isMobile]
  );

  const volatilityData = useMemo(() => {
    if (!klineVolatilityData || !Array.isArray(klineVolatilityData)) return {};
    
    const result = {};
    klineVolatilityData.forEach(item => {
      if (item && item.base_asset) {
        result[item.base_asset] = parseFloat(item.mean_diff || 0).toFixed(2);
      }
    });
    
    return result;
  }, [klineVolatilityData]);

  const validAiRankRecommendations = useMemo(() => {
    if (isAiRecsError && aiRecsError?.status === 404) {
      return null;
    }
    return aiRankRecommendations;
  }, [aiRankRecommendations, isAiRecsError, aiRecsError]);

  const data = useMemo(() => {
    if (!realTimeDataList || realTimeDataList.length === 0) {
      return [];
    }
    
    const processedData = realTimeDataList.map((asset) => {
      if (!asset || !asset.base_asset) return null;
      
      const name = asset.base_asset;
      let favoriteAssetId;
      
      if (loggedin) {
        favoriteAssetId = favoriteAssets?.[name];
      } else {
        const index = localFavoriteAssets?.indexOf(name) ?? -1;
        favoriteAssetId = index >= 0 ? index : undefined;
      }
      
      const targetFR = targetFundingRate?.[name]?.[0];
      const originFR = originFundingRate?.[name]?.[0];
      
      // Find AI recommendation for this asset if available
      const aiRankRecommendation = validAiRankRecommendations?.find(
        recommendation => recommendation.base_asset === name
      );
      
      let walletStatusSummary = {
        right: [],
        left: [],
        all: []
      };
      
      if (walletStatus && walletStatus[name] && marketCodes) {
        const target = marketCodes.targetMarketCode.replace(
          REGEX.spotMarketSuffix,
          ''
        );
        const origin = marketCodes.originMarketCode.replace(
          REGEX.spotMarketSuffix,
          ''
        );
        
        const targetWithdraw = walletStatus[name][target]?.withdraw || [];
        const targetDeposit = walletStatus[name][target]?.deposit || [];
        const originWithdraw = walletStatus[name][origin]?.withdraw || [];
        const originDeposit = walletStatus[name][origin]?.deposit || [];
        
        walletStatusSummary = {
          right: intersection(targetWithdraw, originDeposit),
          left: intersection(targetDeposit, originWithdraw),
          all: union(targetDeposit, targetWithdraw, originDeposit, originWithdraw)
        };
      }
      
      return {
        name,
        favoriteAssetId,
        icon: assetsData?.[name]?.icon,
        spread: asset ? asset.SL_close - asset.LS_close : '',
        volatility: volatilityData[name] || '0.00',
        ...(targetFR
          ? {
              targetFundingRate: targetFR.funding_rate * 100,
              targetFR,
            }
          : {}),
        ...(originFR
          ? {
              originFundingRate: originFR.funding_rate * 100,
              originFR,
            }
          : {}),
        ...asset,
        walletStatus: walletStatusSummary,
        walletNetworks: walletStatus?.[name] || {},
        aiRankRecommendation,
        chart: true,
      };
    }).filter(Boolean);
    
    return orderBy(
      processedData,
      [(o) => !isUndefined(o.favoriteAssetId)],
      ['desc']
    );
  }, [
    realTimeDataList,
    assetsData,
    favoriteAssets,
    localFavoriteAssets,
    targetFundingRate,
    originFundingRate,
    walletStatus,
    volatilityData,
    marketCodes,
    loggedin,
    validAiRankRecommendations,
  ]);

  const prevAssets = usePrevious(assets);

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    if (realTimeData?.disconnected) {
      if (!connectionLost) {
        setConnectionLost(true);
        if (!reconnectingRef.current) {
          reconnectingRef.current = true;
          timeoutRef.current = setTimeout(() => {
            onDisconnected();
            timeoutRef.current = null;
            setTimeout(() => {
              reconnectingRef.current = false;
            }, 5000);
          }, 3000);
        }
      }
      return;
    }
    
    if (realTimeData && 
       !realTimeData.disconnected && 
       Object.keys(realTimeData).length > 0 && 
       !Array.isArray(realTimeData)) {
      if (connectionLost) {
        setConnectionLost(false);
      }
      return;
    }
    
    if (isSuccess && (!realTimeData || 
       Object.keys(realTimeData).length === 0 || 
       (Array.isArray(realTimeData) && realTimeData.length === 0))) {
      
      if (!connectionLost && !reconnectingRef.current) {
        setConnectionLost(true);
        reconnectingRef.current = true;
        timeoutRef.current = setTimeout(() => {
          onDisconnected();
          timeoutRef.current = null;
          setTimeout(() => {
            reconnectingRef.current = false;
          }, 5000);
        }, 5000);
      }
    }
  }, [realTimeData, isSuccess, onDisconnected, connectionLost]);

  useEffect(() => {
    if (isSuccess && realTimeDataList && realTimeDataList.length > 0) {
      const realTimeAssets = realTimeDataList
        .map(item => item.base_asset)
        .filter(Boolean)
        .sort();
      
      if (!isEqual(prevAssets, realTimeAssets)) {
        setAssets(realTimeAssets);
      }
    }
  }, [isSuccess, realTimeDataList, prevAssets]);

  useEffect(() => {
    if (!isEqual(prevAssets, assets)) {
      if (assets.length > 0) {
        setAssetsParam(assets.join(','));
        setReady(true);
      } else {
        setReady(false);
      }
    }
  }, [assets, prevAssets]);

  useEffect(() => {
    setAssetsParam();
    setMarketCodesParam(marketCodes);
  }, [marketCodes]);

  const prevIsAssetsDataSuccess = usePrevious(isAssetsDataSuccess);
  useEffect(() => {
    if (!prevIsAssetsDataSuccess && isAssetsDataSuccess)
      if (!isEqual(prevAssets, assets))
        assets.forEach((asset) => {
          if (!assetsData?.[asset]) postAsset({ symbol: asset });
        });
  }, [assets, assetsData, isAssetsDataSuccess]);

  useEffect(() => {
    if (createFavoriteRes?.isSuccess) window.scrollTo(0, 0);
  }, [createFavoriteRes?.isSuccess]);

  const [columnVisibility, setColumnVisibility] = useState({});
  const [expanded, setExpanded] = useState({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });

  const sortWithStarred = useCallback((rowA, rowB, columnId) => {
    if (
      !isUndefined(rowA.original.favoriteAssetId) &&
      isUndefined(rowB.original.favoriteAssetId)
    )
      return -1;
    if (
      !isUndefined(rowB.original.favoriteAssetId) &&
      isUndefined(rowA.original.favoriteAssetId)
    )
      return 0;
    if (rowA.original[columnId] > rowB.original[columnId]) return 1;
    if (rowA.original[columnId] < rowB.original[columnId]) return -1;
    return 0;
  }, []);

  const renderSubComponent = useCallback(
    ({ row, meta }) => (
      <Box>
        <PremiumDataChartViewer
          showExchangeWallets
          showFundingRate
          showFundingRateDiff
          ref={premiumDataViewerRef}
          baseAssetData={row.original}
          onIntervalChange={(newInterval) => setKlineInterval(newInterval)}
          {...meta}
        />
        {loggedin && (
          <AssetTradeConfig
            showTable
            premiumDataViewerRef={premiumDataViewerRef}
            baseAsset={row.original.name}
            onTriggerConfigChange={onTriggerConfigChange}
            interval={meta.klineInterval}
            {...meta}
          />
        )}
      </Box>
    ),
    [loggedin]
  );

  useEffect(() => {
    setGlobalFilter(searchKeyword);
  }, [searchKeyword]);

  useEffect(() => {
    setColumnVisibility({
      chart: !isMobile,
      spread: !isMobile,
      favoriteAssetId: !isMobile,
    });
  }, [isMobile]);

  const tableRef = useRef();
  const rows = tableRef.current?.getRowModel().rows;

  const getRowId = useCallback((row) => row.name, []);
  const onExpandedChange = useCallback(
    (newExpanded) =>
      setExpanded(isFunction(newExpanded) ? newExpanded() : newExpanded),
    []
  );

  useEffect(() => () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (marketCodesParam && lastMarketCodesRef.current && 
        (lastMarketCodesRef.current.targetMarketCode !== marketCodesParam.targetMarketCode ||
         lastMarketCodesRef.current.originMarketCode !== marketCodesParam.originMarketCode)) {
      
      setMarketCodeChangeCounter(prev => prev + 1);
    }
    
    lastMarketCodesRef.current = { ...marketCodesParam };
  }, [marketCodesParam]);

  useEffect(() => {
    if (isAiRecsError) {
      console.log("AI Recommendations error:", aiRecsError);
    }
  }, [validAiRankRecommendations, isAiRecsError, aiRecsError]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const wasHidden = documentVisibilityRef.current === 'hidden';
      documentVisibilityRef.current = document.visibilityState;
      
      if (wasHidden && document.visibilityState === 'visible') {
        if (connectionLost && !reconnectingRef.current) {
          reconnectingRef.current = true;
          onDisconnected();
          setTimeout(() => {
            reconnectingRef.current = false;
          }, 5000);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connectionLost, onDisconnected]);

  // Memoize the columns to prevent unnecessary recalculations
  const columnVisibilityMemo = useMemo(() => ({
    chart: !isMobile,
    spread: !isMobile,
    favoriteAssetId: !isMobile,
  }), [isMobile]);

  // Memoize the table meta
  const tableMeta = useMemo(() => ({
    triggerConfig,
    klineInterval,
    marketCodes,
    queryKey,
    isMobile,
    isKimpExchange,
    isTetherPriceView,
    onAddFavoriteAsset,
    onRemoveFavoriteAsset,
    theme,
    expandIcon: InsightsIcon,
  }), [
    triggerConfig,
    klineInterval,
    marketCodes,
    queryKey,
    isMobile,
    isKimpExchange,
    isTetherPriceView,
    onAddFavoriteAsset,
    onRemoveFavoriteAsset,
    theme,
  ]);

  useEffect(() => {
    setColumnVisibility(columnVisibilityMemo);
  }, [columnVisibilityMemo]);

  const isTableLoading = useMemo(() => 
    isRealTimeDataLoading || createFavoriteRes.isLoading || deleteFavoriteRes.isLoading,
    [isRealTimeDataLoading, createFavoriteRes.isLoading, deleteFavoriteRes.isLoading]
  );

  return (
    <Box sx={{ boxShadow: 2, borderRadius: '6px !important', overflow: 'hidden' }}>
      <ReactTableUI
        ref={tableRef}
        columns={columns}
        data={data}
        options={{
          getRowId,
          defaultColumn: { sortingFn: sortWithStarred },
          state: {
            columnVisibility,
            expanded,
            globalFilter,
            pagination,
          },
          onExpandedChange,
          onPaginationChange: setPagination,
          meta: tableMeta,
        }}
        renderSubComponent={renderSubComponent}
        getCellProps={() => ({ sx: { height: 40 } })}
        getRowProps={(row) => ({
          onClick: () => row.toggleExpanded(!row.getIsExpanded()),
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { bgcolor: theme.palette.background.paper }
              : {}),
          },
        })}
        showProgressBar={isTableLoading}
        isLoading={!ready}
      />
      {ready && (
        <Box sx={{ textAlign: 'center' }}>
          {rows?.length >= DEFAULT_PAGE_SIZE && (
            <Button
              color={
                tableRef.current?.getCanNextPage() ? 'primary' : 'secondary'
              }
              endIcon={
                tableRef.current?.getCanNextPage() ? (
                  <ExpandMoreIcon />
                ) : (
                  <ExpandLessIcon />
                )
              }
              onClick={() => {
                tableRef.current?.setPageSize(
                  tableRef.current?.getCanNextPage()
                    ? pagination.pageSize + DEFAULT_PAGE_SIZE
                    : DEFAULT_PAGE_SIZE
                );
                if (!tableRef.current?.getCanNextPage()) window.scrollTo(0, 0);
              }}
              sx={{
                fontSize: '0.85rem',
                fontStyle: 'italic',
                letterSpacing: '0.085em',
                textTransform: 'none',
                ':hover': { backgroundColor: 'unset' },
              }}
            >
              {tableRef.current?.getCanNextPage()
                ? t('See more')
                : t('See less')}
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
}

export default React.memo(PremiumTable);
