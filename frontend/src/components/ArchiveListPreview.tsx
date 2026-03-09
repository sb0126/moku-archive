"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { FadeInSection } from "@/components/FadeInSection";
import { Button } from "@/components/ui/button";
import { ArrowRight, Clock } from "lucide-react";
import { ArticleResponse } from "@/types/article";
import { cn } from "@/lib/utils";

interface ArchiveListPreviewProps {
  articles: ArticleResponse[];
}

export function ArchiveListPreview({ articles }: ArchiveListPreviewProps) {
  const { t, i18n } = useTranslation();
  const [activeCategory, setActiveCategory] = useState("All");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const categories = ["All", "Guide", "Life", "News"];

  // A helper to get the title based on locale, fallback to ja
  const getArticleLocale = (article: ArticleResponse) => {
    // Only use client language after hydration to prevent mismatches
    const lang = mounted ? i18n.language : "ja";
    return lang === "ko" && article.ko ? article.ko : article.ja;
  };

  const formatDate = (dateString: string | Date) => {
    const d = new Date(dateString);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}.${month}.${day}`;
  };

  const featuredArticle = articles.length > 0 ? articles[0] : null;
  const listArticles = articles.length > 1 ? articles.slice(1, 4) : [];

  return (
    <section id="archive" className="bg-[#FAFAF9] py-28 md:py-36">
      <div className="container mx-auto px-6 max-w-4xl">
        <FadeInSection>
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
            <div>
              <h2 className="text-[32px] md:text-[40px] font-bold tracking-tight text-[#2C2825] mb-4" suppressHydrationWarning>
                {t("preview.title", "Latest Guides & News", { lng: mounted ? i18n.language : "ja" })}
              </h2>
              <div className="flex gap-2 flex-wrap mt-6">
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    suppressHydrationWarning
                    className={cn(
                      "px-5 py-1.5 rounded-full text-sm font-medium transition-colors border",
                      activeCategory === cat
                        ? "bg-[#B8935F] text-white border-[#B8935F]"
                        : "bg-[#FAFAF9] text-[#6B6660] border-[#2C2825]/10 hover:bg-[#F5F3F0]"
                    )}
                  >
                    {t(`categories.${cat.toLowerCase()}`, cat, { lng: mounted ? i18n.language : "ja" })}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </FadeInSection>

        {articles.length === 0 ? (
          <p className="text-center py-12 text-[#6B6660]" suppressHydrationWarning>
            {t("preview.empty", "No articles found.", { lng: mounted ? i18n.language : "ja" })}
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8">
            {/* Featured Article */}
            {featuredArticle && (
              <FadeInSection delay={150}>
                <Link href={`/archive/${featuredArticle.id}`} className="group block h-full">
                  <div className="relative h-72 w-full rounded-2xl overflow-hidden mb-6 shadow-sm border border-[#2C2825]/5">
                    <Image
                      src={featuredArticle.imageUrl || "https://images.unsplash.com/photo-1548115184-bc6544d06a58"}
                      alt={getArticleLocale(featuredArticle).imageAlt || getArticleLocale(featuredArticle).title}
                      fill
                      className="object-cover transition-transform duration-700 group-hover:scale-105 filter brightness-[0.98] contrast-[0.95] saturate-[0.85]"
                      sizes="(max-width: 1024px) 100vw, 60vw"
                    />
                    <div className="absolute top-4 left-4 bg-[#B8935F] text-white px-4 py-1.5 rounded-full text-xs font-bold shadow-md tracking-wider" suppressHydrationWarning>
                      {t("preview.featured", "注目記事", { lng: mounted ? i18n.language : "ja" })}
                    </div>
                  </div>
                  <div className="px-1">
                    <span className="text-[#8A6420] text-sm font-semibold mb-2 block">
                      {getArticleLocale(featuredArticle).category}
                    </span>
                    <h3 className="text-2xl font-bold text-[#2C2825] mb-3 group-hover:text-[#B8935F] transition-colors line-clamp-2 leading-snug">
                      {getArticleLocale(featuredArticle).title}
                    </h3>
                    <p className="text-[#6B6660] leading-relaxed line-clamp-2 text-[15px]">
                      {getArticleLocale(featuredArticle).excerpt}
                    </p>
                  </div>
                </Link>
              </FadeInSection>
            )}

            {/* List Articles */}
            <div className="flex flex-col gap-5 justify-start">
              {listArticles.map((article, idx) => {
                const localeData = getArticleLocale(article);
                return (
                  <FadeInSection key={article.id} delay={(idx + 2) * 150}>
                    <Link href={`/archive/${article.id}`} className="group flex items-center gap-5 p-3 rounded-xl hover:bg-white hover:shadow-sm transition-all border border-transparent hover:border-[#2C2825]/5">
                      <div className="relative w-28 h-24 flex-shrink-0 rounded-lg overflow-hidden border border-[#2C2825]/5">
                        <Image
                          src={article.imageUrl || "https://images.unsplash.com/photo-1517154421773-0529f29ea451"}
                          alt={localeData.title}
                          fill
                          className="object-cover transition-transform duration-700 group-hover:scale-110 filter brightness-[0.98] contrast-[0.95] saturate-[0.85]"
                          sizes="120px"
                        />
                      </div>
                      <div className="flex flex-col flex-1 min-w-0 py-1">
                        <span className="text-[#8A6420] text-xs font-semibold mb-1">
                          {localeData.category}
                        </span>
                        <h4 className="text-[15px] font-bold text-[#2C2825] leading-snug line-clamp-2 group-hover:text-[#B8935F] transition-colors mb-2">
                          {localeData.title}
                        </h4>
                        <span className="text-xs text-[#6B6660] flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDate(article.createdAt)}
                        </span>
                      </div>
                    </Link>
                  </FadeInSection>
                );
              })}
            </div>
          </div>
        )}

        <FadeInSection delay={500} className="mt-14 flex justify-center">
          <Button asChild variant="outline" className="rounded-full px-10 py-6 h-auto text-[#2C2825] border-[#2C2825]/20 hover:bg-[#F5F3F0] font-medium transition-colors w-full sm:w-auto hover:text-[#B8935F]">
            <Link href="/archive" className="flex items-center" suppressHydrationWarning>
              {t("preview.viewAll", "もっと見る", { lng: mounted ? i18n.language : "ja" })} <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </FadeInSection>

      </div>
    </section>
  );
}
