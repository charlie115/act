import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import {
  addLocalFavoriteAsset,
  removeLocalFavoriteAsset,
  togglePriceView,
} from 'redux/reducers/home';
import {
  useCreateFavoriteAssetsMutation,
  useDeleteFavoriteAssetsMutation,
  useGetFavoriteAssetsQuery,
} from 'redux/api/drf/user';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

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

export default function RealTimeCoinsTable() {
  const dispatch = useDispatch();

  const favoriteAssetRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const { loggedin } = useSelector((state) => state.auth);

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
  const { assets } = useSelector((state) => state.websocket);

  const isKimpExchange =
    isKoreanMarket(marketCodes?.targetMarketCode) &&
    !isKoreanMarket(marketCodes?.originMarketCode);

  // const isKimpPriceView = priceView === 'kimp';
  // const isKimp =
  //   isKoreanMarket(marketCodes?.targetMarketCode) &&
  //   !isKoreanMarket(marketCodes?.originMarketCode) &&
  //   priceView === 'kimp';

  // const { data: realTimeData, isLoading } = useGetWsCoinsQuery(
  //   {
  //     ...marketCodes,
  //     period: REALTIME_INTERVAL_KEY,
  //     isTableData: true,
  //   },
  //   { skip: !marketCodes }
  // );

  const { data: realTimeData, isLoading } = useGetRealTimeKlineQuery(
    {
      ...marketCodes,
      interval: '1T',
      isTableData: true,
    },
    { skip: !marketCodes }
  );
  console.log('isLoading: ', isLoading);

  const { data: favoriteAssets } = useGetFavoriteAssetsQuery(marketCodes, {
    skip: !(loggedin && marketCodes),
  });

  const [createFavoriteAsset, createFavoriteRes] =
    useCreateFavoriteAssetsMutation();
  const [deleteFavoriteAsset, deleteFavoriteRes] =
    useDeleteFavoriteAssetsMutation();

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

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
      <Box component="span" sx={{ fontSize: 16 }}>
        {renderedCellValue}
      </Box>
    </Stack>
  );

  const renderNameHeader = ({ column }) => (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      <Box sx={{ width: '15px' }} />
      {column.columnDef.header}
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

  const renderPriceCell = ({ cell, row: { original } }) => (
    <>
      {formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 0 : 4)}
      <Box
        component="small"
        sx={{
          color: original.scr > 0 ? 'success.main' : 'error.main',
          display: 'inline',
          fontSize: 12,
          fontWeight: 700,
          ml: 1,
        }}
      >
        {original.scr > 0 ? '+' : ''}
        {original.scr?.toFixed(2)}%
      </Box>
      <Typography sx={{ color: 'secondary.main' }}>
        {formatIntlNumber(
          original.converted_tp,
          original.converted_tp > 0 ? 0 : 4
        )}
      </Typography>
    </>
  );

  const renderPremiumCell = ({ cell }) => (
    <>
      <Typography sx={{ display: 'inline', fontSize: 17, fontWeight: 700 }}>
        {formatIntlNumber(cell.getValue(), 2, 3)}
      </Typography>{' '}
      <small>%</small>
    </>
  );

  const renderTetherCell = ({ cell, row: { original } }) => (
    <Typography sx={{ display: 'inline', fontSize: 17, fontWeight: 700 }}>
      {formatIntlNumber(original.dollar * (1 + cell.getValue() * 0.01), 1, 1)}
    </Typography>
  );

  const renderSpreadCell = ({ cell }) => (
    <>
      {/* TODO: Check if color is ok  */}
      {/* <Box
        sx={
          {
            // color: `${cell.getValue() < 0 ? 'error' : 'success'}.main`,
            // fontWeight: 700,
          }
        }
      > */}
      {cell.getValue() > 0 ? '+' : ''}
      {formatIntlNumber(cell.getValue(), 2, 2)}{' '}
      <Typography
        sx={{ color: 'secondary.main', display: 'inline', fontSize: 12 }}
      >
        %p
      </Typography>
      {/* </Box> */}
    </>
  );

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
      isEmpty(realTimeData)
        ? assets.map((asset) => ({ name: asset }))
        : orderBy(
            Object.values(realTimeData ?? {})?.map((assetData) => {
              const asset = assetData.base_asset;
              let favoriteAssetId;
              if (loggedin) favoriteAssetId = favoriteAssets?.[asset];
              else {
                const index = localFavoriteAssets?.indexOf(asset);
                favoriteAssetId = index < 0 ? undefined : index;
              }
              return {
                name: asset,
                favoriteAssetId,
                icon: coinicons[`${asset}.png`]
                  ? require(`assets/icons/coinicon/${asset}.png`)
                  : null,
                spread: assetData
                  ? assetData.SL_close - assetData.LS_close
                  : '',
                ...assetData,
              };
            }) ?? [],
            (o) => !isUndefined(o.favoriteAssetId),
            'desc'
          ),
    [realTimeData, favoriteAssets, localFavoriteAssets, loggedin]
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
        size: 50,
        Cell: renderPriceCell,
      },
      // {
      //   header: isMarketKorean(marketCodes?.targetMarketCode)
      //     ? t('KIMP')
      //     : t('Premium'),
      //   accessorKey: 'tp_close',
      //   enableGlobalFilter: false,
      //   size: 50,
      //   Cell: renderPremiumCell,
      // },
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
        size: 50,
        Cell: renderSpreadCell,
      },
      // {
      //   header: t('52-Week High'),
      //   accessorKey: 'weekhigh',
      //   enableGlobalFilter: false,
      //   size: 50,
      // },
      // {
      //   header: t('52-Week Low'),
      //   accessorKey: 'weeklow',
      //   enableGlobalFilter: false,
      //   size: 50,
      //   Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      // },
      {
        header: t('Volume (24h)'),
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatShortNumber(cell.getValue(), 2),
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
    [i18n.language, loggedin, marketCodes, isTetherPriceView]
  );

  useEffect(() => {
    if (createFavoriteRes?.isSuccess) window.scrollTo(0, 0);
  }, [createFavoriteRes?.isSuccess]);

  // TODO: Check if this is needed
  // useEffect(() => {
  //   setExpanded({});
  // }, [marketCodes]);

  return (
    <Box>
      {!matchLargeScreen && (
        <MarketCodeSelector onChange={(value) => setMarketCodes(value)} />
      )}
      {isKoreanMarket(marketCodes?.targetMarketCode) &&
        !isKoreanMarket(marketCodes?.originMarketCode) && (
          <Box sx={{ mx: 1 }}>
            <ToggleButton
              // color={isKimpPriceView ? 'secondary' : 'info'}
              // color="info"
              size="small"
              selected={isTetherPriceView}
              value=""
              onChange={() =>
                dispatch(togglePriceView(isTetherPriceView ? 'kimp' : 'tether'))
              }
              sx={{ border: 0, px: 1, py: 0.5 }}
            >
              {t('View Tether conversion')}
              {/* {isKimpPriceView ? t('View Tether conversion') : t('View KIMP')} */}
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
            // isStarred: matchLargeScreen,
            // weekhigh: matchLargeScreen,
            // weeklow: matchLargeScreen,
            expand: matchLargeScreen,
            'mrt-row-expand': false,
            // 'mrt-row-select': false,
          },
          density: 'compact',
          showColumnFilters: false,
          sorting: [{ id: 'atp24h', desc: true }],
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
            <Collapse unmountOnExit in={row.getIsExpanded()}>
              <LightWeightKlineChart
                baseAsset={row.original}
                marketCodes={marketCodes}
                isKimpExchange={isKimpExchange}
                isTetherPriceView={isTetherPriceView}
                onAddFavoriteAsset={handleAddFavoriteAsset}
                onRemoveFavoriteAsset={handleRemoveFavoriteAsset}
              />
            </Collapse>
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
        muiTableBodyCellProps={{
          align: 'left',
          sx: { fontSize: 16 },
        }}
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
