# Skill: Backend API Endpoints (Complete Specification)

All endpoints served by FastAPI. Admin endpoints require `X-Admin-Token` header with valid JWT.

---

## Posts — `app/routers/posts.py` (prefix: `/api/posts`)

### GET /api/posts
List posts with search, filter, pagination, sort.
```
Query params:
  page: int = 1 (ge=1)
  limit: int = 10 (ge=1, le=100)
  search: str = "" (max 200 chars)
  searchType: "title" | "author" | "content" = "title"
  category: "question" | "info" | "chat" | null
  sort: "newest" | "oldest" | "likes" | "views" | "comments" = "newest"

Response: PostListResponse
```
**Behaviors:**
- Pinned posts (`pinned=true`) ALWAYS appear first (`ORDER BY pinned DESC`)
- `newest`: ORDER BY numeric_id DESC
- `oldest`: ORDER BY created_at ASC
- `views`: ORDER BY views DESC, created_at DESC
- `comments`: ORDER BY comment_count DESC, created_at DESC
- `likes`: COUNT from post_likes table per post, ORDER BY count DESC (requires cross-table query)
- search uses `ILIKE '%keyword%'` on the target column

### POST /api/posts
Create post. Rate limit: 5/minute/IP.
```
Body: PostCreate { author, title, content, password, experience?, category? }
Response: { success, message, post: PostResponse }
Status: 201
```
**Behaviors:** Sanitize author/title/content. Spam check on title+content. Hash password with bcrypt. Generate ID as `post_{unix_ms}`.

### PUT /api/posts/{post_id}
Edit post. Password required.
```
Body: PostUpdate { title?, content?, password }
Response: { success, message, post: PostResponse }
```
**Behaviors:** Verify password first. If `needs_rehash`, upgrade to bcrypt.

### DELETE /api/posts/{post_id}
Delete post. Password OR admin required.
```
Body: PostDeleteRequest { password?, is_admin? }
Response: SuccessResponse
```

### POST /api/posts/{post_id}/view
Increment view count.
```
Response: ViewIncrementResponse { success, views }
```

### POST /api/posts/{post_id}/like
Toggle like.
```
Body: LikeToggleRequest { visitorId (min 8 chars) }
Response: LikeResponse { success, liked, likes }
```
**Behaviors:** Check if row exists in post_likes for (post_id, visitor_id). If exists: DELETE (unlike). If not: INSERT (like). Return updated COUNT.

### GET /api/posts/{post_id}/likes
Get like status.
```
Query: visitorId (optional)
Response: LikeStatusResponse { success, likes, liked }
```

### POST /api/posts/likes/bulk
Bulk get like counts.
```
Body: BulkLikesRequest { postIds: string[] (max 100) }
Response: BulkLikesResponse { success, likes: {postId: count} }
```

### POST /api/posts/{post_id}/verify-password
Verify post password.
```
Body: PasswordVerifyRequest { password }
Response: PasswordVerifyResponse { success, verified }
```

### POST /api/posts/{post_id}/pin [ADMIN]
Toggle pin status.
```
Response: PinToggleResponse { success, message, post }
```

### GET /api/posts/{post_id}/comments
List comments for a post.
```
Response: CommentListResponse { success, comments[], count }
```
ORDER BY created_at ASC.

### POST /api/posts/{post_id}/comments
Create comment. Rate limit: 5/minute/IP.
```
Body: CommentCreate { author, content, password }
Response: { success, message, comment: CommentResponse, commentCount: int }
Status: 201
```
**Behaviors:** Spam check. Hash password. Increment post.comment_count.

---

## Comments — `app/routers/comments.py` (prefix: `/api/comments`)

### PUT /api/comments/{comment_id}
Edit comment. Password required.
```
Body: CommentUpdate { content, password }
Response: { success, message, comment: CommentResponse }
```

### DELETE /api/comments/{comment_id}
Delete comment. Password OR admin required.
```
Body: CommentDeleteRequest { password?, is_admin? }
Response: SuccessResponse
```
**Behaviors:** Decrement parent post.comment_count (floor at 0).

### POST /api/comments/{comment_id}/verify-password
```
Body: PasswordVerifyRequest { password }
Response: PasswordVerifyResponse { success, verified }
```

---

## Inquiries — `app/routers/inquiries.py` (prefix: `/api/inquiries`)

### POST /api/inquiries
Submit inquiry form. Rate limit: 5/minute/IP.
```
Body: InquiryCreate { name, email(EmailStr), phone(Japanese format), age(18-30), preferredDate, plan, message(max 2000) }
Response: SuccessResponse
Status: 201
```

### GET /api/inquiries [ADMIN]
List all inquiries, ordered by created_at DESC.
```
Response: InquiryListResponse { success, inquiries[], count }
```

### PUT /api/inquiries/{inquiry_id}/status [ADMIN]
```
Body: InquiryStatusUpdate { status: "pending"|"contacted"|"completed", admin_note? }
Response: { success, message, inquiry: InquiryResponse }
```

### DELETE /api/inquiries/{inquiry_id} [ADMIN]
```
Response: SuccessResponse
```

---

## Articles — `app/routers/articles.py` (prefix: `/api/articles`)

### GET /api/articles
List all articles. ORDER BY date DESC.
```
Response: ArticleListResponse { success, articles[], count }
```
**Behaviors:** Resolve `storage:` prefixed image_url to signed URLs (batch).

### GET /api/articles/{article_id}
```
Response: { success, article: ArticleResponse }
```
**Behaviors:** Resolve `storage:` image_url to signed URL.

### POST /api/articles [ADMIN]
```
Body: ArticleCreate { id(slug), ja(required), ko(optional), imageUrl?, date? }
Response: { success, message, article }
Status: 201
```
**Behaviors:** Check for duplicate ID. Sanitize all text fields.

### PUT /api/articles/{article_id} [ADMIN]
```
Body: ArticleUpdate { ja?, ko?, imageUrl?, date? }
Response: { success, message, article }
```
**Behaviors:** Merge with existing fields (partial update).

### DELETE /api/articles/{article_id} [ADMIN]
```
Response: SuccessResponse
```
**Behaviors:** If image_url starts with `storage:`, also delete from Supabase Storage.

---

## Admin — `app/routers/admin.py` (prefix: `/api/admin`)

### POST /api/admin/login
Rate limit: 5/5min/IP.
```
Body: AdminLoginRequest { password }
Response: AdminLoginResponse { success, authenticated, token(JWT 24h) }
```
**Behaviors:** Compare with MOKU_ADMIN_PASSWORD env var. Return HS256 JWT.

### GET /api/admin/stats [ADMIN]
```
Response: AdminStatsResponse { success, stats: AdminStats }
```
**AdminStats:** total_inquiries, pending/contacted/completed counts, total_posts, total_views, total_comments.

### POST /api/admin/upload-image [ADMIN]
```
Body: multipart/form-data { file, articleId? }
Max: 5MB. Types: JPEG, PNG, WebP, GIF, AVIF.
Response: { success, storagePath, storageValue("storage:..."), signedUrl, size, type }
Status: 201
```

### POST /api/admin/delete-image [ADMIN]
```
Body: { storagePath: str }
Response: SuccessResponse
```

---

## Config — `app/routers/config.py` (prefix: `/api`)

### GET /api/config
Public endpoint. Cache: 1 hour.
```
Response: SiteConfigResponse { gaMeasurementId, verification: { google, naver } }
```
