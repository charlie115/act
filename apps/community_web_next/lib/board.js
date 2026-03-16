import { fetchCachedJson } from "./clientCache";

export const POST_CATEGORY_LIST = [
  { label: "자유", value: "FREE", color: "#8f9bb7" },
  { label: "질문", value: "QUESTION", color: "#2b73ff" },
  { label: "정보", value: "INFO", color: "#16c784" },
  { label: "분석", value: "ANALYSIS", color: "#f0b90b" },
  { label: "후기", value: "REVIEW", color: "#e879f9" },
];

export async function getPost(postId) {
  return fetchCachedJson(`/api/board/posts/${postId}/`, { ttlMs: 5000 });
}

export async function getComments(postId) {
  const data = await fetchCachedJson(`/api/board/comments/?post=${postId}`, { ttlMs: 5000 });
  return Array.isArray(data) ? data : data?.results || [];
}
