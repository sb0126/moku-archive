"use client";

import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import DOMPurify from "isomorphic-dompurify";
import { Badge } from "@/components/ui/badge";
import { Clock, User } from "lucide-react";
import { ArticleResponse } from "@/types/article";

export default function ArchiveArticle({ article }: { article: ArticleResponse }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language === "ko" ? "ko" : "ja";

  const localeData = (lang === "ko" && article.ko) ? article.ko : article.ja;

  const sanitizedContent = useMemo(() => {
    return DOMPurify.sanitize(localeData.content || "");
  }, [localeData.content]);

  const formattedDate = useMemo(() => {
    if (!article.date) return "";
    return new Date(article.date).toLocaleDateString(lang === "ko" ? "ko-KR" : "ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }, [article.date, lang]);

  return (
    <article className="max-w-4xl mx-auto py-8">
      <header className="mb-10 text-center space-y-4">
        {localeData.category && (
          <Badge variant="outline" className="mb-4 text-sm px-3 py-1 bg-primary/10 text-primary border-primary/20">
            {localeData.category}
          </Badge>
        )}
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-foreground leading-snug">
          {localeData.title}
        </h1>
        
        <div className="flex flex-wrap items-center justify-center gap-6 text-muted-foreground mt-6 text-sm">
          {formattedDate && <time dateTime={article.date!}>{formattedDate}</time>}
          {localeData.author && (
            <div className="flex items-center gap-2">
              <User className="w-4 h-4" />
              <span>{localeData.author}</span>
            </div>
          )}
          {localeData.readTime && (
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>{localeData.readTime}</span>
            </div>
          )}
        </div>
      </header>

      {article.imageUrl && (
        <div className="my-10 aspect-[21/9] w-full relative overflow-hidden rounded-xl shadow-lg border border-border">
          <img
            src={article.imageUrl}
            alt={localeData.imageAlt || localeData.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {localeData.excerpt && (
        <div className="text-lg text-muted-foreground bg-muted/50 p-6 rounded-xl border-l-4 border-primary mb-10 italic">
          {localeData.excerpt}
        </div>
      )}

      <div
        className="prose prose-lg dark:prose-invert max-w-none prose-headings:font-bold prose-a:text-primary prose-img:rounded-xl"
        dangerouslySetInnerHTML={{ __html: sanitizedContent }}
      />

      {localeData.tags && localeData.tags.length > 0 && (
        <div className="mt-12 flex flex-wrap gap-2">
          {localeData.tags.map(tag => (
            <Badge key={tag} variant="secondary" className="px-3 py-1 text-sm bg-secondary text-secondary-foreground hover:bg-secondary/80">
              #{tag}
            </Badge>
          ))}
        </div>
      )}
    </article>
  );
}
