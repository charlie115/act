import sanitizeHtml from "sanitize-html";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
const directBackendBaseUrl =
  process.env.ACW_API_PROXY_TARGET?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_DRF_URL?.replace(/\/$/, "") ||
  "";
const mediaBaseUrl = directBackendBaseUrl;
const API_BASE =
  directBackendBaseUrl ||
  (siteUrl ? `${siteUrl}/api` : null) ||
  "http://localhost:8000";

function buildUrl(pathname, searchParams) {
  const url = new URL(pathname.replace(/^\//, ""), API_BASE.endsWith("/") ? API_BASE : `${API_BASE}/`);

  if (searchParams) {
    Object.entries(searchParams).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }

      if (Array.isArray(value)) {
        value.forEach((item) => url.searchParams.append(key, item));
        return;
      }

      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

async function fetchJson(pathname, searchParams) {
  const response = await fetch(buildUrl(pathname, searchParams), {
    next: { revalidate: 60 },
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${pathname}: ${response.status}`);
  }

  return response.json();
}

export function safeHtml(html = "") {
  const normalizedHtml = mediaBaseUrl
    ? html.replaceAll('src="/media/', `src="${mediaBaseUrl}/media/`)
    : html;

  return sanitizeHtml(normalizedHtml, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img", "h1", "h2", "h3"]),
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      img: ["src", "alt", "title"],
      a: ["href", "name", "target", "rel"],
    },
    allowedSchemes: ["http", "https", "data", "mailto"],
    transformTags: {
      a: (tagName, attribs) => ({
        tagName,
        attribs: {
          ...attribs,
          rel: "noreferrer nofollow",
          target: "_blank",
        },
      }),
    },
  });
}

export function stripHtml(html = "") {
  return sanitizeHtml(html, { allowedTags: [], allowedAttributes: {} }).trim();
}

export function formatDate(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export async function getNews(params = {}) {
  const data = await fetchJson("/newscore/news/", params);
  return data?.results || [];
}

export async function getAnnouncements(params = {}) {
  const data = await fetchJson("/newscore/announcements/", params);
  return data?.results || [];
}

export async function getSocialPosts(params = {}) {
  const data = await fetchJson("/newscore/posts/", params);
  return data?.results || [];
}

export async function getBoardPosts(params = {}) {
  const data = await fetchJson("/board/posts/", params);
  return {
    count: data?.count || 0,
    results: data?.results || [],
  };
}

export async function getBoardPost(postId) {
  return fetchJson(`/board/posts/${postId}/`);
}

export async function getBoardComments(postId) {
  const data = await fetchJson("/board/comments/", { post: postId });
  return data?.results || [];
}
