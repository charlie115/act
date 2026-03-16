/**
 * 5-level heatmap color intensity for premium/spread cells.
 * Returns an rgba background string based on value magnitude.
 */

const POSITIVE_LEVELS = [
  { threshold: 3, color: "rgba(22, 199, 132, 0.28)" },
  { threshold: 2, color: "rgba(22, 199, 132, 0.20)" },
  { threshold: 1, color: "rgba(22, 199, 132, 0.13)" },
  { threshold: 0.3, color: "rgba(22, 199, 132, 0.07)" },
  { threshold: 0, color: "rgba(22, 199, 132, 0.03)" },
];

const NEGATIVE_LEVELS = [
  { threshold: -3, color: "rgba(234, 57, 67, 0.28)" },
  { threshold: -2, color: "rgba(234, 57, 67, 0.20)" },
  { threshold: -1, color: "rgba(234, 57, 67, 0.13)" },
  { threshold: -0.3, color: "rgba(234, 57, 67, 0.07)" },
  { threshold: 0, color: "rgba(234, 57, 67, 0.03)" },
];

export function premiumHeatmap(value) {
  const n = Number(value || 0);

  if (!Number.isFinite(n) || n === 0) {
    return "transparent";
  }

  if (n > 0) {
    for (const level of POSITIVE_LEVELS) {
      if (n >= level.threshold) {
        return level.color;
      }
    }
  } else {
    for (const level of NEGATIVE_LEVELS) {
      if (n <= level.threshold) {
        return level.color;
      }
    }
  }

  return "transparent";
}

export function spreadHeatmap(value) {
  const n = Number(value || 0);

  if (!Number.isFinite(n) || n === 0) {
    return "transparent";
  }

  // Spread uses opportunity color for positive (wider spread = more opportunity)
  if (n > 0) {
    if (n >= 2) return "rgba(240, 185, 11, 0.24)";
    if (n >= 1) return "rgba(240, 185, 11, 0.16)";
    if (n >= 0.5) return "rgba(240, 185, 11, 0.10)";
    if (n >= 0.2) return "rgba(240, 185, 11, 0.06)";
    return "rgba(240, 185, 11, 0.03)";
  }

  if (n <= -2) return "rgba(234, 57, 67, 0.20)";
  if (n <= -1) return "rgba(234, 57, 67, 0.12)";
  if (n <= -0.5) return "rgba(234, 57, 67, 0.07)";
  return "rgba(234, 57, 67, 0.03)";
}
