# Skill: Frontend Structure & TypeScript Types

---

## Next.js App Router Structure

```
src/
├── app/
│   ├── layout.tsx           # Root: fonts, i18n, CookieConsent, Toaster, ErrorBoundary
│   ├── page.tsx             # Home: Hero + VisaProcess + Archive + FAQ + InquiryForm (SSG+ISR)
│   ├── not-found.tsx        # 404
│   ├── sitemap.ts           # Dynamic sitemap
│   ├── robots.ts            # robots.txt
│   ├── archive/
│   │   ├── page.tsx         # Article list (SSG + ISR 5min)
│   │   └── [id]/page.tsx    # Article detail (SSG + generateStaticParams + ISR 5min)
│   ├── community/page.tsx   # 'use client' — full CRUD board
│   ├── partners/page.tsx    # SSG + ISR 1d
│   ├── guideline/page.tsx   # SSG
│   ├── admin/page.tsx       # 'use client' — admin dashboard
│   ├── privacy/page.tsx     # SSG
│   ├── terms/page.tsx       # SSG
│   └── tokushoho/page.tsx   # SSG
├── components/
│   ├── Header.tsx           # Scroll-aware, mobile hamburger
│   ├── Footer.tsx
│   ├── SideNav.tsx          # Floating side navigation dots
│   ├── LanguageSwitcher.tsx # ja/ko/en dropdown
│   ├── CookieConsent.tsx    # GDPR-style banner
│   ├── Hero.tsx, VisaProcess.tsx, FAQ.tsx, InquiryForm.tsx  # Home sections
│   ├── ArchiveListPage.tsx, ArchiveArticle.tsx
│   ├── CommunityPage.tsx   # ~1500 lines, most complex
│   ├── AdminDashboard.tsx, AdminArchiveTab.tsx
│   ├── Breadcrumb.tsx, ScrollToTop.tsx, FadeInSection.tsx
│   ├── ErrorBoundary.tsx, ErrorState.tsx, NetworkStatus.tsx
│   ├── SkeletonLoaders.tsx  # PageSkeleton, PostListSkeleton, etc.
│   └── ui/                  # shadcn/ui (30+ components, copy as-is)
├── lib/
│   ├── api.ts               # Typed fetch wrapper
│   └── utils.ts             # cn(), scroll helpers
├── types/                   # TypeScript types mirroring backend schemas
│   ├── post.ts
│   ├── comment.ts
│   ├── inquiry.ts
│   ├── article.ts
│   ├── admin.ts
│   └── config.ts
├── i18n/
│   ├── config.ts            # i18next init
│   └── locales/
│       ├── ja.ts            # ~500+ keys, bundled inline
│       ├── ko.ts            # lazy loaded
│       └── en.ts            # lazy loaded
└── styles/
    └── globals.css          # Tailwind + CSS variables
```

## SSR/SSG Strategy
| Page | Strategy | Reason |
|------|----------|--------|
| `/` | SSG + ISR 1h | Static content, SEO critical |
| `/archive` | SSG + ISR 5min | Article list, SEO critical |
| `/archive/[id]` | SSG + `generateStaticParams` + ISR 5min | Per-article, SEO critical |
| `/guideline` | SSG | Static |
| `/community` | CSR (`'use client'`) | Heavy interactivity |
| `/partners` | SSG + ISR 1d | Mostly static |
| `/admin` | CSR (`'use client'`) | Auth-protected, no SEO |
| `/privacy`, `/terms`, `/tokushoho` | SSG | Static legal |

---

## TypeScript Types (mirror backend Pydantic schemas exactly)

```typescript
// src/types/post.ts
export interface PostResponse {
  id: string;
  numericId: number;
  title: string;
  author: string;
  content: string;
  views: number;
  comments: number;
  pinned: boolean;
  pinnedAt: string | null;
  experience: "experienced" | "inexperienced" | null;
  category: "question" | "info" | "chat" | null;
  createdAt: string;
  updatedAt: string;
}

export interface PostListResponse {
  success: boolean;
  posts: PostResponse[];
  count: number;
  total: number;
  totalPages: number;
  currentPage: number;
  limit: number;
}

export interface PostCreateRequest {
  author: string;
  title: string;
  content: string;
  password: string;
  experience?: "experienced" | "inexperienced";
  category?: "question" | "info" | "chat";
}

export interface PostUpdateRequest {
  title?: string;
  content?: string;
  password: string;
}

export interface PostDeleteRequest {
  password?: string;
  isAdmin?: boolean;
}

export interface LikeToggleRequest {
  visitorId: string;
}

export interface LikeResponse {
  success: boolean;
  liked: boolean;
  likes: number;
}

export interface LikeStatusResponse {
  success: boolean;
  likes: number;
  liked: boolean;
}

export interface BulkLikesResponse {
  success: boolean;
  likes: Record<string, number>;
}

export type PostSearchType = "title" | "author" | "content";
export type PostSortField = "newest" | "oldest" | "likes" | "views" | "comments";
export type PostCategoryFilter = "question" | "info" | "chat";
```

```typescript
// src/types/comment.ts
export interface CommentResponse {
  id: string;
  postId: string;
  author: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface CommentCreateRequest {
  author: string;
  content: string;
  password: string;
}

export interface CommentUpdateRequest {
  content: string;
  password: string;
}

export interface CommentListResponse {
  success: boolean;
  comments: CommentResponse[];
  count: number;
}
```

```typescript
// src/types/inquiry.ts
export interface InquiryCreateRequest {
  name: string;
  email: string;
  phone: string;
  age: number;
  preferredDate: string;
  plan: string;
  message?: string;
}

export interface InquiryResponse {
  id: string;
  name: string;
  email: string;
  phone: string;
  age: number;
  preferredDate: string | null;
  plan: string | null;
  message: string;
  status: "pending" | "contacted" | "completed";
  adminNote: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface InquiryListResponse {
  success: boolean;
  inquiries: InquiryResponse[];
  count: number;
}
```

```typescript
// src/types/article.ts
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
```

```typescript
// src/types/admin.ts
export interface AdminLoginResponse {
  success: boolean;
  authenticated: boolean;
  token: string;
}

export interface AdminStats {
  totalInquiries: number;
  pendingInquiries: number;
  contactedInquiries: number;
  completedInquiries: number;
  totalPosts: number;
  totalViews: number;
  totalComments: number;
}

export interface AdminStatsResponse {
  success: boolean;
  stats: AdminStats;
}
```

```typescript
// src/types/config.ts
export interface SiteConfig {
  gaMeasurementId: string;
  verification: {
    google: string | null;
    naver: string | null;
  };
}
```

---

## API Client (typed)

```typescript
// src/lib/api.ts
const API_BASE: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  public status: number;
  public details: string | undefined;
  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data: unknown = await res.json();
  if (!res.ok) {
    const err = data as { error?: string; detail?: string; details?: string };
    throw new ApiError(err.error || err.detail || "Unknown error", res.status, err.details);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "GET", ...init }),
  post: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "POST", body: JSON.stringify(body), ...init }),
  put: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body), ...init }),
  del: <T>(path: string, body?: unknown, init?: RequestInit): Promise<T> =>
    apiFetch<T>(path, { method: "DELETE", body: body ? JSON.stringify(body) : undefined, ...init }),
};
```
