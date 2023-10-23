import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';
import ToggleButton from '@mui/material/ToggleButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';

import { alpha } from '@mui/material/styles';

import { useDispatch, useSelector } from 'react-redux';
import {
  addLocalFavoriteAsset,
  removeLocalFavoriteAsset,
  togglePriceView,
} from 'redux/reducers/home';
import { useGetFundingRateQuery } from 'redux/api/drf/infocore';
import {
  useCreateFavoriteAssetsMutation,
  useDeleteFavoriteAssetsMutation,
  useGetFavoriteAssetsQuery,
} from 'redux/api/drf/user';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import { Trans } from 'react-i18next';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isEmpty from 'lodash/isEmpty';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';
import isKoreanMarket from 'utils/isKoreanMarket';

import LightWeightKlineChart from 'components/charts/LightWeightKlineChart';
import MarketCodeSelector from 'components/MarketCodeSelector';
import MaterialReactTable from 'components/MaterialReactTable';

import { coinicons } from 'assets/exports';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function RealTimePremiumTable({
  t,
  language,
  loggedin,
  theme,
  timezone,
  matchLargeScreen,
}) {
  const dispatch = useDispatch();

  const favoriteAssetRef = useRef();

  const [assets, setAssets] = useState([]);

  const [expanded, setExpanded] = useState({});

  const [marketCodes, setMarketCodes] = useState(null);

  const localFavoriteAssets = useSelector(
    (state) =>
      state.home.favoriteAssets[
        `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`
      ]
  );
  const isTetherPriceView = useSelector(
    (state) => state.home.priceView === 'tether'
  );

  const isKimpExchange =
    isKoreanMarket(marketCodes?.targetMarketCode) &&
    !isKoreanMarket(marketCodes?.originMarketCode);

  const { data: realTimeData, isLoading } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval: '1T' },
    { skip: !marketCodes }
  );

  const realTimeDataList = useMemo(
    () => orderBy(Object.values(realTimeData ?? {}), 'atp24h', 'desc'),
    [realTimeData]
  );

  const { data: favoriteAssets } = useGetFavoriteAssetsQuery(marketCodes, {
    skip: !(loggedin && marketCodes),
  });

  const { data: targetFundingRate } = useGetFundingRateQuery(
    {
      baseAssets: realTimeDataList.map((o) => o.base_asset).join(),
      marketCode: marketCodes?.targetMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !marketCodes ||
        marketCodes?.targetMarketCode.includes('SPOT') ||
        realTimeDataList.length === 0,
    }
  );
  const { data: originFundingRate } = useGetFundingRateQuery(
    {
      baseAssets: realTimeDataList.map((o) => o.base_asset).join(),
      marketCode: marketCodes?.originMarketCode,
    },
    {
      pollingInterval: 1000 * 60,
      skip:
        !marketCodes ||
        marketCodes?.originMarketCode.includes('SPOT') ||
        realTimeDataList.length === 0,
    }
  );

  const [createFavoriteAsset, createFavoriteRes] =
    useCreateFavoriteAssetsMutation();
  const [deleteFavoriteAsset, deleteFavoriteRes] =
    useDeleteFavoriteAssetsMutation();

  const handleAddFavoriteAsset = useCallback(
    (baseAsset) => {
      const marketCodeKey = `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`;
      if (loggedin) createFavoriteAsset({ baseAsset, ...marketCodes });
      else dispatch(addLocalFavoriteAsset({ marketCodeKey, baseAsset }));
      favoriteAssetRef.current = baseAsset;
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

  const handleExpandRow = (newExpanded) => setExpanded(newExpanded);
  const debouncedHandleExpandRow = useCallback(
    debounce(handleExpandRow, 100, {
      leading: true,
      trailing: true,
    }),
    []
  );

  const renderNameHeader = ({ column }) => (
    <Stack
      direction="row"
      spacing={1}
      sx={{
        alignItems: 'center',
        color: column.getIsSorted()
          ? theme.palette.text.main
          : theme.palette.grey[theme.palette.mode === 'dark' ? '100' : '700'],
        fontSize: '0.725em',
      }}
    >
      <Box sx={{ width: '15px' }} />
      {column.columnDef.header}
    </Stack>
  );

  const renderNameCell = ({ renderedCellValue, row }) => (
    <Stack
      direction="row"
      spacing={1}
      sx={{ alignItems: 'center' }}
      onClick={() =>
        debouncedHandleExpandRow({ [row.id]: !row.getIsExpanded() })
      }
    >
      {row.original.icon ? (
        <img loading="lazy" width="15" src={row.original.icon} alt="" />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: 15 }} />
      )}
      <Box>{renderedCellValue}</Box>
    </Stack>
  );

  const renderExpandCell = ({ row }) => (
    <InsightsIcon
      onClick={() =>
        debouncedHandleExpandRow({
          [row.id]: !row.getIsExpanded(),
        })
      }
      color={row.getIsExpanded() ? 'info' : ''}
      fontSize="small"
    />
  );

  const renderStarCell = ({ cell, row }) => {
    const isFavorite = !isUndefined(cell.getValue());
    return (
      <Tooltip
        title={isFavorite ? t('Remove from favorites') : t('Add to favorites')}
      >
        <StarIcon
          color={isFavorite ? 'accent' : 'secondary'}
          onClick={(e) => {
            e.stopPropagation();
            if (isFavorite) handleRemoveFavoriteAsset(cell.getValue());
            else handleAddFavoriteAsset(row.original.name);
          }}
          sx={{
            '& :hover': { color: theme.palette.accent.main, opacity: 0.5 },
          }}
        />
      </Tooltip>
    );
  };

  const renderPriceCell = ({ cell, row: { original } }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <>
        {formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 0 : 4)}
        <Box
          component="small"
          sx={{
            color: original.scr > 0 ? 'success.main' : 'error.main',
            fontWeight: 700,
            ml: 1,
          }}
        >
          {original.scr > 0 ? '+' : ''}
          {original.scr?.toFixed(2)}%
        </Box>
        <Box>
          <Box component="small" sx={{ color: 'secondary.main' }}>
            {formatIntlNumber(
              original.converted_tp,
              original.converted_tp > 0 ? 0 : 4
            )}
          </Box>
        </Box>
      </>
    );

  const renderPremiumCell = ({ cell }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <>
        <Box component="span" sx={{ fontWeight: 700 }}>
          {formatIntlNumber(cell.getValue(), 2, 3)}
        </Box>{' '}
        <small>%</small>
      </>
    );

  const renderTetherCell = ({ cell, row: { original } }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <Box component="span" sx={{ fontWeight: 700 }}>
        {formatIntlNumber(original.dollar * (1 + cell.getValue() * 0.01), 1, 1)}
      </Box>
    );

  const renderSpreadCell = ({ cell }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <>
        {cell.getValue() > 0 ? '+' : ''}
        {formatIntlNumber(cell.getValue(), 2, 2)}{' '}
        <Box component="small" sx={{ color: 'secondary.main' }}>
          %p
        </Box>
      </>
    );

  const renderFundingRateHeader = ({ column }) => {
    const marketCode = MARKET_CODE_LIST.find(
      (o) =>
        o.value ===
        (column.id === 'targetFundingRate'
          ? marketCodes?.targetMarketCode
          : marketCodes?.originMarketCode)
    );
    if (!marketCode) return column.columnDef.header;
    return (
      <Tooltip title={marketCode.getLabel()} placement="bottom-end">
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          <SvgIcon sx={{ fontSize: 11 }}>
            <marketCode.icon />
          </SvgIcon>
          <Box component="span">{column.columnDef.header}</Box>
        </Stack>
      </Tooltip>
    );
  };

  const renderFundingRateCell = ({ cell, column, row }) => {
    if (isUndefined(cell.getValue())) return '...';
    const fundingRate =
      column.id === 'targetFundingRate'
        ? row.original.targetFR
        : row.original.originFR;
    const dateTimeNow = fundingRate?.datetime_now
      ? DateTime.fromISO(fundingRate.datetime_now)
      : null;
    const fundingTime = fundingRate?.funding_time
      ? DateTime.fromISO(fundingRate.funding_time)
      : null;
    const diff =
      dateTimeNow && fundingTime
        ? fundingTime
            .diff(dateTimeNow, ['hours', 'minutes', 'seconds'])
            .toObject()
        : null;
    return (
      <>
        {formatIntlNumber(cell.getValue(), 1, 3)} <small>%</small>
        {diff && (
          <Box sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
            <Trans>
              <strong>{{ hours: diff.hours }}</strong>
              <small>h</small> <strong>{{ minutes: diff.minutes }}</strong>
              <small>m</small>{' '}
              <strong>{{ seconds: diff.seconds.toFixed(0) }}</strong>
              <small>s</small> <strong>left</strong>
            </Trans>
          </Box>
        )}
      </>
    );
  };

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

  const tableData = useMemo(
    () =>
      isEmpty(realTimeDataList)
        ? assets.map((asset) => ({ name: asset }))
        : orderBy(
            realTimeDataList?.map((assetData) => {
              const asset = assetData.base_asset;
              let favoriteAssetId;
              if (loggedin) favoriteAssetId = favoriteAssets?.[asset];
              else {
                const index = localFavoriteAssets?.indexOf(asset);
                favoriteAssetId = index < 0 ? undefined : index;
              }

              const targetFR = targetFundingRate?.[asset];
              const originFR = originFundingRate?.[asset];
              return {
                name: asset,
                favoriteAssetId,
                icon: coinicons[`${asset}.png`]
                  ? require(`assets/icons/coinicon/${asset}.png`)
                  : null,
                spread: assetData
                  ? assetData.SL_close - assetData.LS_close
                  : '',
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
                ...assetData,
              };
            }) ?? [],
            (o) => !isUndefined(o.favoriteAssetId),
            'desc'
          ),
    [
      realTimeDataList,
      targetFundingRate,
      originFundingRate,
      favoriteAssets,
      localFavoriteAssets,
      loggedin,
    ]
  );

  const columns = useMemo(
    () => [
      {
        header: t('Favorite Asset'),
        accessorKey: 'favoriteAssetId',
        enableGlobalFilter: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { sx: { pl: 1 } },
        muiTableHeadCellProps: {
          sx: {
            pointerEvents: 'none',
            '& .MuiTableSortLabel-root': { display: 'none' },
          },
        },
        Cell: renderStarCell,
        Header: <span />,
      },
      {
        header: t('Name'),
        accessorKey: 'name',
        size: 50,
        muiTableBodyCellProps: { sx: { pl: { xs: 0, sm: 2 } } },
        muiTableHeadCellProps: { sx: { pl: { xs: 0, sm: 2 } } },
        Cell: renderNameCell,
        Header: renderNameHeader,
      },
      {
        header: t('Current Price'),
        accessorKey: 'tp',
        enableGlobalFilter: false,
        size: 60,
        muiTableBodyCellProps: { sx: { fontSize: '0.85rem' } },
        Cell: renderPriceCell,
      },
      {
        header: isKimpExchange
          ? [isTetherPriceView ? t('Enter Tether') : t('Enter KIMP')]
          : t('LS Premium'),
        accessorKey: 'LS_close',
        enableGlobalFilter: false,
        size: 50,
        Cell: isTetherPriceView ? renderTetherCell : renderPremiumCell,
      },
      {
        header: isKimpExchange
          ? [isTetherPriceView ? t('Exit Tether') : t('Exit KIMP')]
          : t('SL Premium'),
        accessorKey: 'SL_close',
        enableGlobalFilter: false,
        size: 50,
        Cell: isTetherPriceView ? renderTetherCell : renderPremiumCell,
      },
      {
        header: t('Spread'),
        accessorKey: 'spread',
        enableGlobalFilter: false,
        size: 40,
        muiTableBodyCellProps: { sx: { fontSize: '0.85rem' } },
        Cell: renderSpreadCell,
      },
      {
        header: t('Funding Rate'),
        accessorKey: 'targetFundingRate',
        enableGlobalFilter: false,
        size: 60,
        Header: renderFundingRateHeader,
        Cell: renderFundingRateCell,
      },
      {
        header: t('Funding Rate'),
        accessorKey: 'originFundingRate',
        enableGlobalFilter: false,
        size: 60,
        Header: renderFundingRateHeader,
        Cell: renderFundingRateCell,
      },
      {
        header: t('Volume (24h)'),
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        size: 40,
        Cell: ({ cell }) =>
          isUndefined(cell.getValue())
            ? '...'
            : formatShortNumber(cell.getValue(), 2),
      },
      {
        header: t('Expand'),
        accessorKey: 'expand',
        enableGlobalFilter: false,
        enableSorting: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { align: 'right', sx: { px: 0.5 } },
        muiTableHeadCellProps: { align: 'right' },
        Cell: renderExpandCell,
        Header: <span />,
      },
    ],
    [language, loggedin, marketCodes, isTetherPriceView, theme]
  );

  useEffect(() => {
    if (createFavoriteRes?.isSuccess) window.scrollTo(0, 0);
  }, [createFavoriteRes?.isSuccess]);

  useEffect(() => {
    if (realTimeDataList.length > 0)
      setAssets(realTimeDataList.map((item) => item.base_asset));
  }, [realTimeDataList]);

  useEffect(() => {
    setExpanded({});
  }, [marketCodes]);

  return (
    <Box>
      {!matchLargeScreen && (
        <MarketCodeSelector onChange={(value) => setMarketCodes(value)} />
      )}
      {isKoreanMarket(marketCodes?.targetMarketCode) &&
        !isKoreanMarket(marketCodes?.originMarketCode) && (
          <Box sx={{ mb: 1, mx: 1 }}>
            <ToggleButton
              size="small"
              selected={isTetherPriceView}
              value=""
              onChange={() =>
                dispatch(togglePriceView(isTetherPriceView ? 'kimp' : 'tether'))
              }
              sx={{ border: 0, px: 1, py: 0.5 }}
            >
              {t('View Tether conversion')}
            </ToggleButton>
          </Box>
        )}
      <MaterialReactTable
        defaultColumn={{ sortingFn: 'sortWithStarred' }}
        columns={columns}
        data={tableData}
        getRowId={(row) => row.name}
        initialState={{
          columnOrder: columns.map((col) => col.accessorKey),
          columnVisibility: {
            originFundingRate: !marketCodes?.originMarketCode.includes('SPOT'),
            targetFundingRate: !marketCodes?.targetMarketCode.includes('SPOT'),
            spread: matchLargeScreen,
            favoriteAssetId: matchLargeScreen,
            expand: matchLargeScreen,
            atp24h: matchLargeScreen,
            'mrt-row-expand': false,
            // 'mrt-row-select': false,
          },
          density: 'compact',
          showColumnFilters: false,
          // sorting: [{ id: 'atp24h', desc: true }],
        }}
        state={{
          expanded,
          isLoading: tableData?.length === 0,
          showProgressBars:
            isLoading ||
            createFavoriteRes.isLoading ||
            deleteFavoriteRes.isLoading,
        }}
        sortingFns={{ sortWithStarred }}
        renderDetailPanel={({ row }) => (
          <Box>
            {row.getIsExpanded() && (
              <LightWeightKlineChart
                baseAsset={row.original}
                marketCodes={marketCodes}
                isKimpExchange={isKimpExchange}
                isTetherPriceView={isTetherPriceView}
                onAddFavoriteAsset={handleAddFavoriteAsset}
                onRemoveFavoriteAsset={handleRemoveFavoriteAsset}
                timezone={timezone}
              />
            )}
          </Box>
        )}
        renderTopToolbarCustomActions={
          matchLargeScreen
            ? () => (
                <MarketCodeSelector
                  onChange={(value) => setMarketCodes(value)}
                />
              )
            : null
        }
        muiSearchTextFieldProps={{
          inputProps: {
            placeholder: t('Search {{size}} coins', {
              size: tableData?.length,
            }),
          },
        }}
        muiTableHeadCellProps={{ align: 'left' }}
        muiTableBodyCellProps={{ align: 'left' }}
        muiTableBodyRowProps={({ row }) => ({
          onClick: (e) => {
            if (!e.target.classList.contains('Mui-TableBodyCell-DetailPanel'))
              // debouncedHandleExpandRow({ [row.id]: !expanded[row.id] });
              setExpanded({ [row.id]: !expanded[row.id] });
          },
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded() ||
            !isUndefined(row.original.favoriteAssetId)
              ? {
                  bgcolor: alpha(
                    theme.palette[row.getIsExpanded() ? 'primary' : 'secondary']
                      .main,
                    0.075
                  ),
                }
              : {}),
          },
        })}
      />
    </Box>
  );
}
