import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
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
  useGetWalletStatusQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';
import {
  useCreateFavoriteAssetMutation,
  useDeleteFavoriteAssetMutation,
  useGetFavoriteAssetsQuery,
} from 'redux/api/drf/user';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import { useTranslation } from 'react-i18next';

import { usePrevious, useVisibilityChange } from '@uidotdev/usehooks';

import { DateTime } from 'luxon';

import intersection from 'lodash/intersection';
import isEqual from 'lodash/isEqual';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';
import union from 'lodash/union';

import LightWeightKlineChart from 'components/charts/LightWeightKlineChart';
import ReactTableUI from 'components/ReactTableUI';

import { REGEX } from 'constants';

import renderFundingRateHeader from './renderFundingRateHeader';

import renderChartExpandCell from './renderChartExpandCell';
import renderFundingRateCell from './renderFundingRateCell';
import renderNameCell from './renderNameCell';
import renderPremiumCell from './renderPremiumCell';
import renderPriceCell from './renderPriceCell';
import renderSpreadCell from './renderSpreadCell';
import renderStarCell from './renderStarCell';
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
}) {
  const dispatch = useDispatch();
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const timeoutRef = useRef();

  const isFocused = useVisibilityChange();
  const [lastActive, setLastActive] = useState();
  const [queryKey, setQueryKey] = useState(DateTime.now().toMillis());
  const [ready, setReady] = useState(false);

  const [assets, setAssets] = useState([]);
  const [assetsParam, setAssetsParam] = useState();
  const [marketCodesParam, setMarketCodesParam] = useState();

  const localFavoriteAssets = useSelector(
    (state) =>
      state.home.favoriteAssets[
        `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`
      ]
  );

  const {
    data: realTimeData,
    isLoading,
    isSuccess,
  } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval: '1T', queryKey },
    { skip: !marketCodes }
  );

  const realTimeDataList = useMemo(
    () => orderBy(Object.values(realTimeData ?? {}), 'atp24h', 'desc'),
    [realTimeData]
  );

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  const { data: favoriteAssets } = useGetFavoriteAssetsQuery(
    { marketCodes: Object.values(marketCodes ?? {}).join() },
    {
      skip: !(loggedin && marketCodes),
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
    }
  );

  const { data: walletStatus, isLoading: isWalletStatusLoading } =
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
      }
    );
  const [createFavoriteAsset, createFavoriteRes] =
    useCreateFavoriteAssetMutation();
  const [deleteFavoriteAsset, deleteFavoriteRes] =
    useDeleteFavoriteAssetMutation();

  const handleAddFavoriteAsset = useCallback(
    (baseAsset) => {
      const marketCodeKey = `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`;
      if (loggedin) createFavoriteAsset({ baseAsset, ...marketCodes });
      else dispatch(addLocalFavoriteAsset({ marketCodeKey, baseAsset }));
    },
    [loggedin, marketCodes]
  );
  const handleRemoveFavoriteAsset = useCallback(
    (id) => {
      const marketCodeKey = `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`;
      if (loggedin) deleteFavoriteAsset(id);
      else dispatch(removeLocalFavoriteAsset({ marketCodeKey, id }));
    },
    [loggedin, marketCodes]
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
        size: isMobile ? 40 : 45,
        header: t('Name'),
        cell: renderNameCell,
      },
      ...(marketCodes?.targetMarketCode.includes('SPOT') ||
      marketCodes?.originMarketCode.includes('SPOT')
        ? [
            {
              accessorKey: 'walletStatus',
              enableGlobalFilter: false,
              enableSorting: false,
              size: 25,
              header: <WalletIcon fontSize="small" />,
              cell: isWalletStatusLoading ? '...' : renderWalletStatusCell,
            },
          ]
        : []),
      {
        accessorKey: 'tp',
        enableGlobalFilter: false,
        size: isMobile ? 40 : 65,
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
      ...(!marketCodes?.targetMarketCode.includes('SPOT')
        ? [
            {
              accessorKey: 'targetFundingRate',
              enableGlobalFilter: false,
              size: isMobile ? 40 : 60,
              header: (props) =>
                renderFundingRateHeader({ ...props, marketCodes }),
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
              header: (props) =>
                renderFundingRateHeader({ ...props, marketCodes }),
              cell: renderFundingRateCell,
            },
          ]
        : []),
      {
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        size: isMobile ? 30 : 45,
        header: t('Volume (24h)'),
        cell: renderVolumeCell,
      },
      {
        accessorKey: 'chart',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderChartExpandCell,
        header: <span />,
      },
    ],
    [
      i18n.language,
      loggedin,
      marketCodes,
      isTetherPriceView,
      isWalletStatusLoading,
      isMobile,
    ]
  );

  const data = useMemo(
    () =>
      orderBy(
        realTimeDataList?.map((asset) => {
          const name = asset.base_asset;
          let favoriteAssetId;
          if (loggedin) favoriteAssetId = favoriteAssets?.[name];
          else {
            const index = localFavoriteAssets?.indexOf(name);
            favoriteAssetId = index < 0 ? undefined : index;
          }
          const targetFR = targetFundingRate?.[name]?.[0];
          const originFR = originFundingRate?.[name]?.[0];

          const target = marketCodes?.targetMarketCode.replace(
            REGEX.spotMarketSuffix,
            ''
          );
          const origin = marketCodes?.originMarketCode.replace(
            REGEX.spotMarketSuffix,
            ''
          );
          const walletStatusSummary = {
            right: intersection(
              walletStatus?.[name]?.[target]?.withdraw,
              walletStatus?.[name]?.[origin]?.deposit
            ),
            left: intersection(
              walletStatus?.[name]?.[target]?.deposit,
              walletStatus?.[name]?.[origin]?.withdraw
            ),
            all: union(
              walletStatus?.[name]?.[target]?.deposit,
              walletStatus?.[name]?.[target]?.withdraw,
              walletStatus?.[name]?.[origin]?.deposit,
              walletStatus?.[name]?.[origin]?.withdraw
            ),
          };

          return {
            name,
            favoriteAssetId,
            icon: assetsData?.[name]?.icon,
            spread: asset ? asset.SL_close - asset.LS_close : '',
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
            walletNetworks: walletStatus?.[name],
            chart: true,
          };
        }) ?? [],
        (o) => !isUndefined(o.favoriteAssetId),
        'desc'
      ),
    [
      marketCodes,
      realTimeDataList,
      targetFundingRate,
      originFundingRate,
      walletStatus,
      assetsData,
      favoriteAssets,
      localFavoriteAssets,
      loggedin,
    ]
  );

  const prevAssets = usePrevious(assets);
  useEffect(() => {
    if (isSuccess) {
      if (realTimeDataList.length > 0) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        const realTimeAssets = realTimeDataList
          .map((item) => item.base_asset)
          .sort();
        if (!isEqual(prevAssets, realTimeAssets)) {
          setAssets(realTimeAssets);
        }
        setReady(true);
      } else {
        setReady(false);
        timeoutRef.current = setTimeout(() => {
          setAssets([]);
          setReady(true);
        }, 5000);
      }
    }
  }, [isSuccess, realTimeDataList]);

  useEffect(() => {
    if (!isEqual(prevAssets, assets)) setAssetsParam(assets.join(','));
  }, [assets]);

  useEffect(() => {
    setAssetsParam();
    setMarketCodesParam(marketCodes);
  }, [marketCodes]);

  useEffect(() => {
    if (!isFocused) setLastActive(DateTime.now().toMillis());
    else if (lastActive) {
      const diff = DateTime.now()
        .diff(DateTime.fromMillis(lastActive), ['minutes'])
        .toObject();
      if (diff.minutes > 60) {
        window.location.reload();
      } else if (diff.minutes > 10) {
        setAssets([]);
        setReady(false);
        setQueryKey(DateTime.now().toMillis());
      }
    }
  }, [isFocused]);

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
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [pagination, setPagination] = React.useState({
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
    ({ row, extraData }) => (
      <Box>
        <LightWeightKlineChart baseAssetData={row.original} {...extraData} />
      </Box>
    ),
    []
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

  return (
    <Box sx={{ boxShadow: 2 }}>
      <ReactTableUI
        ref={tableRef}
        columns={columns}
        data={data}
        extraData={{
          marketCodes,
          queryKey,
          isKimpExchange,
          isTetherPriceView,
          handleAddFavoriteAsset,
          handleRemoveFavoriteAsset,
        }}
        options={{
          getRowId: (row) => row.name,
          defaultColumn: { sortingFn: sortWithStarred },
          state: {
            columnVisibility,
            expanded,
            globalFilter,
            pagination,
          },

          onExpandedChange: (newExpanded) => setExpanded(newExpanded()),
          onPaginationChange: setPagination,
        }}
        renderSubComponent={renderSubComponent}
        getCellProps={() => ({ sx: { height: 50 } })}
        getRowProps={(row) => ({
          onClick: () => row.toggleExpanded(!row.getIsExpanded()),
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { bgcolor: theme.palette.background.paper }
              : {}),
          },
        })}
        showProgressBar={
          isLoading ||
          createFavoriteRes.isLoading ||
          deleteFavoriteRes.isLoading
        }
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
