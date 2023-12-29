import React, {
  useEffect,
  useState,
  useMemo,
  useRef,
  useCallback,
} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import RemoveIcon from '@mui/icons-material/Remove';
import StarIcon from '@mui/icons-material/Star';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';

import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import isNaN from 'lodash/isNaN';
import isUndefined from 'lodash/isUndefined';

import { useTranslation } from 'react-i18next';

import ChartDataTypeSelector from 'components/ChartDataTypeSelector';
import ExchangeWalletNetworks from 'components/ExchangeWalletNetworks';
import IntervalSelector from 'components/IntervalSelector';

import { MARKET_CODE_LIST } from 'constants/lists';

import LightWeightPremiumKlineChart from 'components/charts/LightWeightPremiumKlineChart';
import LightWeightFundingRateChart from 'components/charts/LightWeightFundingRateChart';
import LightWeightFundingRateDiffChart from 'components/charts/LightWeightFundingRateDiffChart';

function PremiumDataChartViewer({
  baseAssetData,
  marketCodes,
  defaultDChartDataType,
  defaultDisabledChartDataType,
  isKimpExchange,
  isTetherPriceView,
  onAddFavoriteAsset,
  onRemoveFavoriteAsset,
  queryKey,
  showFundingRate,
  showFundingRateDiff,
  showMarketCodes,
}) {
  const {
    name: baseAsset,
    favoriteAssetId,
    walletNetworks,
    walletStatus,
    tp,
  } = baseAssetData;

  const { loggedin, user } = useSelector((state) => state.auth);
  const isAuthorized = loggedin && user.role !== 'visitor';

  const theme = useTheme();

  const { t } = useTranslation();

  const wrapperRef = useRef();

  const premiumKlineChartRef = useRef();

  const [title, setTitle] = useState();

  const [klineInterval, setKlineInterval] = useState('1T');

  const [chartDataType, setChartDataType] = useState(defaultDChartDataType);
  const [disabledChartDataType, setDisabledChartDataType] = useState();

  const [subtrahend, setSubtrahend] = useState('origin');

  const { targetMarketCode, originMarketCode } = useMemo(
    () => ({
      targetMarketCode: MARKET_CODE_LIST.find(
        (o) => o.value === marketCodes?.targetMarketCode
      ) ?? {
        ...MARKET_CODE_LIST.find(
          (o) => o.exchange === marketCodes?.targetMarketCode?.split('_')[0]
        ),
        getLabel: () => marketCodes?.targetMarketCode,
        value: marketCodes?.targetMarketCode,
      },
      originMarketCode: MARKET_CODE_LIST.find(
        (o) => o.value === marketCodes?.originMarketCode
      ) ?? {
        ...MARKET_CODE_LIST.find(
          (o) => o.exchange === marketCodes?.originMarketCode?.split('_')[0]
        ),
        getLabel: () => marketCodes?.originMarketCode,
        value: marketCodes?.originMarketCode,
      },
    }),
    [marketCodes]
  );

  useEffect(() => {
    const value = marketCodes?.targetMarketCode;
    setTitle(`${baseAsset} / ${value?.split('/').pop()}`);
    if (marketCodes) setKlineInterval('1T');
  }, [marketCodes]);

  useEffect(() => {
    if (!chartDataType && !defaultDisabledChartDataType) {
      if (tp && !isNaN(tp)) setChartDataType('tp');
      else {
        setChartDataType('LS');
        setDisabledChartDataType({ tp: true });
      }
    }
  }, [tp, chartDataType, defaultDisabledChartDataType]);

  useEffect(() => {
    if (chartDataType === 'FRD') setSubtrahend('origin');
    else setSubtrahend();
  }, [chartDataType]);

  useEffect(() => {
    if (defaultDisabledChartDataType)
      setDisabledChartDataType(defaultDisabledChartDataType);
  }, [defaultDisabledChartDataType]);

  const renderMarketCodes = useCallback(() => {
    let leftMarket;
    let rightMarket;

    if (chartDataType !== 'FRD') {
      leftMarket = targetMarketCode;
      rightMarket = originMarketCode;
    } else {
      leftMarket =
        subtrahend === 'origin' ? targetMarketCode : originMarketCode;
      rightMarket =
        subtrahend === 'origin' ? originMarketCode : targetMarketCode;
    }

    return (
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="center"
        spacing={1}
        mt={2}
      >
        <Box
          component="img"
          src={leftMarket.icon}
          alt={leftMarket.getLabel()}
          sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
        />
        <Box>{leftMarket.getLabel()}</Box>
        {chartDataType === 'FRD' ? <RemoveIcon /> : <ArrowRightAltIcon />}
        <Box
          component="img"
          src={rightMarket.icon}
          alt={rightMarket.getLabel()}
          sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
        />
        <Box>{rightMarket.getLabel()}</Box>
        <Tooltip title={t('Swap')}>
          <IconButton
            onClick={() =>
              setSubtrahend((state) =>
                state === 'origin' ? 'target' : 'origin'
              )
            }
          >
            <SwapHorizIcon color="info" />
          </IconButton>
        </Tooltip>
      </Stack>
    );
  }, [targetMarketCode, originMarketCode, chartDataType, subtrahend]);

  const renderChart = useCallback(() => {
    switch (chartDataType) {
      case 'FR':
        return (
          <Grid container>
            {!targetMarketCode.value.includes('SPOT') && (
              <Grid
                item
                xs={12}
                md={originMarketCode.value.includes('SPOT') ? 12 : 6}
              >
                <Typography align="center">
                  {targetMarketCode.getLabel()}
                </Typography>
                <LightWeightFundingRateChart
                  baseAsset={baseAsset}
                  marketCode={targetMarketCode.value}
                />
              </Grid>
            )}
            {!originMarketCode.value.includes('SPOT') && (
              <Grid
                item
                xs={12}
                md={targetMarketCode.value.includes('SPOT') ? 12 : 6}
              >
                <Typography align="center">
                  {originMarketCode.getLabel()}
                </Typography>
                <LightWeightFundingRateChart
                  baseAsset={baseAsset}
                  marketCode={originMarketCode.value}
                />
              </Grid>
            )}
          </Grid>
        );
      case 'FRD':
        return (
          <>
            {renderMarketCodes()}
            <LightWeightFundingRateDiffChart
              baseAsset={baseAsset}
              marketCodes={{
                targetMarketCode: targetMarketCode.value,
                originMarketCode: originMarketCode.value,
              }}
              subtrahend={subtrahend}
            />
          </>
        );
      case 'SL':
      case 'LS':
      case 'tp':
        return (
          <>
            {showMarketCodes && renderMarketCodes()}
            <LightWeightPremiumKlineChart
              ref={premiumKlineChartRef}
              baseAsset={baseAsset}
              dataType={chartDataType}
              interval={klineInterval}
              marketCodes={marketCodes}
              queryKey={queryKey}
              isKimpExchange={isKimpExchange}
              isTetherPriceView={isTetherPriceView}
            />
          </>
        );
      default:
        return null;
    }
  }, [
    chartDataType,
    klineInterval,
    targetMarketCode,
    originMarketCode,
    marketCodes,
    baseAsset,
    subtrahend,
  ]);

  const isFavorite = !isUndefined(favoriteAssetId);

  return (
    <Card
      ref={wrapperRef}
      onClick={(e) => e.stopPropagation()}
      sx={{ borderRadius: 0 }}
    >
      <Box sx={{ bgcolor: 'background.paper' }}>
        {(targetMarketCode?.value.includes('SPOT') ||
          originMarketCode?.value.includes('SPOT')) && (
          <Box sx={{ p: 2 }}>
            <ExchangeWalletNetworks
              direction={
                targetMarketCode.value.includes('SPOT') &&
                originMarketCode.value.includes('SPOT') &&
                targetMarketCode.exchange !== originMarketCode.exchange
                  ? 'right'
                  : 'all'
              }
              targetMarketCode={targetMarketCode}
              originMarketCode={originMarketCode}
              walletNetworks={walletNetworks}
              walletStatus={walletStatus}
            />
            {targetMarketCode.value.includes('SPOT') &&
              originMarketCode.value.includes('SPOT') &&
              targetMarketCode.exchange !== originMarketCode.exchange && (
                <ExchangeWalletNetworks
                  direction="left"
                  targetMarketCode={targetMarketCode}
                  originMarketCode={originMarketCode}
                  walletNetworks={walletNetworks}
                  walletStatus={walletStatus}
                />
              )}
          </Box>
        )}
        <Grid container sx={{ p: 1, pt: 2 }}>
          <Grid
            item
            xs={6}
            sm={3}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {onAddFavoriteAsset && onRemoveFavoriteAsset && (
              <Tooltip
                title={
                  isFavorite
                    ? t('Remove from favorites')
                    : t('Add to favorites')
                }
              >
                <StarIcon
                  color={isFavorite ? 'accent' : 'secondary'}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (isFavorite) onRemoveFavoriteAsset(favoriteAssetId);
                    else onAddFavoriteAsset(baseAsset);
                  }}
                  sx={{
                    '& :hover': {
                      color: theme.palette.accent.main,
                      opacity: 0.5,
                    },
                  }}
                />
              </Tooltip>
            )}
            <Typography sx={{ fontWeight: 700, ml: 2 }}>{title}</Typography>
          </Grid>
          <Grid
            item
            xs={3}
            sm={6}
            sx={{ display: 'flex', justifyContent: 'center' }}
          >
            {chartDataType !== 'FR' && chartDataType !== 'FRD' && (
              <IntervalSelector
                defaultValue={klineInterval}
                disabled={!isAuthorized}
                onChange={(value) => {
                  premiumKlineChartRef?.current?.reinitialize();
                  setKlineInterval(value);
                }}
              />
            )}
          </Grid>
          <Grid
            item
            xs={3}
            sm={3}
            sx={{ display: 'flex', justifyContent: 'end' }}
          >
            {chartDataType && (
              <ChartDataTypeSelector
                defaultValue={chartDataType}
                disabled={disabledChartDataType}
                isKimpExchange={isKimpExchange}
                isTetherPriceView={isTetherPriceView}
                showFundingRate={
                  showFundingRate &&
                  (!targetMarketCode.value.includes('SPOT') ||
                    !originMarketCode.value.includes('SPOT'))
                }
                showFundingRateDiff={
                  showFundingRateDiff &&
                  !targetMarketCode.value.includes('SPOT') &&
                  !originMarketCode.value.includes('SPOT')
                }
                onChange={(value) => setChartDataType(value)}
              />
            )}
          </Grid>
        </Grid>
        {renderChart()}
      </Box>
    </Card>
  );
}

export default PremiumDataChartViewer;
