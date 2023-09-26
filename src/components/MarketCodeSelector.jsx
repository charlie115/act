import React, { useEffect, useState } from 'react';

import Stack from '@mui/material/Stack';
import SvgIcon from '@mui/material/SvgIcon';

import PushPinIcon from '@mui/icons-material/PushPin';
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import { useTranslation } from 'react-i18next';

import AnimatedClick from 'components/AnimatedClick';
import DropdownMenu from 'components/DropdownMenu';

import { MARKET_CODE_LIST } from 'constants/lists';

function MarketCodeSelector({ onChange }) {
  const { i18n, t } = useTranslation();

  const [marketCodeList, setMarketCodeList] = useState([]);
  const [targetMarketCode, setTargetMarketCode] = useState(0);
  const [originMarketCode, setOriginMarketCode] = useState(5);

  const [targetAnchorEl, setTargetAnchorEl] = useState(null);
  const [originAnchorEl, setOriginAnchorEl] = useState(null);

  useEffect(() => {
    if (onChange && marketCodeList.length > 0)
      onChange({
        targetMarketCode: marketCodeList[targetMarketCode].value,
        originMarketCode: marketCodeList[originMarketCode].value,
      });
  }, [targetMarketCode, originMarketCode, marketCodeList]);

  useEffect(() => {
    setMarketCodeList(
      MARKET_CODE_LIST.map((market, index) => ({
        ...market,
        index,
        label: market.getLabel(),
        icon: (
          <SvgIcon>
            <market.icon />
          </SvgIcon>
        ),
        // secondaryIcon: (
        //   <PushPinIcon
        //     onClick={(e) => {
        //       e.stopPropagation();
        //     }}
        //   />
        // ),
      }))
    );
  }, [i18n.language]);

  return (
    <Stack
      direction="row"
      spacing={2}
      sx={{
        alignItems: 'center',
        flex: 0.9,
        mb: { xs: 3, md: 0 },
      }}
    >
      <DropdownMenu
        options={marketCodeList}
        value={marketCodeList[targetMarketCode]}
        tooltipTitle={t('Base Market Code')}
        onSelectItem={(item) => {
          setTargetMarketCode(item.index);
          if (item.index === originMarketCode)
            setOriginMarketCode(
              item.index === marketCodeList.length - 1 ? 0 : item.index + 1
            );
        }}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
      <AnimatedClick
        animation="flipOutY"
        onClick={() => {
          setTargetAnchorEl(null);
          setOriginAnchorEl(null);
          setTargetMarketCode(originMarketCode);
          setOriginMarketCode(targetMarketCode);
        }}
        containerStyle={{
          zIndex: targetAnchorEl || originAnchorEl ? 1500 : null,
        }}
      >
        <SyncAltIcon
          color="secondary"
          fontSize="small"
          sx={{ cursor: 'pointer' }}
        />
      </AnimatedClick>
      <DropdownMenu
        options={marketCodeList}
        value={marketCodeList[originMarketCode]}
        disabledValue={marketCodeList[targetMarketCode]}
        tooltipTitle={t('Origin Market Code')}
        onSelectItem={(item) => setOriginMarketCode(item.index)}
        buttonStyle={{ justifyContent: 'start', px: 2 }}
        containerStyle={{ alignSelf: 'stretch', flex: 1.5 }}
      />
    </Stack>
  );
}

export default React.memo(MarketCodeSelector);
