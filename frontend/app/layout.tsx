import type { Metadata } from "next";
import { M_PLUS_Rounded_1c } from "next/font/google";
import "./globals.css";

// 丸ゴシック。可変フォントではないためウェイトを明示する。
// 日本語はサブセットが多く preload すると読み込みが重くなるため preload は無効にし、
// subsets は指定しない（指定すると日本語グリフが落ちる）。
const mPlusRounded = M_PLUS_Rounded_1c({
  variable: "--font-rounded",
  weight: ["400", "500", "700"],
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: "鎌倉ルート最適化",
  description: "持ち時間と好みに合わせて、満足度が最大になる鎌倉観光の順路を提案します",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" className={`${mPlusRounded.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
