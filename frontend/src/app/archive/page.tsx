import type { Metadata } from "next";
import ArchiveListPage from "@/components/ArchiveListPage";
import { Breadcrumb } from "@/components/Breadcrumb";
import { ArticleListResponse, ArticleResponse } from "@/types/article";

export const revalidate = 300; // SSG + ISR 5 minutes

export const metadata: Metadata = {
  title: "アーカイブ | Moku",
  description: "韓国ワーキングホリデーに関する記事一覧",
};

export default async function ArchivePage() {
  let articles: ArticleResponse[] = [];
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/articles`);
    
    if (res.ok) {
      const data: ArticleListResponse = await res.json();
      articles = data.articles || [];
    }
  } catch (error) {
    console.error("Failed to fetch articles:", error);
  }

  return (
    <div className="bg-[#FAFAF9] min-h-screen pt-16 md:pt-20">
      <div className="container mx-auto px-4 max-w-5xl pb-16 mt-4">
        <Breadcrumb />
        <ArchiveListPage articles={articles} />
      </div>
    </div>
  );
}
