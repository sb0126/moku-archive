import type { Metadata } from "next";
import { Noto_Sans_JP, Noto_Sans_KR, M_PLUS_1p } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { I18nProvider } from "@/components/I18nProvider";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { CookieConsent } from "@/components/CookieConsent";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { NetworkStatus } from "@/components/NetworkStatus";
import { GoogleAnalytics } from "@/components/GoogleAnalytics";
import "@/styles/globals.css";

const notoSansJP = Noto_Sans_JP({
  variable: "--font-noto-sans-jp",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

const notoSansKR = Noto_Sans_KR({
  variable: "--font-noto-sans-kr",
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

const mPlus1p = M_PLUS_1p({
  variable: "--font-m-plus-1p",
  weight: ["400", "500", "700"],
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: "Moku | 韓国ワーキングホリデーサポート",
  description: "ビザ申請から家探し、生活サポートまで",
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
    shortcut: '/favicon.svg',
  },
  alternates: {
    canonical: 'https://moku.com',
    languages: {
      'ja': 'https://moku.com',
      'ko': 'https://moku.com?lang=ko',
      'en': 'https://moku.com?lang=en',
      'x-default': 'https://moku.com',
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <body
        className={`${notoSansJP.variable} ${notoSansKR.variable} ${mPlus1p.variable} antialiased bg-background text-foreground min-h-screen flex flex-col`}
      >
        <GoogleAnalytics />
        <I18nProvider>
          <ErrorBoundary>
            <NetworkStatus />
            <Header />
            <main className="flex-1 flex flex-col min-h-[calc(100vh-64px)] overflow-x-hidden pt-16">
              {children}
            </main>
            <Footer />
            <CookieConsent />
          </ErrorBoundary>
        </I18nProvider>
        <Toaster position="bottom-center" />
      </body>
    </html>
  );
}
