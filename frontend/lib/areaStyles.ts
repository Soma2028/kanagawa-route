// app.py の AREA_COLORS / AREA_ICONS を移植したもの

export const AREA_COLORS: Record<string, string> = {
  北鎌倉: "#4a7c59",
  八幡宮: "#b5651d",
  金沢街道: "#6b5b95",
  長谷: "#2b7a9e",
  江ノ電: "#d4874a",
  西鎌倉: "#7a9e2b",
  大町材木座: "#9e2b5b",
  その他: "#5a5a5a",
  起点: "#c0392b",
  昼食: "#c9902e",
};

export const AREA_ICONS: Record<string, string> = {
  北鎌倉: "🍃",
  八幡宮: "⛩️",
  金沢街道: "🎋",
  長谷: "🗿",
  江ノ電: "🌊",
  西鎌倉: "🦊",
  大町材木座: "🏯",
  その他: "📍",
  昼食: "🍱",
};

export function areaColor(area: string): string {
  return AREA_COLORS[area] ?? "#5a5a5a";
}

export function areaIcon(area: string): string {
  return AREA_ICONS[area] ?? "📍";
}

export function stars(score: number): string {
  const filled = Math.round(score / 2);
  return "★".repeat(filled) + "☆".repeat(5 - filled);
}
