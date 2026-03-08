import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Script from "next/script";
import { Breadcrumb } from "@/components/Breadcrumb";
import ArchiveArticle from "@/components/ArchiveArticle";
import { ArticleResponse, ArticleListResponse } from "@/types/article";

export const revalidate = 300; // SSG + ISR 5 minutes

interface PageProps {
  params: Promise<{ id: string }>;
}

async function fetchArticle(id: string): Promise<ArticleResponse | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/articles/${id}`);
    
    if (!res.ok) {
      return null;
    }
    const data: ArticleResponse = await res.json();
    return data;
  } catch (error) {
    console.error(`Failed to fetch article ${id}:`, error);
    return null;
  }
}

export async function generateStaticParams(): Promise<{ id: string }[]> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/articles`);
    
    if (res.ok) {
      const data: ArticleListResponse = await res.json();
      return (data.articles || []).map((article) => ({ id: article.id }));
    }
  } catch (error) {
    console.error("Failed to fetch articles for static params:", error);
  }
  return [];
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const p = await params;
  const article = await fetchArticle(p.id);
  
  if (!article) {
    return { title: "Not Found | Moku" };
  }

  const url = `https://moku.com/archive/${article.id}`;

  return {
    title: `${article.ja?.title || "記事詳細"} | Moku`,
    description: article.ja?.excerpt || undefined,
    openGraph: {
      images: article.imageUrl ? [article.imageUrl] : [],
    },
    alternates: {
      canonical: url,
      languages: {
        'ja': url,
        'ko': `${url}?lang=ko`,
        'en': `${url}?lang=en`,
        'x-default': url,
      },
    },
  };
}

export default async function ArchiveDetailPage({ params }: PageProps) {
  const p = await params;
  const article = await fetchArticle(p.id);

  if (!article) {
    notFound();
  }

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.ja?.title || "Moku Article",
    image: article.imageUrl ? [article.imageUrl] : [],
    datePublished: article.createdAt,
    dateModified: article.updatedAt,
    author: [
      {
        "@type": "Person",
        name: article.ja?.author || "Moku Team",
      },
    ],
  };

  return (
    <>
      <Script
        id={`article-jsonld-${article.id}`}
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="container mx-auto px-4 py-16 md:py-20 max-w-5xl min-h-screen mt-4">
        <Breadcrumb />
        <ArchiveArticle article={article} />
      </div>
    </>
  );
}
