import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import Tooltip from '@mui/material/Tooltip';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';

import useMediaQuery from '@mui/material/useMediaQuery';

import Countdown from 'react-countdown';

import { useDispatch, useSelector } from 'react-redux';
import {
  addLocalFavoriteAsset,
  removeLocalFavoriteAsset,
  togglePriceView,
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

import { Trans } from 'react-i18next';

import { DateTime } from 'luxon';

import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import isFunction from 'lodash/isFunction';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';

import { useVisibilityChange } from '@uidotdev/usehooks';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';
import isKoreanMarket from 'utils/isKoreanMarket';

import LightWeightKlineChart from 'components/charts/LightWeightKlineChart';
import MarketCodeMenu from 'components/MarketCodeMenu';
import MaterialReactTable from 'components/MaterialReactTable';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function RealTimePremiumTable({
  t,
  language,
  loggedin,
  theme,
  timezone,
}) {
  const isFocused = useVisibilityChange();

  const dispatch = useDispatch();

  const favoriteAssetRef = useRef();

  const [assets, setAssets] = useState([]);

  const [columnVisibility, setColumnVisibility] = useState({});
  const [expanded, setExpanded] = useState({});

  const [marketCodes, setMarketCodes] = useState(null);

  const [ready, setReady] = useState(false);

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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

  const {
    data: realTimeData,
    isLoading,
    isSuccess,
  } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval: '1T' },
    { skip: !marketCodes || !isFocused }
  );

  const realTimeDataList = useMemo(
    () => orderBy(Object.values(realTimeData ?? {}), 'atp24h', 'desc'),
    [realTimeData]
  );

  const { data: assetsData } = useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  const { data: favoriteAssets } = useGetFavoriteAssetsQuery(
    { marketCodes: Object.values(marketCodes ?? {}).join() },
    {
      skip: !(loggedin && marketCodes),
    }
  );

  const { data: targetFundingRate } = useGetFundingRateQuery(
    {
      baseAsset: realTimeDataList.map((o) => o.base_asset).join(),
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
      baseAsset: realTimeDataList.map((o) => o.base_asset).join(),
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
    useCreateFavoriteAssetMutation();
  const [deleteFavoriteAsset, deleteFavoriteRes] =
    useDeleteFavoriteAssetMutation();

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

  const renderNameCell = ({ cell, renderedCellValue, row }) => {
    const isFavorite = !isUndefined(row.original.favoriteAssetId);
    return (
      <>
        <Stack
          direction="row"
          spacing={{ xs: 0.5, sm: 1 }}
          sx={{ alignItems: 'center' }}
        >
          {row.original.icon ? (
            <img
              loading="lazy"
              width={isMobile ? '10' : '15'}
              src={row.original.icon}
              alt={row.original.name}
            />
          ) : (
            <BlockIcon color="secondary" sx={{ fontSize: 12 }} />
          )}

          <Box>{renderedCellValue}</Box>
        </Stack>
        {isMobile && (
          <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
            <StarIcon
              color={isFavorite ? 'accent' : 'secondary'}
              onClick={(e) => {
                e.stopPropagation();
                if (isFavorite)
                  handleRemoveFavoriteAsset(row.original.favoriteAssetId);
                else handleAddFavoriteAsset(cell.getValue());
              }}
              sx={{
                fontSize: 13,
                '& :hover': { color: theme.palette.accent.main, opacity: 0.5 },
              }}
            />
            <InsightsIcon
              color={row.getIsExpanded() ? 'info' : 'secondary'}
              sx={{ fontSize: 12 }}
            />
          </Stack>
        )}
      </>
    );
  };

  const renderChartExpandCell = ({ row }) => (
    <InsightsIcon
      color={row.getIsExpanded() ? 'info' : ''}
      sx={{ fontSize: { md: '0.65rem', lg: 14 } }}
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
            fontSize: { sm: '0.75rem', md: 16, lg: 20 },
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
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={{ xs: 0, sm: 0.5 }}
          sx={{ alignItems: 'flex-start' }}
        >
          <Box>{formatIntlNumber(cell.getValue(), 1)}</Box>
          <Box
            component="small"
            sx={{
              color: original.scr > 0 ? 'success.main' : 'error.main',
              fontWeight: 700,
            }}
          >
            {original.scr > 0 ? '+' : ''}
            {original.scr?.toFixed(2)}%
          </Box>
        </Stack>
        <Box>
          <Box component="small" sx={{ color: 'secondary.main' }}>
            {formatIntlNumber(original.converted_tp, 2)}
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
          {formatIntlNumber(cell.getValue(), 3)}
        </Box>{' '}
        <small>%</small>
      </>
    );

  const renderTetherCell = ({ cell, row: { original } }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <Box component="span" sx={{ fontWeight: 700 }}>
        {formatIntlNumber(original.dollar * (1 + cell.getValue() * 0.01), 2)}
      </Box>
    );

  const renderSpreadCell = ({ cell }) =>
    isUndefined(cell.getValue()) ? (
      '...'
    ) : (
      <>
        {cell.getValue() > 0 ? '+' : ''}
        {formatIntlNumber(cell.getValue(), 2, 1)}{' '}
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
    if (!marketCode) return t('Funding Rate');
    return (
      <Tooltip title={marketCode.getLabel()} placement="bottom-end">
        <Stack direction="row" spacing={0.5}>
          <Box component="span">{t('Funding Rate')}</Box>
          <Box
            component="img"
            src={marketCode.icon}
            alt={marketCode.label}
            sx={{
              height: { xs: 8, sm: 10, md: 12 },
              width: { xs: 8, sm: 10, md: 12 },
            }}
          />
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
    const value = cell.getValue();
    return (
      <>
        <Box
          component="span"
          sx={{ color: value < 0 ? 'error.main' : undefined }}
        >
          {formatIntlNumber(value, 3, 1)} <small>%</small>
        </Box>
        {diff &&
          (!isMobile ? (
            <Box sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
              <Countdown
                date={DateTime.fromISO(fundingRate.funding_time).toJSDate()}
                renderer={({ hours, minutes, seconds }) => (
                  <Trans>
                    <small>
                      {{ hours }}h {{ minutes: `${minutes}`.padStart(2, '0') }}m{' '}
                      {{ seconds: `${seconds}`.padStart(2, '0') }}s left
                    </small>
                  </Trans>
                )}
              />
            </Box>
          ) : (
            <Box sx={{ color: 'secondary.main', fontStyle: 'italic' }}>
              <Countdown
                date={DateTime.fromISO(fundingRate.funding_time).toJSDate()}
                renderer={({ hours, minutes, seconds }) =>
                  `${hours.toString().padStart(2, '0')}:${minutes
                    .toString()
                    .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
                }
              />
            </Box>
          ))}
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
        ? orderBy(
            assets.map((asset) => {
              let favoriteAssetId;
              if (loggedin) favoriteAssetId = favoriteAssets?.[asset];
              else {
                const index = localFavoriteAssets?.indexOf(asset);
                favoriteAssetId = index < 0 ? undefined : index;
              }
              return {
                name: asset,
                favoriteAssetId,
                icon: assetsData?.[asset]?.icon,
              };
            }),
            (o) => !isUndefined(o.favoriteAssetId),
            'desc'
          )
        : orderBy(
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

  const columns = useMemo(
    () => [
      {
        header: t('Favorite Asset'),
        accessorKey: 'favoriteAssetId',
        columnDefType: 'display',
        size: 18,
        maxSize: 18,
        muiTableBodyCellProps: { sx: { pl: 1 } },
        muiTableHeadCellProps: { sx: { pointerEvents: 'none' } },
        Cell: renderStarCell,
        Header: <span />,
      },
      {
        header: t('Name'),
        accessorKey: 'name',
        enableHiding: false,
        size: isMobile ? 45 : 50,
        Cell: renderNameCell,
      },
      {
        header: t('Current Price'),
        accessorKey: 'tp',
        enableGlobalFilter: false,
        enableHiding: false,
        size: isMobile ? 45 : 65,
        Cell: renderPriceCell,
      },
      {
        header: isKimpExchange
          ? [isTetherPriceView ? t('Enter Tether') : t('Enter KIMP')]
          : t('LS Premium'),
        accessorKey: 'LS_close',
        enableGlobalFilter: false,
        enableHiding: false,
        size: isMobile ? 30 : 50,
        Cell: isTetherPriceView ? renderTetherCell : renderPremiumCell,
      },
      {
        header: isKimpExchange
          ? [isTetherPriceView ? t('Exit Tether') : t('Exit KIMP')]
          : t('SL Premium'),
        accessorKey: 'SL_close',
        enableGlobalFilter: false,
        enableHiding: false,
        size: isMobile ? 30 : 50,
        Cell: isTetherPriceView ? renderTetherCell : renderPremiumCell,
      },
      {
        header: t('Spread'),
        accessorKey: 'spread',
        enableGlobalFilter: false,
        size: 50,
        Cell: renderSpreadCell,
      },
      ...(!marketCodes?.targetMarketCode.includes('SPOT')
        ? [
            {
              header: t('Funding Rate ({{marketCode}})', {
                marketCode: marketCodes?.targetMarketCode,
              }),
              accessorKey: 'targetFundingRate',
              enableGlobalFilter: false,
              size: isMobile ? 30 : 60,
              Header: renderFundingRateHeader,
              Cell: renderFundingRateCell,
            },
          ]
        : []),
      ...(!marketCodes?.originMarketCode.includes('SPOT')
        ? [
            {
              header: t('Funding Rate ({{marketCode}})', {
                marketCode: marketCodes?.originMarketCode,
              }),
              accessorKey: 'originFundingRate',
              enableGlobalFilter: false,
              size: isMobile ? 30 : 60,
              Header: renderFundingRateHeader,
              Cell: renderFundingRateCell,
            },
          ]
        : []),
      {
        header: t('Volume (24h)'),
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        enableHiding: false,
        size: 45,
        Cell: ({ cell }) =>
          isUndefined(cell.getValue())
            ? '...'
            : formatShortNumber(cell.getValue(), 2),
      },
      {
        header: t('View Chart'),
        accessorKey: 'chart',
        columnDefType: 'display',
        size: 11,
        maxSize: 11,
        muiTableBodyCellProps: { align: 'right', sx: { pl: 0, pr: 0.25 } },
        muiTableHeadCellProps: { align: 'right' },
        Cell: renderChartExpandCell,
        Header: <span />,
      },
    ],
    [language, loggedin, marketCodes, isTetherPriceView, theme, isMobile]
  );

  useEffect(() => {
    if (createFavoriteRes?.isSuccess) window.scrollTo(0, 0);
  }, [createFavoriteRes?.isSuccess]);

  useEffect(() => {
    let timeout;
    if (isSuccess) {
      if (realTimeDataList.length > 0) {
        if (timeout) clearTimeout(timeout);
        const realTimeAssets = realTimeDataList.map((item) => item.base_asset);
        if (!isEqual(assets, realTimeAssets)) {
          setAssets(realTimeAssets);
          setReady(true);
        }
      } else {
        setReady(false);
        timeout = setTimeout(() => {
          setAssets([]);
          setReady(true);
        }, 5000);
      }
    }
  }, [isSuccess, realTimeDataList]);

  useEffect(() => {
    setExpanded({});
  }, [marketCodes]);

  useEffect(() => {
    setColumnVisibility({
      chart: !isMobile,
      spread: !isMobile,
      favoriteAssetId: !isMobile,
      'mrt-row-expand': false,
    });
  }, [isMobile]);

  useEffect(() => {
    assets.forEach((asset) => {
      if (!assetsData?.[asset]?.icon) postAsset({ symbol: asset });
    });
  }, [assets, assetsData]);

  const renderTetherToggle = () =>
    marketCodes ? (
      <FormGroup
        row
        sx={{
          pointerEvents:
            isKoreanMarket(marketCodes?.targetMarketCode) &&
            !isKoreanMarket(marketCodes?.originMarketCode)
              ? undefined
              : 'none',
          width: { xs: 200, sm: 'auto' },
          mb: { xs: 0.5, sm: 2, md: 1, lg: 0 },
        }}
        className={`animate__animated animate__${
          isKoreanMarket(marketCodes?.targetMarketCode) &&
          !isKoreanMarket(marketCodes?.originMarketCode)
            ? 'zoomIn'
            : 'zoomOut'
        }`}
      >
        <FormControlLabel
          checked={isTetherPriceView}
          control={
            <Switch
              color="info"
              size={isMobile ? 'small' : 'medium'}
              checked={isTetherPriceView}
              onChange={(e) =>
                dispatch(togglePriceView(e.target.checked ? 'tether' : 'gimp'))
              }
            />
          }
          label={t('View Tether conversion')}
          labelPlacement="start"
          slotProps={{
            typography: {
              sx: {
                color: isTetherPriceView ? 'info.main' : 'inherit',
                fontSize: { xs: '0.65rem', sm: '0.8rem' },
                fontWeight: 700,
              },
            },
          }}
          sx={{ ml: { xs: 0.5, sm: 1 } }}
        />
      </FormGroup>
    ) : null;

  return (
    <Box>
      <MaterialReactTable
        defaultColumn={{ sortingFn: 'sortWithStarred' }}
        columns={columns}
        data={tableData}
        getRowId={(row) => row.name}
        initialState={{
          columnVisibility,
          columnOrder: columns.map((col) => col.accessorKey),
          density: 'compact',
          showColumnFilters: false,
        }}
        state={{
          columnVisibility,
          expanded,
          isLoading: !ready,
          showProgressBars:
            isLoading ||
            createFavoriteRes.isLoading ||
            deleteFavoriteRes.isLoading,
        }}
        sortingFns={{ sortWithStarred }}
        onColumnVisibilityChange={(getNewColumnVisibility) => {
          if (getNewColumnVisibility)
            if (isFunction(getNewColumnVisibility))
              setColumnVisibility((state) => ({
                ...state,
                ...getNewColumnVisibility(),
                chart: !isMobile,
                favoriteAssetId: !isMobile,
              }));
            else
              setColumnVisibility((state) => ({
                ...state,
                ...getNewColumnVisibility,
                chart: !isMobile,
                favoriteAssetId: !isMobile,
              }));
        }}
        renderDetailPanel={({ row }) => (
          <Box>
            {expanded[row.id] && (
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
        renderTopToolbarCustomActions={() => (
          <Stack direction="column" spacing={0.25}>
            {renderTetherToggle()}
            <MarketCodeMenu onChange={(value) => setMarketCodes(value)} />
          </Stack>
        )}
        muiTableDetailPanelProps={{ sx: { p: 0 } }}
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
              setExpanded({
                [row.id]: !expanded[row.id],
              });
          },
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { bgcolor: theme.palette.background.default }
              : {}),
          },
        })}
      />
    </Box>
  );
}
