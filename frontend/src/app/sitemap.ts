import type { MetadataRoute } from "next";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPages: MetadataRoute.Sitemap = [
    { url: "https://moku.com", lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
    { url: "https://moku.com/archive", changeFrequency: "weekly", priority: 0.8 },
    { url: "https://moku.com/guideline", changeFrequency: "monthly", priority: 0.7 },
    { url: "https://moku.com/community", changeFrequency: "daily", priority: 0.6 },
    { url: "https://moku.com/partners", changeFrequency: "monthly", priority: 0.5 },
    { url: "https://moku.com/privacy", changeFrequency: "yearly", priority: 0.2 },
    { url: "https://moku.com/terms", changeFrequency: "yearly", priority: 0.2 },
    { url: "https://moku.com/tokushoho", changeFrequency: "yearly", priority: 0.2 },
  ];

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/articles`);
    if (res.ok) {
      const { articles } = await res.json();
      const articlePages = articles.map((a: { id: string; updatedAt: string }) => ({
        url: `https://moku.com/archive/${a.id}`,
        lastModified: new Date(a.updatedAt),
        changeFrequency: "monthly" as const,
        priority: 0.6,
      }));
      return [...staticPages, ...articlePages];
    }
  } catch (error) {
    console.error("Failed to fetch articles for sitemap", error);
  }

  return staticPages;
}
