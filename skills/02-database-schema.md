# Skill: Database Schema

Supabase PostgreSQL. All tables already exist — DO NOT recreate. Use Alembic only if schema changes are needed.

```sql
CREATE TABLE posts (
    id TEXT PRIMARY KEY,                    -- "post_{unix_ms}"
    numeric_id BIGINT NOT NULL,             -- Unix ms, ordering key
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    password TEXT NOT NULL,                  -- bcrypt / "saltHex:hashHex" / plaintext
    views INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    pinned BOOLEAN NOT NULL DEFAULT FALSE,
    pinned_at TIMESTAMPTZ,
    experience TEXT,                         -- 'experienced' | 'inexperienced' | NULL
    category TEXT,                           -- 'question' | 'info' | 'chat' | NULL
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE post_likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT NOT NULL REFERENCES posts(id),
    visitor_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(post_id, visitor_id)
);
-- Like count = COUNT rows in post_likes WHERE post_id = X (normalized, no counter column)

CREATE TABLE comments (
    id TEXT PRIMARY KEY,                     -- "comment_{postId}_{unix_ms}"
    post_id TEXT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE inquiries (
    id TEXT PRIMARY KEY,                     -- "inquiry_{unix_ms}"
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    age INTEGER NOT NULL,
    preferred_date TEXT,
    plan TEXT,
    message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'contacted' | 'completed'
    admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE articles (
    id TEXT PRIMARY KEY,                     -- URL slug e.g. "visa-application-guide"
    image_url TEXT,                          -- HTTP URL or "storage:articles/folder/file.ext"
    date TEXT,                               -- "YYYY-MM-DD"
    ja JSONB NOT NULL,                       -- {title, category, excerpt, content(HTML), imageAlt, author, readTime, tags[]}
    ko JSONB,                                -- same structure, Korean
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Key Behaviors
- `post_likes`: normalized counting. Never store like count directly; always COUNT rows.
- `comments`: CASCADE delete when parent post is deleted.
- `articles.ja` / `articles.ko`: JSONB containing `{title, category, excerpt, content(HTML), imageAlt, author, readTime, tags[]}`.
- `articles.image_url`: if starts with `storage:`, must resolve to signed URL (1h expiry) before sending to client.
- Password fields store THREE possible formats: bcrypt ($2b$...), SHA-256 (saltHex:hashHex), plaintext (legacy).
