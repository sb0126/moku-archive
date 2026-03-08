# Skill: Moku Project Overview

## What is Moku?
Moku is a professional agency website helping Japanese citizens (aged 18-30) apply for Korea's H-1 Working Holiday visa. The agency provides consultation, application support, and settlement guidance.

## Languages
Three languages supported: Japanese (primary), Korean, English.
All UI text comes from i18n locale files (~500+ keys each). No hardcoded strings.

## Design System
```css
--background: #FAFAF9;            /* off-white */
--foreground: #2C2825;            /* soft dark brown */
--primary: #B8935F;               /* muted gold accent */
--accent-text: #8A6420;           /* WCAG AA gold for small text */
--secondary: #F5F3F0;             /* soft beige */
--muted-foreground: #5C5652;      /* WCAG AA compliant */
--destructive: #C62828;
--border: rgba(44, 40, 37, 0.08);
--radius: 0.5rem;
```
Fonts: Noto Sans JP, Noto Sans KR, M PLUS 1p (Google Fonts)
Design inspiration: letusibiza.com — minimal, elegant, warm

## Tech Stack
- Frontend: Next.js 15 (App Router) + TypeScript (strict) + Tailwind CSS v4
- Backend: FastAPI + Pydantic v2 + SQLModel + asyncpg
- Database: Supabase PostgreSQL (existing instance)
- Storage: Supabase Storage (private bucket, signed URLs)
- Auth: JWT admin auth (python-jose, HS256, 24h expiry)
- Password: passlib[bcrypt] (new) + SHA-256/plaintext legacy support
- Deployment: Vercel (frontend) + Railway or Fly.io (backend, Docker)

## Environment Variables
```bash
# Backend
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...     # NEVER expose to frontend
MOKU_ADMIN_PASSWORD=
JWT_SECRET_KEY=
GA_MEASUREMENT_ID=G-M0EESK8HQK
GOOGLE_SITE_VERIFICATION=
NAVER_SITE_VERIFICATION=

# Frontend
NEXT_PUBLIC_API_URL=https://api.moku.com
```
