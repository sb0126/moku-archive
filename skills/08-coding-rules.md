# Skill: Coding Rules & Conventions

---

## Universal Rules

1. **Every function, parameter, return type, and variable MUST have explicit type annotations.**
2. Backend: `mypy --strict` must pass.
3. Frontend: `tsc --noEmit` must pass.
4. No `# type: ignore` or `@ts-ignore` unless absolutely unavoidable (document reason).
5. No `Any` type except for JSONB dict fields in SQLModel models.

---

## Python Backend Rules

### Formatting & Linting
- Formatter: `ruff format`
- Linter: `ruff check` (rules: E, F, I, UP, B, SIM, N)
- Type checker: `mypy --strict`

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Enum members: `UPPER_SNAKE_CASE`

### Pydantic Rules
- All schemas inherit from `BaseModel`
- Use `Field()` with min_length, max_length, ge, le constraints
- Use `Literal["a", "b"]` for fixed value sets
- Use `field_validator` for custom validation
- camelCase API fields: use `alias="camelName"` + `model_config = {"populate_by_name": True}`
- Response serialization: use `serialization_alias` for camelCase output

### SQLModel Rules
- All table models use `table=True`
- Primary keys use `sa_column=Column(Text, primary_key=True)` for text PKs
- `nullable=False` on all required fields
- `default_factory=datetime.utcnow` for timestamps (not `default=datetime.utcnow`)
- Foreign keys via `Field(foreign_key="table.column")`
- Index frequently queried columns

### Error Handling
```python
from fastapi import HTTPException

# Standard error responses
raise HTTPException(status_code=400, detail="必須項目をすべて入力してください")
raise HTTPException(status_code=401, detail="管理者認証が必要です")
raise HTTPException(status_code=403, detail="パスワードが正しくありません")
raise HTTPException(status_code=404, detail="投稿が見つかりません")
raise HTTPException(status_code=409, detail="同じIDの記事が既に存在します")
raise HTTPException(status_code=422, detail=f"スパムが検出されました: {reason}")
raise HTTPException(status_code=429, detail="リクエストが多すぎます")
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"New post created: {post_id}")
logger.warning(f"Rate limit exceeded for {ip}")
logger.error(f"DB error creating post: {error}")
```

---

## TypeScript Frontend Rules

### Naming
- Files: `kebab-case.tsx` for pages, `PascalCase.tsx` for components
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Types/Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

### Component Rules
- Use named exports: `export function MyComponent()`
- Props interface always defined: `interface MyComponentProps { ... }`
- Event handlers: `handleClick`, `handleSubmit`, etc.
- Use `'use client'` directive only when needed (interactivity, hooks, browser APIs)
- Server components by default

### State Management
- Local state: `useState`, `useReducer`
- No global state library (keep it simple)
- Admin JWT token: React state only (not localStorage)
- Language preference: localStorage `moku_language`
- Visitor ID: localStorage `moku_visitor_id`

### API Calls
- Always use the typed `api` client from `src/lib/api.ts`
- Handle errors with try/catch and show toast notifications
- Loading states with skeleton loaders (not spinners)

### Tailwind CSS
- Use Tailwind v4 utility classes
- Design tokens via CSS variables in `globals.css`
- shadcn/ui components for all standard UI elements
- `cn()` utility for conditional classes

---

## camelCase <-> snake_case Convention

- Database columns: `snake_case` (e.g., `comment_count`, `created_at`, `preferred_date`)
- Backend Pydantic schemas: `snake_case` internally, `camelCase` via aliases for API
- API JSON responses: `camelCase` (e.g., `commentCount`, `createdAt`, `preferredDate`)
- Frontend TypeScript types: `camelCase` (e.g., `commentCount`, `createdAt`, `preferredDate`)

Backend handles the conversion via Pydantic Field aliases and `model_config`.

---

## Security Rules

1. `SUPABASE_SERVICE_ROLE_KEY` NEVER reaches the frontend.
2. Admin JWT stored in React state only (not localStorage, not cookies).
3. All user input sanitized server-side before DB write.
4. Passwords hashed with bcrypt (never stored in plaintext for new data).
5. Rate limiting on all write endpoints.
6. Spam detection on post/comment content.
7. CORS restricted to frontend domain in production.
