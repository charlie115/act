/**
 * Subtle heatmap: thin left border + very faint background wash.
 * Returns { bg, bar } for use as inline styles.
 */

export function premiumHeatmap(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n === 0) return "transparent";

  const abs = Math.abs(n);
  const t = Math.min(1, abs / 4);

  if (n > 0) return `rgba(22, 199, 132, ${(0.02 + t * 0.08).toFixed(3)})`;
  return `rgba(234, 57, 67, ${(0.02 + t * 0.08).toFixed(3)})`;
}

export function spreadHeatmap(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n === 0) return "transparent";

  const abs = Math.abs(n);
  const t = Math.min(1, abs / 2);

  if (n > 0) return `rgba(240, 185, 11, ${(0.02 + t * 0.10).toFixed(3)})`;
  return `rgba(234, 57, 67, ${(0.02 + t * 0.06).toFixed(3)})`;
}
