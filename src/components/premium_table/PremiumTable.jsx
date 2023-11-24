import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';

import { useDispatch, useSelector } from 'react-redux';

import {
  addLocalFavoriteAsset,
  removeLocalFavoriteAsset,
} from 'redux/reducers/home';
import {
  useGetAssetsQuery,
  useGetFundingRateQuery,
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

import isEqual from 'lodash/isEqual';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';

import LightWeightKlineChart from 'components/charts/LightWeightKlineChart';

import ReactTable from './ReactTable';

import renderFundingRateHeader from './renderFundingRateHeader';

import renderChartExpandCell from './renderChartExpandCell';
import renderFundingRateCell from './renderFundingRateCell';
import renderNameCell from './renderNameCell';
import renderPremiumCell from './renderPremiumCell';
import renderPriceCell from './renderPriceCell';
import renderSpreadCell from './renderSpreadCell';
import renderStarCell from './renderStarCell';
import renderVolumeCell from './renderVolumeCell';

export default function PremiumTable({
  marketCodes,
  searchKeyword,
  loggedin,
  isKimpExchange,
  isTetherPriceView,
  isMobile,
}) {
  const dispatch = useDispatch();
  const { i18n, t } = useTranslation();

  const timeoutRef = useRef();

  const isFocused = useVisibilityChange();
  const [lastActive, setLastActive] = useState();
  const [queryKey, setQueryKey] = useState(DateTime.now().toMillis());
  const [ready, setReady] = useState(false);

  const [assets, setAssets] = useState([]);
  const [fundingRateAssets, setFundingRateAssets] = useState();
  const [fundingRateMarketCodes, setFundingRateMarketCodes] = useState();

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
      baseAsset: fundingRateAssets,
      marketCode: fundingRateMarketCodes?.targetMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !ready ||
        !fundingRateAssets ||
        !fundingRateMarketCodes ||
        fundingRateMarketCodes?.targetMarketCode.includes('SPOT'),
    }
  );
  const { data: originFundingRate } = useGetFundingRateQuery(
    {
      baseAsset: fundingRateAssets,
      marketCode: fundingRateMarketCodes?.originMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !ready ||
        !fundingRateAssets ||
        !fundingRateMarketCodes ||
        fundingRateMarketCodes?.originMarketCode.includes('SPOT'),
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
        size: isMobile ? 40 : 50,
        header: t('Name'),
        cell: renderNameCell,
      },
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
    [i18n.language, loggedin, marketCodes, isTetherPriceView, isMobile]
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
          const targetFR = targetFundingRate?.[name];
          const originFR = originFundingRate?.[name];
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
            chart: true,
          };
        }) ?? [],
        (o) => !isUndefined(o.favoriteAssetId),
        'desc'
      ),
    [
      realTimeDataList,
      targetFundingRate,
      originFundingRate,
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
    if (!isEqual(prevAssets, assets)) setFundingRateAssets(assets.join(','));
  }, [assets]);

  useEffect(() => {
    setFundingRateAssets();
    setFundingRateMarketCodes(marketCodes);
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

  const renderSubComponent = useCallback(
    ({ row, contextData }) => (
      <Box>
        <LightWeightKlineChart baseAsset={row.original} {...contextData} />
      </Box>
    ),
    []
  );

  return (
    <ReactTable
      key={`${marketCodes?.targetMarketCode}-${marketCodes?.originMarketCode}`}
      columns={columns}
      data={data}
      isLoading={!ready}
      showProgressBar={
        isLoading || createFavoriteRes.isLoading || deleteFavoriteRes.isLoading
      }
      contextData={{
        marketCodes,
        queryKey,
        isKimpExchange,
        isTetherPriceView,
        handleAddFavoriteAsset,
        handleRemoveFavoriteAsset,
      }}
      searchKeyword={searchKeyword}
      renderSubComponent={renderSubComponent}
    />
  );
}
