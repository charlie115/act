import React from 'react';
import { Helmet } from 'react-helmet';
import { useLocation } from 'react-router-dom';

import i18n from 'configs/i18n';
import {
  defaultSEO,
  getSEOForRoute,
  getCanonicalUrl,
  getSiteUrl,
  getLocale,
} from 'configs/seo';

/**
 * SEO Component - Comprehensive meta tags management
 *
 * Provides:
 * - Dynamic title and meta descriptions
 * - Open Graph tags for social media
 * - Twitter Card tags
 * - Canonical URLs
 * - Language-specific tags (hreflang)
 * - Structured data support
 */
function SEO({
  title = null,
  description = null,
  keywords = null,
  image = null,
  type = 'website',
  noindex = false,
  structuredData = null,
  children = null,
}) {
  const location = useLocation();
  const currentLang = i18n.language || 'ko';
  const locale = getLocale(currentLang);

  // Get route-specific SEO data
  const routeSEO = getSEOForRoute(location.pathname);

  // Use provided props or fall back to route-specific or default values
  const finalTitle = title || routeSEO.title || defaultSEO.defaultTitle;
  const finalDescription = description || routeSEO.description;
  const finalKeywords = keywords || routeSEO.keywords;
  const finalImage = image || routeSEO.image;
  const finalNoindex = noindex || routeSEO.noindex;

  // Generate URLs
  const canonicalUrl = getCanonicalUrl(location.pathname);
  const siteUrl = getSiteUrl();
  const fullImageUrl = finalImage?.startsWith('http')
    ? finalImage
    : `${siteUrl}${finalImage}`;

  // Generate hreflang URLs
  const hreflangUrls = {
    ko: `${siteUrl}/ko${location.pathname}`,
    en: `${siteUrl}/en${location.pathname}`,
    zh: `${siteUrl}/zh${location.pathname}`,
  };

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <html lang={currentLang} />
      <title>{finalTitle}</title>
      <meta name="description" content={finalDescription} />
      {finalKeywords && finalKeywords.length > 0 && (
        <meta name="keywords" content={finalKeywords.join(', ')} />
      )}

      {/* Robots */}
      {finalNoindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Canonical URL */}
      <link rel="canonical" href={canonicalUrl} />

      {/* Open Graph Tags */}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={finalTitle} />
      <meta property="og:description" content={finalDescription} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:site_name" content={defaultSEO.siteName} />
      <meta property="og:locale" content={locale} />
      {finalImage && <meta property="og:image" content={fullImageUrl} />}
      {finalImage && <meta property="og:image:width" content="1200" />}
      {finalImage && <meta property="og:image:height" content="630" />}
      {finalImage && <meta property="og:image:alt" content={finalTitle} />}

      {/* Twitter Card Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={finalTitle} />
      <meta name="twitter:description" content={finalDescription} />
      {finalImage && <meta name="twitter:image" content={fullImageUrl} />}
      {finalImage && <meta name="twitter:image:alt" content={finalTitle} />}
      {defaultSEO.twitterHandle && (
        <meta name="twitter:site" content={defaultSEO.twitterHandle} />
      )}

      {/* Language Alternates (hreflang) */}
      <link rel="alternate" hrefLang="ko" href={hreflangUrls.ko} />
      <link rel="alternate" hrefLang="en" href={hreflangUrls.en} />
      <link rel="alternate" hrefLang="zh" href={hreflangUrls.zh} />
      <link rel="alternate" hrefLang="x-default" href={hreflangUrls.ko} />

      {/* Structured Data (JSON-LD) */}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}

      {/* Additional custom head elements */}
      {children}
    </Helmet>
  );
}

export default SEO;
