import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, styled, useTheme } from '@mui/material/styles';

import {
  useGetAssetsQuery,
  useGetAverageFundingRateQuery,
  usePostAssetMutation,
} from 'redux/api/drf/infocore';

import { useTranslation } from 'react-i18next';

import { usePrevious } from '@uidotdev/usehooks';

import debounce from 'lodash/debounce';
import isEqual from 'lodash/isEqual';
import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import DropdownMenu from 'components/DropdownMenu';
import ReactTableUI from 'components/ReactTableUI';

import { EXCHANGE_LIST } from 'constants/lists';

import renderFundingRateCell from './renderFundingRateCell';
import renderIconCell from './renderIconCell';
import renderMarketCell from './renderMarketCell';

const DEFAULT_PAGE_SIZE = 50;

export default function AvgFundingRateTable() {
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [assets, setAssets] = useState([]);

  const [marketList, setMarketList] = useState([]);
  const [selectedMarket, setSelectedMarket] = useState();

  const [avgFundingRateParams, setAvgFundingRateParams] = useState({ n: 100 });
  const [n, setN] = useState(100);

  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });

  const handleParamsChange = (newValue) => setAvgFundingRateParams(newValue);
  const debouncedHandleParamsChange = useCallback(
    debounce(handleParamsChange, 1000, {
      leading: false,
      trailing: true,
    }),
    []
  );

  const { data, isLoading } = useGetAverageFundingRateQuery(
    avgFundingRateParams,
    { pollingInterval: 1000 * 60, skip: !avgFundingRateParams }
  );

  const { data: assetsData, isSuccess: isAssetsDataSuccess } =
    useGetAssetsQuery();
  const [postAsset] = usePostAssetMutation();

  useEffect(() => {
    setAssets(uniqBy(data, 'base_asset').map((item) => item.base_asset));
    const markets = [
      { label: t('All Markets'), value: 'ALL', icon: <CheckBoxIcon /> },
    ].concat(
      uniqBy(data, 'market_code').map((item) => {
        const icon = EXCHANGE_LIST.find(
          (exchange) => exchange.value === item.market_code.split('_')?.[0]
        )?.icon;
        return {
          label: item.market_code,
          value: item.market_code,
          icon: (
            <Box
              component="img"
              src={icon}
              alt={item.market_code}
              sx={{
                height: { xs: 16, md: 18 },
                width: { xs: 16, md: 18 },
              }}
            />
          ),
        };
      })
    );
    setMarketList(markets);
    if (!selectedMarket) setSelectedMarket(markets[0]);
  }, [data, selectedMarket, i18n.language]);

  useEffect(() => {
    debouncedHandleParamsChange({ n });
  }, [n]);

  const prevAssets = usePrevious(assets);
  const prevIsAssetsDataSuccess = usePrevious(isAssetsDataSuccess);
  useEffect(() => {
    if (!prevIsAssetsDataSuccess && isAssetsDataSuccess)
      if (!isEqual(prevAssets, assets))
        assets.forEach((asset) => {
          if (!assetsData?.[asset]) postAsset({ symbol: asset });
        });
  }, [assets, assetsData, isAssetsDataSuccess]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 20 : 40,
        header: <span />,
        cell: renderIconCell,
      },
      {
        accessorKey: 'symbol',
        size: isMobile ? 110 : 180,
        header: t('Symbol'),
        props: isMobile ? { sx: { fontSize: 10 } } : undefined,
      },
      {
        accessorKey: 'market',
        size: isMobile ? 120 : 250,
        header: t('Market'),
        cell: renderMarketCell,
      },
      {
        accessorKey: 'fundingRate',
        size: isMobile ? 80 : 180,
        header: `${t('Avg. of the Last {{n}} Funding Rates', {
          n: avgFundingRateParams?.n,
        })} (N)`,
        cell: renderFundingRateCell,
      },
    ],
    [avgFundingRateParams?.n, i18n.language, isMobile]
  );

  const tableData = useMemo(
    () =>
      orderBy(
        data?.filter(
          (item) =>
            selectedMarket?.value === 'ALL' ||
            item.market_code === selectedMarket?.value
        ),
        'funding_rate',
        'desc'
      ).map((item, idx) => ({
        rowId: `${item.base_asset}-${idx}`,
        name: item.base_asset,
        icon: assetsData?.[item.base_asset]?.icon,
        market: item.market_code,
        symbol: item.symbol,
        exchange: item.market_code.split('_')?.[0],
        fundingRate: item.funding_rate * 100,
        ...item,
      })) || [],
    [data, assetsData, selectedMarket?.value]
  );

  const rows = tableRef.current?.getRowModel().rows;

  return (
    <>
      <Stack direction="row" spacing={{ xs: 1, sm: 2 }} sx={{ mb: 2 }}>
        <DropdownMenu
          value={selectedMarket}
          options={marketList}
          onSelectItem={setSelectedMarket}
          buttonStyle={{
            justifyContent: 'flex-start',
            minWidth: isMobile ? 190 : 220,
          }}
        />
        <TextField
          id="n-value"
          label="N (1~100)"
          variant="outlined"
          type="number"
          value={`${n}`}
          onChange={(e) => {
            const value = parseInt(e.target.value, 10);
            if (value >= 1 && value <= 100) setN(value);
            else setN(value > 100 ? 100 : 1);
          }}
          inputProps={{ min: '1', max: '100' }}
          sx={{ minWidth: isMobile ? 100 : 120 }}
        />
      </Stack>
      <Box sx={{ boxShadow: 2 }}>
        <ReactTableUI
          ref={tableRef}
          columns={columns}
          data={tableData}
          options={{
            state: { pagination },
            onPaginationChange: setPagination,
          }}
          getCellProps={() => ({ sx: { height: 40 } })}
          showProgressBar={isLoading}
          isLoading={isLoading}
          // renderRow={(props) => <CustomRow {...props} />}
        />
        {rows?.length >= DEFAULT_PAGE_SIZE && (
          <Box sx={{ textAlign: 'center' }}>
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
            >
              {tableRef.current?.getCanNextPage()
                ? t('See more')
                : t('See less')}
            </Button>
          </Box>
        )}
      </Box>
    </>
  );
}
