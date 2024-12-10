import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';

import i18n from 'configs/i18n';

export const DATE_FORMAT_API_QUERY = "yyyy-MM-dd'T'HH:mm:ss";

export const DATE_FORMAT_BY_UNIT = {
  minutes: 'HH:mm',
  hours: 'HH:mm',
};

export const DEPOSIT_TYPE = {
  COMMISSION: {
    getLabel: () => i18n.t('Commission'),
    color: 'success.main',
  },
  COUPON: {
    getLabel: () => i18n.t('Coupon'),
    color: 'success.main',
  },
  DEPOSIT: {
    getLabel: () => i18n.t('Deposit'),
    color: 'success.main',
  },
  FEE: {
    getLabel: () => i18n.t('Fee'),
    color: 'error.main',
  },
  TRANSFER: {
    getLabel: () => i18n.t('Transfer'),
    color: 'error.main',
  },
  WITHDRAW: {
    getLabel: () => i18n.t('Withdrawal'),
    color: 'error.main',
  },
};

export const POST_REACTION_TYPE = {
  DISLIKE: {
    value: 'DISLIKE',
    icon: ThumbDownIcon,
  },
  LIKE: {
    value: 'LIKE',
    icon: ThumbUpIcon,
  },
};

export const REGEX = {
  chatMention: /\B@([\w_]+)/,
  // eslint-disable-next-line no-control-regex
  ctrlCharactersRegex: /[\u0000-\u001F\u007F-\u009F\u2000-\u200D\uFEFF]/gim,
  spotMarketSuffix: /(_SPOT\/)([A-Z]+)/,
  koreanCharacters:
    /[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]$/i,
  usernameFirstCharacter:
    /^[A-Za-z]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/i,
  usernameFull:
    /^([A-Za-z0-9_.]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff])+$/i,
};

export const RIGHT_SIDEBAR_WIDTH = 360;

export const USER_ROLE = {
  admin: 'ADMIN',
  internal: 'INTERNAL',
  user: 'USER',
  visitor: 'VISITOR',
};
