"use client";

import { useEffect, useState } from "react";

// optimize.solve() の実際の処理段階（時間枠の適用・省略ペナルティ・
// GUIDED_LOCAL_SEARCHでの組み替え）に即した文言にしている
const MESSAGES = [
  "候補スポットを評価中...",
  "拝観時間を照合中...",
  "順路を組み替え中...",
  "移動時間を計算中...",
];

export default function LoadingMessage() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % MESSAGES.length);
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  return <div className="mb-4 text-sm text-[#6b6b6b]">{MESSAGES[index]}</div>;
}
