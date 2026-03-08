# Skill: SEO, i18n, and Community Page Spec

---

## SEO Requirements

### Next.js Metadata API
Every page must export `metadata` or `generateMetadata`:
```tsx
// Static pages
export const metadata: Metadata = {
  title: "アーカイブ | Moku",
  description: "韓国ワーキングホリデーに関する記事一覧",
};

// Dynamic pages
export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const article = await fetchArticle(params.id);
  return {
    title: `${article.ja.title} | Moku`,
    description: article.ja.excerpt,
    openGraph: { images: article.imageUrl ? [article.imageUrl] : [] },
  };
}
```

### JSON-LD Structured Data (preserve all)
1. **Organization** — Moku agency info
2. **ProfessionalService** — visa consultation service
3. **FAQPage** — auto-generated from i18n FAQ items
4. **BreadcrumbList** — per page
5. **Article** — for archive articles

### Sitemap — `app/sitemap.ts`
Static pages + all article slugs (static + dynamic from DB).
```typescript
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

  // Fetch dynamic articles from backend
  const res = await fetch(`${API_BASE}/api/articles`);
  const { articles } = await res.json();
  const articlePages = articles.map((a: { id: string; updated_at: string }) => ({
    url: `https://moku.com/archive/${a.id}`,
    lastModified: new Date(a.updated_at),
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  return [...staticPages, ...articlePages];
}
```

### Robots — `app/robots.ts`
```typescript
import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: "/admin" },
      { userAgent: "Googlebot", allow: "/" },
      { userAgent: "Yeti", allow: "/" },  // Naver bot
    ],
    sitemap: "https://moku.com/sitemap.xml",
    host: "https://moku.com",
  };
}
```

### Additional SEO
- Hreflang: ja/ko/en + x-default on multilingual pages
- OG/Twitter meta: title, description, image per page
- Google Analytics 4: measurement ID from `/api/config`
- Search Console verification: Google + Naver meta tags from server config

---

## i18n Structure

### Setup
- Library: i18next + react-i18next (client-side)
- Japanese: bundled inline (primary audience)
- Korean, English: lazy loaded on language switch
- Language detection: localStorage `moku_language` > `navigator.language` > fallback `ja`

### Namespace Keys (~500+ per locale)
`common`, `header`, `footer`, `hero`, `visaProcess`, `archive`, `faq`, `inquiry`, `community`, `partners`, `guideline`, `admin`, `cookie`, `privacy`, `terms`, `tokushoho`, `error`, `breadcrumb`, `notFound`

### Usage Pattern
```tsx
const { t } = useTranslation();
return <h1>{t("hero.title")}</h1>;
```
All UI text MUST come from i18n. No hardcoded Japanese/Korean/English strings.

---

## Community Page Spec (~1500 lines, most complex component)

### Features
- **Post list** with server-side pagination (10/page)
- **Search** by title / author / content (dropdown selector)
- **Filter** by category (question / info / chat)
- **Sort:** newest / oldest / likes / views / comments
- **Post CRUD** with password protection
- **Comment CRUD** with password protection
- **Like/unlike toggle** (visitor ID based, stored in post_likes table)
- **Pinned posts** shown first with visual indicator
- **Experience badges** (experienced / inexperienced) with distinct colors
- **Category badges** (question=blue, info=green, chat=amber)
- **Post detail view** (inline expansion, not separate route)
- **Relative time display** ("3 minutes ago", "2 hours ago", "5 days ago")
- **Skeleton loaders** during data fetch
- **All text from i18n** (no hardcoded strings)

### Data Flow
1. Page load → `GET /api/posts?page=1&limit=10&sort=newest`
2. Bulk fetch likes → `POST /api/posts/likes/bulk { postIds }`
3. Click post → increment view `POST /api/posts/{id}/view`, expand detail
4. Load comments → `GET /api/posts/{id}/comments`
5. Like toggle → `POST /api/posts/{id}/like { visitorId }`
6. Create post → dialog form → `POST /api/posts`
7. Edit/Delete → verify password first → `PUT/DELETE /api/posts/{id}`

### Visitor ID
Generated once per browser via `crypto.randomUUID()`, stored in `localStorage("moku_visitor_id")`.
Used for like toggle (one like per visitor per post).

---

## Admin Dashboard Spec

### Auth Flow
1. Password input → `POST /api/admin/login`
2. Receive JWT → store in React state (not localStorage for security)
3. All admin API calls include `X-Admin-Token: {jwt}` header
4. JWT expires after 24h → redirect to login

### Tabs
1. **Inquiries:** list, status update (pending→contacted→completed), admin notes, delete
2. **Community:** post list, pin/unpin, delete
3. **Archive:** article CRUD with rich text content (HTML), image upload to Supabase Storage, bilingual (ja/ko)
4. **Stats overview:** total inquiries by status, total posts, total views, total comments
