"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";

export default function NotFound() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center bg-[#FAFAF9]">
      <h1 className="text-8xl font-bold text-[#B8935F]/20 mb-4">{t('notFound.title', '404')}</h1>
      <p className="text-xl text-[#6B6660] mb-8">
        {t('notFound.description', 'お探しのページは見つかりませんでした。')}
      </p>
      <Link 
        href="/"
        className="px-6 py-3 bg-[#B8935F] text-white rounded-full hover:bg-[#8A6420] transition-colors shadow-sm"
      >
        {t('notFound.backHome', 'ホームへ戻る')}
      </Link>
    </div>
  );
}
