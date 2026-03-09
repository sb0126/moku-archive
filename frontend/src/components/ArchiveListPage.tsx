"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock } from "lucide-react";
import { ArticleResponse } from "@/types/article";

export default function ArchiveListPage({ articles }: { articles: ArticleResponse[] }) {
  const { t, i18n } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const lang = mounted && i18n.language === "ko" ? "ko" : "ja";

  const formatDate = (dateString: string | Date) => {
    const d = new Date(dateString);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}.${month}.${day}`;
  };

  return (
    <>
      <div className="mb-12 mt-4 text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-[#2C2825]">{t("archive.title", "Archive", { lng: mounted ? i18n.language : "ja" })}</h1>
        <p className="text-xl text-[#6B6660] max-w-3xl mx-auto break-keep">
          {t("archive.description", "Helpful information for working holiday preparation and local life in Korea.", { lng: mounted ? i18n.language : "ja" })}
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {articles.map((article) => {
        // Fallback to ja if ko is not available
        const localeData = (lang === "ko" && article.ko) ? article.ko : article.ja;
        
        return (
          <Link key={article.id} href={`/archive/${article.id}`}>
            <div className="rounded-2xl border border-[#2C2825]/6 h-full overflow-hidden hover:shadow-lg transition-shadow duration-300 group cursor-pointer bg-white flex flex-col">
              <div className="relative h-56 w-full bg-muted overflow-hidden shrink-0">
                {article.imageUrl ? (
                  <img
                    src={article.imageUrl}
                    alt={localeData.imageAlt || localeData.title}
                    className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500 brightness-[0.98] contrast-[0.95] saturate-[0.85]"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground bg-secondary/50">
                    No Image
                  </div>
                )}
                {localeData.category && (
                  <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-medium text-[#2C2825]">
                    {localeData.category}
                  </div>
                )}
              </div>
              <div className="p-5 flex flex-col gap-3 flex-1">
                <h3 className="text-lg font-bold line-clamp-2 leading-snug group-hover:text-[#8A6420] transition-colors text-[#2C2825]">
                  {localeData.title}
                </h3>
                {localeData.excerpt && (
                  <p className="text-sm text-[#6B6660] line-clamp-2">
                    {localeData.excerpt}
                  </p>
                )}
                <div className="flex items-center gap-4 text-xs text-[#6B6660] mt-auto pt-2">
                  {article.date && (
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {formatDate(article.date)}
                    </span>
                  )}
                  {localeData.readTime && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {localeData.readTime}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
    </>
  );
}
