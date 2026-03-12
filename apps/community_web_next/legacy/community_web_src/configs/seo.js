import i18n from 'configs/i18n';

// Get current site URL from environment variables
const getSiteUrl = () => process.env.REACT_APP_SITE_URL || window.location.origin;

// Language to locale mapping for Open Graph
const getLocale = (lang) => {
  const localeMap = {
    en: 'en_US',
    ko: 'ko_KR',
    zh: 'zh_CN',
  };
  return localeMap[lang] || 'en_US';
};

// Default SEO configuration
export const defaultSEO = {
  siteName: 'ArbiCrypto',
  titleTemplate: '%s | ArbiCrypto',
  separator: '|',
  defaultTitle: 'ArbiCrypto - 암호화폐 차익거래 플랫폼',
  defaultDescription: {
    ko: '여러 거래소의 실시간 암호화폐 차익거래 기회를 제공합니다. 펀딩 비율 추적, 가격 차이 분석, 고급 봇으로 거래 전략을 자동화하세요.',
    en: 'Real-time cryptocurrency arbitrage opportunities across multiple exchanges. Track funding rates, analyze price differences, and automate your trading strategy with our advanced bot.',
    zh: '跨多个交易所的实时加密货币套利机会。跟踪资金费率，分析价差，使用我们的高级机器人自动化您的交易策略。',
  },
  defaultKeywords: [
    '암호화폐',
    '차익거래',
    '펀딩',
    '트레이딩',
    '자동매매',
    '비트코인',
    '이더리움',
    '거래소',
    '봇',
    'crypto',
    'cryptocurrency',
    'arbitrage',
    'trading',
    'funding rate',
    'bitcoin',
    'ethereum',
    'exchange',
    'bot',
    'automated trading',
  ],
  defaultImage: '/social/og-default.png',
  twitterHandle: '@arbicrypto', // Update with actual Twitter handle if exists
};

