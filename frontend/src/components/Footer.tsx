"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { MapPin, Mail } from "lucide-react";

const XIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 24.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.045 4.126H5.078z" />
  </svg>
);

const InstagramIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
  </svg>
);

const LineIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
    <path d="M24 10.304c0-5.369-5.383-9.738-12-9.738-6.616 0-12 4.369-12 9.738 0 4.814 3.53 8.909 8.356 9.617 1.25.176 1.464.444 1.348 1.493-.075.688-.236 1.581-.236 1.581s-.11.666.581.332c.69-.333 4.845-2.812 7.279-5.368 1.636-1.724 2.672-3.812 2.672-6.16zM8.342 12.871h-2.347c-.201 0-.365-.164-.365-.365v-4.524c0-.201.164-.365.365-.365h.923c.201 0 .365.164.365.365v3.6h1.059c.201 0 .365.164.365.365v.924h.001zm3.629-.365c0 .201-.164.365-.365.365h-.924c-.201 0-.365-.164-.365-.365v-4.524c0-.201.164-.365.365-.365h.924c.201 0 .365.164.365.365v4.524zm4.498 0c0 .201-.164.365-.365.365h-1.077c-.12 0-.232-.058-.299-.153l-1.898-2.656v2.445c0 .201-.164.365-.365.365h-.923c-.201 0-.365-.164-.365-.365v-4.524c0-.201.164-.365.365-.365h.966c.121 0 .233.059.299.155l1.986 2.766v-2.556c0-.201.164-.365.365-.365h.923c.201 0 .365.164.365.365v4.524h.023zm3.782-3.235c0 .201-.164.365-.365.365h-1.928v.831h1.928c.201 0 .365.164.365.365v.924c0 .201-.164.365-.365.365h-2.852c-.201 0-.365-.164-.365-.365v-4.524c0-.201.164-.365.365-.365h2.852c.201 0 .365.164.365.365v.923c0-.001-.164.364-.365.364h-1.928v.751h1.928c.201 0 .365.164.365.364v-.001h.001z"/>
  </svg>
);

export function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="bg-[#2C2825] text-[#E8E5E1] py-10">
      <div className="container mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
        
        {/* Logo and Description */}
        <div className="flex flex-col">
          <Link href="/" className="text-xl lg:text-2xl font-bold text-[#9E7030] mb-3 block tracking-tight">
            MOKU
          </Link>
          <p className="text-xs opacity-80 mb-5 leading-relaxed">
            {t("footer.description1", "日本と韓国をつなぐ架け橋。")}<br />
            {t("footer.description2", "あなたのワーキングホリデーを、真心を込めてサポートします。")}
          </p>
          <div className="flex items-center gap-3 mt-auto">
            <Link href="https://twitter.com/moku" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-9 h-9 rounded-full border border-[#B8935F]/20 text-[#B8935F] hover:bg-[#B8935F]/20 transition-colors">
              <XIcon />
              <span className="sr-only">X (Twitter)</span>
            </Link>
            <Link href="https://instagram.com/moku" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-9 h-9 rounded-full border border-[#B8935F]/20 text-[#B8935F] hover:bg-[#B8935F]/20 transition-colors">
              <InstagramIcon />
              <span className="sr-only">Instagram</span>
            </Link>
            <Link href="https://line.me/ti/p/moku" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-9 h-9 rounded-full border border-[#B8935F]/20 text-[#B8935F] hover:bg-[#B8935F]/20 transition-colors">
              <LineIcon />
              <span className="sr-only">LINE</span>
            </Link>
          </div>
        </div>
        
        {/* Sitemap */}
        <div className="flex flex-col gap-3">
          <h3 className="font-semibold text-[#B8935F] text-[15px] mb-1">{t("footer.sitemap", "サイトマップ")}</h3>
          <Link href="/about" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.about", "MOKUについて")}</Link>
          <Link href="/archive" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.archive", "アーカイブ")}</Link>
          <Link href="/community" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.community", "コミュニティ")}</Link>
          <Link href="/partners" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.partners", "提携サービス")}</Link>
        </div>

        {/* Services */}
        <div className="flex flex-col gap-3">
          <h3 className="font-semibold text-[#B8935F] text-[15px] mb-1">{t("footer.services", "サービス")}</h3>
          <Link href="/visa" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.visa", "ビザ申請の流れ")}</Link>
          <Link href="/faq" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.faq", "よくある質問")}</Link>
          <Link href="/consultation" className="text-sm opacity-80 hover:text-[#B8935F] transition-colors">{t("footer.consultation", "無料相談")}</Link>
        </div>

        {/* Contact */}
        <div className="flex flex-col gap-3">
          <h3 className="font-semibold text-[#B8935F] text-[15px] mb-1">{t("footer.contact", "お問い合わせ")}</h3>
          <div className="flex items-center gap-2 text-sm opacity-80">
            <Mail className="w-4 h-4 opacity-70" strokeWidth={1.5} />
            <a href="mailto:info@moku.com" className="hover:text-[#B8935F] transition-colors">info@moku.com</a>
          </div>
          <div className="flex items-start gap-2 text-sm opacity-80 leading-relaxed">
            <MapPin className="w-4 h-4 opacity-70 mt-0.5 flex-shrink-0" strokeWidth={1.5} />
            <address className="not-italic">
              {t("footer.address.city", "ソウル特別市 江南区")}<br />
              {t("footer.address.street", "테헤란로 123")}
            </address>
          </div>
        </div>
      </div>
      
      {/* Bottom Row */}
      <div className="container mx-auto px-6 mt-10 pt-6 border-t border-[#B8935F]/10 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-sm opacity-70">
          © {new Date().getFullYear()} MOKU. All rights reserved.
        </div>
        <div className="flex flex-wrap justify-center items-center gap-6">
          <Link href="/privacy" className="text-sm opacity-70 hover:text-[#B8935F] transition-colors whitespace-nowrap">{t("footer.privacy", "プライバシーポリシー")}</Link>
          <Link href="/terms" className="text-sm opacity-70 hover:text-[#B8935F] transition-colors whitespace-nowrap">{t("footer.terms", "利用規約")}</Link>
          <Link href="/tokushoho" className="text-sm opacity-70 hover:text-[#B8935F] transition-colors whitespace-nowrap">{t("footer.tokushoho", "特定商取引法")}</Link>
        </div>
      </div>
    </footer>
  );
}
