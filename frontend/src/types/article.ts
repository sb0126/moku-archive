export interface ArticleLocale {
  title: string;
  category: string;
  excerpt: string;
  content: string;        // HTML
  imageAlt: string;
  author: string;
  readTime: string;
  tags: string[];
}

export interface ArticleResponse {
  id: string;
  imageUrl: string | null;
  date: string | null;
  ja: ArticleLocale;
  ko: ArticleLocale | null;
  createdAt: string;
  updatedAt: string;
}

export interface ArticleListResponse {
  success: boolean;
  articles: ArticleResponse[];
  count: number;
}