// Page-specific SEO configurations
export const pageSEO = {
  '/': {
    title: {
      en: 'Home - Cryptocurrency Arbitrage Trading',
      ko: '홈 - 암호화폐 차익거래',
      zh: '首页 - 加密货币套利交易',
    },
    description: {
      en: 'Real-time cryptocurrency arbitrage opportunities. Monitor funding rates, price differences, and trading volumes across major exchanges like Binance, Bybit, OKX, and more.',
      ko: '실시간 암호화폐 차익거래 기회. 바이낸스, 바이비트, OKX 등 주요 거래소의 펀딩 비율, 가격 차이, 거래량을 모니터링하세요.',
      zh: '实时加密货币套利机会。监控币安、Bybit、OKX等主要交易所的资金费率、价差和交易量。',
    },
    keywords: [
      'crypto arbitrage',
      'funding rate',
      'premium table',
      'binance',
      'bybit',
      'okx',
      'real-time trading',
      'crypto exchange comparison',
    ],
    image: '/social/og-home.png',
  },
  '/arbitrage': {
    title: {
      en: 'Arbitrage - Funding Rate Analysis',
      ko: '차익거래 - 펀딩 비율 분석',
      zh: '套利 - 资金费率分析',
    },
    description: {
      en: 'Advanced funding rate analysis tools for cryptocurrency arbitrage. Compare funding rates across exchanges, analyze historical data, and identify profitable trading opportunities.',
      ko: '암호화폐 차익거래를 위한 고급 펀딩 비율 분석 도구. 거래소 간 펀딩 비율 비교, 과거 데이터 분석, 수익성 있는 거래 기회 식별.',
      zh: '用于加密货币套利的高级资金费率分析工具。比较交易所之间的资金费率，分析历史数据，识别有利可图的交易机会。',
    },
    keywords: [
      'funding rate arbitrage',
      'funding rate comparison',
      'crypto arbitrage analysis',
      'funding rate history',
      'perpetual futures',
      'exchange comparison',
    ],
    image: '/social/og-arbitrage.png',
  },
  '/arbitrage/funding-rate/diff': {
    title: {
      en: 'Funding Rate Difference',
      ko: '펀딩 비율 차이',
      zh: '资金费率差异',
    },
    description: {
      en: 'Compare funding rate differences between exchanges to find optimal arbitrage opportunities in real-time.',
      ko: '거래소 간 펀딩 비율 차이를 실시간으로 비교하여 최적의 차익거래 기회를 찾으세요.',
      zh: '实时比较交易所之间的资金费率差异，找到最佳套利机会。',
    },
    keywords: ['funding rate difference', 'arbitrage spread', 'exchange arbitrage'],
  },
  '/arbitrage/funding-rate/avg': {
    title: {
      en: 'Average Funding Rate',
      ko: '평균 펀딩 비율',
      zh: '平均资金费率',
    },
    description: {
      en: 'Track average funding rates across multiple exchanges and timeframes for better arbitrage decision making.',
      ko: '여러 거래소와 기간의 평균 펀딩 비율을 추적하여 더 나은 차익거래 결정을 내리세요.',
      zh: '跟踪多个交易所和时间范围的平均资金费率，做出更好的套利决策。',
    },
    keywords: ['average funding rate', 'funding rate trends', 'historical funding'],
  },
  '/community-board': {
    title: {
      en: 'Notice Board - Community Updates',
      ko: '공지사항 - 커뮤니티 업데이트',
      zh: '公告板 - 社区更新',
    },
    description: {
      en: 'Stay updated with the latest announcements, news, and community discussions about cryptocurrency arbitrage trading.',
      ko: '암호화폐 차익거래에 대한 최신 공지사항, 뉴스 및 커뮤니티 토론을 확인하세요.',
      zh: '了解有关加密货币套利交易的最新公告、新闻和社区讨论。',
    },
    keywords: ['crypto news', 'trading community', 'announcements', 'updates'],
  },
  '/news': {
    title: {
      en: 'News - Cryptocurrency Market Updates',
      ko: '뉴스 - 암호화폐 시장 업데이트',
      zh: '新闻 - 加密货币市场更新',
    },
    description: {
      en: 'Latest cryptocurrency news, market analysis, and insights for arbitrage traders.',
      ko: '차익거래 트레이더를 위한 최신 암호화폐 뉴스, 시장 분석 및 인사이트.',
      zh: '面向套利交易者的最新加密货币新闻、市场分析和见解。',
    },
    keywords: ['crypto news', 'market analysis', 'trading insights', 'cryptocurrency updates'],
  },
  '/bot': {
    title: {
      en: 'Trading Bot - Automated Arbitrage',
      ko: '트레이딩 봇 - 자동화된 차익거래',
      zh: '交易机器人 - 自动化套利',
    },
    description: {
      en: 'Automate your cryptocurrency arbitrage trading with our advanced bot. Set triggers, manage positions, track PnL, and execute strategies 24/7.',
      ko: '고급 봇으로 암호화폐 차익거래를 자동화하세요. 트리거 설정, 포지션 관리, 손익 추적, 24/7 전략 실행.',
      zh: '使用我们的高级机器人自动化您的加密货币套利交易。设置触发器，管理头寸，跟踪盈亏，全天候执行策略。',
    },
    keywords: [
      'trading bot',
      'automated trading',
      'arbitrage bot',
      'crypto bot',
      'algorithmic trading',
      'auto trading',
    ],
    image: '/social/og-bot.png',
  },
  '/bot/triggers': {
    title: {
      en: 'Trading Triggers',
      ko: '트레이딩 트리거',
      zh: '交易触发器',
    },
    description: {
      en: 'Configure automated trading triggers based on funding rates, price movements, and custom conditions.',
      ko: '펀딩 비율, 가격 변동 및 사용자 정의 조건을 기반으로 자동 트레이딩 트리거를 구성하세요.',
      zh: '根据资金费率、价格变动和自定义条件配置自动交易触发器。',
    },
    keywords: ['trading triggers', 'automated triggers', 'bot configuration'],
  },
  '/bot/scanner': {
    title: {
      en: 'Arbitrage Scanner',
      ko: '차익거래 스캐너',
      zh: '套利扫描仪',
    },
    description: {
      en: 'Scan markets in real-time to identify profitable arbitrage opportunities automatically.',
      ko: '시장을 실시간으로 스캔하여 수익성 있는 차익거래 기회를 자동으로 식별합니다.',
      zh: '实时扫描市场，自动识别有利可图的套利机会。',
    },
    keywords: ['arbitrage scanner', 'opportunity scanner', 'market scanner'],
  },
  '/bot/pnl-history': {
    title: {
      en: 'PnL History',
      ko: '손익 내역',
      zh: '盈亏历史',
    },
    description: {
      en: 'Track your trading performance with detailed profit and loss history.',
      ko: '상세한 손익 내역으로 트레이딩 성과를 추적하세요.',
      zh: '通过详细的盈亏历史跟踪您的交易表现。',
    },
    keywords: ['pnl history', 'trading history', 'profit loss'],
  },
  '/bot/position': {
    title: {
      en: 'Positions',
      ko: '포지션',
      zh: '头寸',
    },
    description: {
      en: 'Monitor and manage your open trading positions across all exchanges.',
      ko: '모든 거래소의 오픈 포지션을 모니터링하고 관리하세요.',
      zh: '监控和管理您在所有交易所的开放头寸。',
    },
    keywords: ['trading positions', 'open positions', 'position management'],
  },
  '/bot/capital': {
    title: {
      en: 'Capital Management',
      ko: '자본 관리',
      zh: '资本管理',
    },
    description: {
      en: 'Manage your trading capital allocation and balance across exchanges.',
      ko: '거래소 간 거래 자본 할당 및 잔액을 관리하세요.',
      zh: '管理您在交易所之间的交易资金分配和余额。',
    },
    keywords: ['capital management', 'balance management', 'fund allocation'],
  },
  '/bot/settings': {
    title: {
      en: 'Bot Settings',
      ko: '봇 설정',
      zh: '机器人设置',
    },
    description: {
      en: 'Configure your trading bot settings, preferences, and trading parameters.',
      ko: '트레이딩 봇 설정, 환경설정 및 거래 매개변수를 구성하세요.',
      zh: '配置您的交易机器人设置、偏好和交易参数。',
    },
    keywords: ['bot settings', 'trading configuration', 'bot preferences'],
  },
  '/bot/api-key': {
    title: {
      en: 'API Key Management',
      ko: 'API 키 관리',
      zh: 'API密钥管理',
    },
    description: {
      en: 'Securely manage your exchange API keys for automated trading.',
      ko: '자동 트레이딩을 위한 거래소 API 키를 안전하게 관리하세요.',
      zh: '安全管理您的交易所API密钥以进行自动交易。',
    },
    keywords: ['api key', 'exchange api', 'api management'],
  },
  '/login': {
    title: {
      en: 'Login',
      ko: '로그인',
      zh: '登录',
    },
    description: {
      en: 'Login to ArbiCrypto to access advanced trading tools and automated arbitrage features.',
      ko: 'ArbiCrypto에 로그인하여 고급 트레이딩 도구 및 자동화된 차익거래 기능에 액세스하세요.',
      zh: '登录ArbiCrypto以访问高级交易工具和自动化套利功能。',
    },
    keywords: ['login', 'sign in', 'user access'],
    noindex: true, // Don't index login pages
  },
  '/register': {
    title: {
      en: 'Register',
      ko: '회원가입',
      zh: '注册',
    },
    description: {
      en: 'Create your ArbiCrypto account to start cryptocurrency arbitrage trading with our advanced platform.',
      ko: 'ArbiCrypto 계정을 생성하여 고급 플랫폼으로 암호화폐 차익거래를 시작하세요.',
      zh: '创建您的ArbiCrypto账户，开始使用我们的高级平台进行加密货币套利交易。',
    },
    keywords: ['register', 'sign up', 'create account'],
    noindex: true, // Don't index registration pages
  },
  '/my-page': {
    title: {
      en: 'My Page',
      ko: '내 페이지',
      zh: '我的页面',
    },
    description: {
      en: 'Manage your account settings, preferences, and profile information.',
      ko: '계정 설정, 환경설정 및 프로필 정보를 관리하세요.',
      zh: '管理您的账户设置、偏好和个人资料信息。',
    },
    keywords: ['my page', 'account settings', 'user profile'],
    noindex: true, // Don't index private pages
  },
};

// Helper function to get SEO data for a specific route
export const getSEOForRoute = (pathname) => {
  const currentLang = i18n.language || 'ko';

  // Find exact match first
  let seoConfig = pageSEO[pathname];

  // If no exact match, try to find parent route (for child routes)
  if (!seoConfig) {
    const pathSegments = pathname.split('/').filter(Boolean);
    for (let i = pathSegments.length; i > 0; i -= 1) {
      const parentPath = `/${pathSegments.slice(0, i).join('/')}`;
      if (pageSEO[parentPath]) {
        seoConfig = pageSEO[parentPath];
        break;
      }
    }
  }

  // If still no match, use defaults
  if (!seoConfig) {
    return {
      title: defaultSEO.defaultTitle,
      description: defaultSEO.defaultDescription[currentLang] || defaultSEO.defaultDescription.ko,
      keywords: defaultSEO.defaultKeywords,
      image: defaultSEO.defaultImage,
      noindex: false,
    };
  }

  return {
    title: typeof seoConfig.title === 'string'
      ? seoConfig.title
      : (seoConfig.title[currentLang] || seoConfig.title.ko || seoConfig.title.en),
    description: typeof seoConfig.description === 'string'
      ? seoConfig.description
      : (seoConfig.description[currentLang] || seoConfig.description.ko || seoConfig.description.en),
    keywords: seoConfig.keywords || defaultSEO.defaultKeywords,
    image: seoConfig.image || defaultSEO.defaultImage,
    noindex: seoConfig.noindex || false,
  };
};

// Helper to generate canonical URL
export const getCanonicalUrl = (pathname) => {
  const siteUrl = getSiteUrl();
  return `${siteUrl}${pathname}`;
};

// Helper to get hreflang URLs for multilingual support
export const getHreflangUrls = (pathname) => {
  const siteUrl = getSiteUrl();
  return {
    en: `${siteUrl}/en${pathname}`,
    ko: `${siteUrl}/ko${pathname}`,
    zh: `${siteUrl}/zh${pathname}`,
  };
};

export { getSiteUrl, getLocale };
